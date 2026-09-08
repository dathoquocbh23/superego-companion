"""
Đẩy `turn_logs` lên Supabase. GĐ6b, 07/09/2026.

KHÁC HẲN app/persistence/transcript.py — đọc kỹ trước khi sửa:

    turn_logs  KHÔNG có user_id, KHÔNG có nguyên văn.
               session_hash = sha256(session_id)[:6], không đảo ngược được.
               Đây là số liệu nghiên cứu: gate, latency, flag, kích thước
               overlay. Không truy ngược về cá nhân, nên phân tích được trên
               TOÀN BỘ traffic mà không cần đụng tới chuyện đồng ý.

    messages   CÓ user_id, CÓ nguyên văn. Kho riêng, bảng riêng, module riêng.

Hai kho này cố ý không nói chuyện với nhau. Đừng "tiện tay" thêm user_id vào
đây — làm vậy là phá đúng thứ khiến turn_logs dùng được thoải mái.

Ghi file `data/turns.jsonl` VẪN GIỮ — hữu ích khi chạy local (đọc nhanh bằng
mắt, không cần mạng) và làm lưới tạm nếu Supabase chết GIỮA LÚC TIẾN TRÌNH
ĐANG SỐNG. Nhưng trên host đĩa tạm thời (Render free tier: container khởi
động lại là mất sạch `data/`), file KHÔNG còn là lưới an toàn thật — nó biến
mất cùng lúc với RAM. Vì vậy đường ghi Supabase ở đây PHẢI tự retry lỗi tạm
thời (app/persistence/http_retry.py) thay vì trông chờ backfill sau này.

Trùng lặp code với transcript.py (headers, thoái hoá, _chi_tiet) là CÓ Ý: gộp
hai kho vào một lớp cha là bước đầu tiên để rồi ai đó tiện tay dùng chung
đường ghi.
"""
from __future__ import annotations

import logging

import httpx

from app.config import settings
from app.persistence.http_retry import voi_retry

logger = logging.getLogger(__name__)

_TIMEOUT = httpx.Timeout(4.0, connect=2.0)

# Chốt chặn: cột nào không có trong bảng thì PostgREST trả 400 và mất cả bản
# ghi. Danh sách khớp 001_init.sql mục D — sửa build_record() mà quên sửa đây
# thì test tests/test_turnlog.py::test_moi_khoa_cua_build_record_deu_co_cot sẽ đỏ.
_COLUMNS = {
    "session_hash", "turn_id", "ts",
    "safety_tier", "safety_matched",
    "input_len", "input_is_chip", "chip_type",
    "extracted", "extract_failed", "extract_hallucinated",
    "overlay_size", "overlay_by_source", "active_cycles",
    "gate", "gate_reason", "target_nodes", "policy_edge_used",
    "message_type", "response_len", "response_sentences", "postcheck_flags",
    "chip_provenance", "latency_ms", "tokens", "flags",
}


class TurnLogStore:
    def __init__(self, url: str, service_key: str):
        self._base = url.rstrip("/")
        self._headers = {
            "apikey": service_key,
            "Authorization": f"Bearer {service_key}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        }
        self._degraded = False

    @property
    def available(self) -> bool:
        return settings.turnlog_ready and not self._degraded

    @staticmethod
    def _chi_tiet(exc: Exception) -> str:
        resp = getattr(exc, "response", None)
        if resp is None:
            return str(exc)
        return f"{resp.status_code} {resp.text[:400]}"

    def _disable(self, reason: str) -> None:
        if not self._degraded:
            logger.warning(
                "Đẩy turn_logs không khả dụng (%s) — vẫn ghi %s bình thường",
                reason, settings.log_path.name,
            )
        self._degraded = True

    async def push(self, records: list[dict]) -> bool:
        """Đẩy 1..n bản ghi. Trả True nếu đã ghi được. KHÔNG BAO GIỜ raise."""
        if not self.available or not records:
            return False
        # Chỉ giữ cột có thật, và san phẳng về cùng tập khoá — PostgREST đòi mọi
        # object trong insert hàng loạt phải khớp khoá (PGRST102), gặp thật ngày
        # 07/09/2026 ở bảng messages.
        body = [{k: r.get(k) for k in sorted(_COLUMNS)} for r in records]
        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT) as c:
                await voi_retry(lambda: c.post(
                    f"{self._base}/rest/v1/turn_logs", headers=self._headers, json=body
                ))
            return True
        except Exception as exc:
            self._disable(f"turn_logs {self._chi_tiet(exc)}")
            return False


_store: TurnLogStore | None = None


def get_turnlog_store() -> TurnLogStore:
    global _store
    if _store is None:
        _store = TurnLogStore(settings.supabase_url, settings.supabase_service_role_key)
    return _store
