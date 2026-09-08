"""
Ghi hội thoại nguyên văn vào Supabase (bảng conversations + messages). GĐ6.

ĐỔI LUẬT 07/09/2026 — trước đây dự án CỐ Ý không lưu transcript:
    app/telemetry/log.py: "KHÔNG BAO GIỜ ghi user_message, verbatim,
    response_text, session_id gốc, PII"
    docx/03 §8: không lưu overlay ra file/DB ở giai đoạn demo
Chủ đề tài quyết định lưu, để có dữ liệu cho phần nghiên cứu phía sau. Bảng đã
dựng sẵn từ 001_init.sql, chỉ chưa ai đấu dây.

RANH GIỚI PHẢI GIỮ — hai kho, KHÔNG trộn:

  turn_logs  : số liệu nghiên cứu, KHÔNG có user_id, KHÔNG có nguyên văn.
               Không truy ngược được về cá nhân, nên phân tích được trên TOÀN
               BỘ traffic mà không cần gì thêm. (app/telemetry/log.py giữ nguyên.)

  messages   : nguyên văn, CÓ chủ (user_id). Xoá theo yêu cầu được, áp RLS được.

Gộp hai thứ vào một bảng là mất cả hai lợi thế cùng lúc.

Ghi ở đây chạy SAU khi lượt chat đã trả xong cho người dùng — chậm hay hỏng đều
không ai thấy. Nuốt lỗi giống memory/store.py: mất transcript còn hơn mất phiên
tư vấn.

⚠️ Bảng này KHÔNG có file dự phòng nào (khác turn_logs, vốn còn data/turns.jsonl
cho tới khi deploy lên host đĩa tạm thời như Render free tier). Một lỗi mạng
thoáng qua là mất vĩnh viễn nếu không retry — xem app/persistence/http_retry.py.
"""
from __future__ import annotations

import logging

import httpx

from app.config import settings
from app.persistence.http_retry import voi_retry

logger = logging.getLogger(__name__)

_TIMEOUT = httpx.Timeout(4.0, connect=2.0)

# Khớp CHECK constraint của bảng messages (001_init.sql mục B). Giá trị ngoài
# danh sách này làm PostgREST trả 400 và mất cả lượt ghi — chặn ở Python để một
# gate mới thêm sau này không âm thầm làm hỏng đường lưu.
_MESSAGE_TYPES = {
    "USER", "REFLECT", "INSIGHT_CARD", "KNOWLEDGE_CARD",
    "COPING_CARD", "BRIDGE_CARD", "CRISIS_CARD",
}

_TITLE_MAX = 42


def title_from(text: str) -> str:
    """Tiêu đề = câu đầu người dùng gõ, cắt 42 ký tự.

    Cùng luật với `titleFrom()` ở frontend/src/lib/conversations.ts để sidebar
    (localStorage) và Supabase không hiện hai tiêu đề khác nhau cho cùng phiên.
    """
    t = " ".join((text or "").split())
    if not t:
        return "Cuộc trò chuyện mới"
    return f"{t[:_TITLE_MAX]}…" if len(t) > _TITLE_MAX else t


