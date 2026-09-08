"""
Overlay store trên Supabase — thay Redis khi không muốn thêm một dịch vụ
ngoài thứ ba. Bật bằng OVERLAY_BACKEND=supabase (mặc định vẫn "redis").

BỐI CẢNH: chuẩn bị deploy Render free tier, free tier không có Redis cục bộ.
Không trỏ REDIS_URL sang dịch vụ ngoài thì OverlayStore (store.py) tự rơi về
RAM trong tiến trình — ÂM THẦM, không lỗi hiển thị — và mỗi lần container
khởi động lại (deploy mới, hoặc rảnh rồi tự ngủ/thức) mọi phiên đang nói dở
QUÊN SẠCH. Đây là landmine NẶNG hơn nhiều so với mất turns.jsonl: nó phá
logic hội thoại đang sống (evidence, gate history, stall streak), không chỉ
số liệu.

ĐÁNH ĐỔI ĐÃ CHỌN — đọc trước khi sửa:

  get()/save() của overlay chạy TRONG đường phản hồi (khác turn_logs/messages,
  vốn chạy SAU khi đã trả lời xong người dùng). Đổi Redis (TCP, ~vài ms) sang
  PostgREST (HTTP, vài chục–vài trăm ms) là cộng thêm độ trễ THẤY ĐƯỢC vào mỗi
  lượt — nhỏ so với ~1.5-2s lời gọi LLM đã chiếm, nhưng không phải bằng 0.

  Giảm bằng CACHE ĐỌC trong RAM (`_mem`): trong một phiên, sau lần `get()` đầu
  tiên, các lượt sau phục vụ từ RAM — KHÔNG round-trip Supabase mỗi lượt. Chỉ
  `save()` luôn chạm mạng, vì đó là thứ giữ tính đúng đắn: overlay PHẢI ghi
  xong trước khi lượt tiếp theo có thể đọc lại (runner.py gọi `save()` TRƯỚC
  khi yield "footer"/"done", cố tình đồng bộ — đừng đổi thành fire-and-forget,
  làm vậy là mở race giữa lượt này ghi xong và lượt sau đọc vào).

  RAM cache mất khi container khởi động lại — đúng ý: `get()` khi đó sẽ miss
  cache, hỏi Supabase, và lấy lại đúng trạng thái đã lưu. Đây chính là điểm
  khác Redis-degrade-to-RAM: RAM ở đây chỉ là CACHE của một nguồn bền, không
  phải toàn bộ nguồn.

TTL Ở TẦNG CLIENT: bảng không tự xoá dòng theo thời gian như Redis `EX`. So
`updated_at` với OVERLAY_TTL_SECONDS lúc đọc; quá hạn thì coi như chưa từng
có (trả Overlay mới), row cũ nằm lại chờ dọn định kỳ (xem 006_overlay_state.sql
mục C).
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

import httpx

from app.config import settings
from app.persistence.http_retry import voi_retry

from .model import Overlay

logger = logging.getLogger(__name__)

_TIMEOUT = httpx.Timeout(4.0, connect=2.0)


def _parse_ts(raw: str) -> datetime:
    return datetime.fromisoformat(raw.replace("Z", "+00:00"))


class SupabaseOverlayStore:
    """Cùng interface với OverlayStore (store.py): get / save / close.

    runner.py không cần biết đang chạy backend nào — get_store() ở store.py
    chọn class theo settings.overlay_backend.
    """

    def __init__(self, url: str, service_key: str, ttl_seconds: int):
        self._base = url.rstrip("/")
        self._headers = {
            "apikey": service_key,
            "Authorization": f"Bearer {service_key}",
            "Content-Type": "application/json",
        }
        self._ttl = ttl_seconds
        self._mem: dict[str, Overlay] = {}
        self._degraded = False

    @property
    def available(self) -> bool:
        return bool(self._base) and not self._degraded

    def _disable(self, reason: str) -> None:
        if not self._degraded:
            logger.warning(
                "Overlay Supabase không khả dụng (%s) — dùng RAM cho toàn tiến trình", reason
            )
        self._degraded = True

    async def get(self, session_id: str) -> Overlay:
        # Cache RAM trước — trong vòng đời MỘT container, session đã chạm tới
        # rồi thì không cần round-trip HTTP mỗi lượt. Cache trống (session
        # mới, hoặc container vừa khởi động lại) mới hỏi Supabase.
        cached = self._mem.get(session_id)
        if cached is not None:
            return cached

        if self.available:
            try:
                async with httpx.AsyncClient(timeout=_TIMEOUT) as c:
                    r = await voi_retry(lambda: c.get(
                        f"{self._base}/rest/v1/overlay_state",
                        headers=self._headers,
                        params={"session_id": f"eq.{session_id}", "select": "data,updated_at"},
                    ))
                rows = r.json()
                if rows:
                    tuoi_giay = (
                        datetime.now(timezone.utc) - _parse_ts(rows[0]["updated_at"])
                    ).total_seconds()
                    if tuoi_giay <= self._ttl:
                        ov = Overlay.model_validate(rows[0]["data"])
                        self._mem[session_id] = ov
                        return ov
                    # Quá TTL — coi như chưa từng có, KHÔNG xoá dòng ở đây
                    # (dọn định kỳ, xem 006_overlay_state.sql mục C). Xoá
                    # ngay lúc đọc là network call thêm cho một việc không
                    # ai đang chờ.
            except Exception as exc:
                self._disable(f"GET {exc}")

        return Overlay(session_id=session_id)

    async def save(self, overlay: Overlay) -> None:
        # Cache TRƯỚC — kể cả khi Supabase chết, lượt SAU trong CÙNG tiến
        # trình vẫn đọc đúng trạng thái vừa lưu (giống hành vi RAM-fallback
        # của OverlayStore/Redis, không đổi UX khi hạ tầng có trục trặc).
        self._mem[overlay.session_id] = overlay
        if not self.available:
            return
        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT) as c:
                await voi_retry(lambda: c.post(
                    f"{self._base}/rest/v1/overlay_state",
                    headers={**self._headers, "Prefer": "resolution=merge-duplicates,return=minimal"},
                    params={"on_conflict": "session_id"},
                    json={
                        "session_id": overlay.session_id,
                        "data": overlay.model_dump(mode="json"),
                    },
                ))
        except Exception as exc:
            self._disable(f"SET {exc}")

    async def close(self) -> None:
        return None