class TranscriptStore:
    """Một instance cho cả tiến trình. An toàn khi tính năng đang tắt."""

    def __init__(self, url: str, service_key: str):
        self._base = url.rstrip("/")
        self._headers = {
            "apikey": service_key,
            "Authorization": f"Bearer {service_key}",
            "Content-Type": "application/json",
        }
        self._degraded = False

    def _disable(self, reason: str) -> None:
        if not self._degraded:
            logger.warning("Lưu hội thoại không khả dụng (%s) — chạy không lưu", reason)
        self._degraded = True

    @staticmethod
    def _chi_tiet(exc: Exception) -> str:
        """Thân phản hồi của lỗi HTTP.

        PostgREST nói RẤT rõ sai ở đâu (cột nào, ràng buộc nào) trong body của
        400/409. `str(exc)` của httpx chỉ có mã và URL — vứt đi phần duy nhất
        dùng được để sửa.
        """
        resp = getattr(exc, "response", None)
        if resp is None:
            return str(exc)
        return f"{resp.status_code} {resp.text[:400]}"

    @property
    def available(self) -> bool:
        return settings.transcript_ready and not self._degraded

    # ------------------------------------------------------------------
    async def ensure_conversation(self, session_id: str, user_id: str | None) -> str | None:
        """Lấy (hoặc tạo) hàng conversations cho phiên này. Trả id, None nếu hỏng.

        Upsert theo `session_id` (cột UNIQUE) thay vì insert thuần: overlay sống
        trong Redis với TTL 24h, hết hạn rồi người dùng quay lại cùng session_id
        thì phải nối vào ĐÚNG hội thoại cũ, không đẻ ra hàng thứ hai.
        """
        if not self.available:
            return None
        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT) as c:
                r = await voi_retry(lambda: c.post(
                    f"{self._base}/rest/v1/conversations",
                    headers={
                        **self._headers,
                        "Prefer": "resolution=merge-duplicates,return=representation",
                    },
                    params={"on_conflict": "session_id"},
                    json={"session_id": session_id, "user_id": user_id},
                ))
                rows = r.json()
                return rows[0]["id"] if rows else None
        except Exception as exc:
            self._disable(f"conversations {self._chi_tiet(exc)}")
            return None

    async def set_title(self, conversation_id: str, title: str) -> None:
        """Đặt tiêu đề từ câu đầu tiên. Chỉ gọi ở lượt 1.

        PATCH này còn kích trigger conversations_touch → updated_at nhảy lên,
        nên sidebar sắp xếp theo thời gian vẫn đúng mà không cần đụng vào
        conversations ở mọi lượt sau.
        """
        if not self.available:
            return
        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT) as c:
                await voi_retry(lambda: c.patch(
                    f"{self._base}/rest/v1/conversations",
                    headers={**self._headers, "Prefer": "return=minimal"},
                    params={"id": f"eq.{conversation_id}"},
                    json={"title": title},
                ))
        except Exception as exc:
            self._disable(f"set_title {self._chi_tiet(exc)}")

    async def record_messages(self, conversation_id: str, rows: list[dict]) -> None:
        """Ghi các message của MỘT lượt trong một lời gọi.

        Hai hàng (user + assistant) đi cùng nhau: tách ra hai request thì có lúc
        câu hỏi đã lưu mà câu trả lời chưa, và bản ghi nghiên cứu bị lệch.
        """
        if not self.available or not rows:
            return
        sach = [r for r in rows if r.get("message_type") in _MESSAGE_TYPES]
        if len(sach) != len(rows):
            logger.warning("Bỏ %d message có message_type lạ", len(rows) - len(sach))
        if not sach:
            return
        # PostgREST đòi MỌI object trong một lần insert hàng loạt phải có CÙNG
        # tập khoá, nếu không trả PGRST102 "All object keys must match" và mất
        # cả lượt. Hàng `user` không có card/quick_replies còn hàng `assistant`
        # có — nên phải san phẳng về cùng một khung, thiếu thì điền None.
        khung = {"conversation_id", "turn_id", "role", "message_type",
                 "content", "card", "quick_replies"}
        body = [
            {k: {**row, "conversation_id": conversation_id}.get(k) for k in sorted(khung)}
            for row in sach
        ]
        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT) as c:
                await voi_retry(lambda: c.post(
                    f"{self._base}/rest/v1/messages",
                    headers={**self._headers, "Prefer": "return=minimal"},
                    json=body,
                ))
        except Exception as exc:
            self._disable(f"messages {self._chi_tiet(exc)}")


_store: TranscriptStore | None = None


def get_transcript_store() -> TranscriptStore:
    global _store
    if _store is None:
        _store = TranscriptStore(settings.supabase_url, settings.supabase_service_role_key)
    return _store
