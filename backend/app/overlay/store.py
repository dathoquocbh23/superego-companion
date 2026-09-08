"""
Overlay store trên Redis + TTL. docx/06 §7.

Redis down → chạy với overlay rỗng trong RAM (bot vẫn hoạt động ở mức CLARIFY).

ĐỔI LUẬT — trước đây "KHÔNG lưu overlay ra file/DB ở giai đoạn demo" (docx/03
§8). Giờ có backend Supabase thay thế (app/overlay/supabase_store.py), dùng
khi deploy lên host không có Redis cục bộ (Render free tier). Chọn backend
qua OVERLAY_BACKEND — factory ở get_store() bên dưới, class Redis trong file
này giữ nguyên không đổi cho cấu hình local/Redis hiện có.
"""
from __future__ import annotations

import logging

from app.config import settings

from .model import Overlay

logger = logging.getLogger(__name__)

_KEY = "overlay:{}"

try:  # redis là optional lúc chạy test
    import redis.asyncio as aioredis
except Exception:  # pragma: no cover
    aioredis = None  # type: ignore


class OverlayStore:
    def __init__(self, url: str, ttl: int):
        self._ttl = ttl
        self._mem: dict[str, str] = {}
        self._client = None
        self._degraded = False  # đã xác nhận Redis không khả dụng → thôi thử lại
        if aioredis is not None and url:
            try:
                self._client = aioredis.from_url(
                    url,
                    decode_responses=True,
                    socket_connect_timeout=0.5,
                    socket_timeout=0.5,
                    retry_on_timeout=False,
                )
            except Exception:  # pragma: no cover
                logger.warning("Không khởi tạo được Redis (%s) — dùng bộ nhớ RAM", url)
        else:
            logger.info("Redis tắt (REDIS_URL rỗng) — overlay sống trong RAM")

    def _disable(self, reason: str) -> None:
        if not self._degraded:
            logger.warning("Redis không khả dụng (%s) — chuyển sang RAM cho toàn phiên", reason)
        self._degraded = True
        self._client = None

    async def get(self, session_id: str) -> Overlay:
        key = _KEY.format(session_id)
        data: str | None = None
        if self._client is not None:
            try:
                data = await self._client.get(key)
            except Exception as exc:
                self._disable(f"GET {exc}")
        if data is None:
            data = self._mem.get(key)
        if data is None:
            return Overlay(session_id=session_id)
        try:
            return Overlay.model_validate_json(data)
        except Exception:
            logger.exception("Overlay hỏng — tạo mới")
            return Overlay(session_id=session_id)

    async def save(self, overlay: Overlay) -> None:
        key = _KEY.format(overlay.session_id)
        payload = overlay.model_dump_json()
        self._mem[key] = payload
        if self._client is not None:
            try:
                await self._client.set(key, payload, ex=self._ttl)
            except Exception as exc:
                self._disable(f"SET {exc}")

    async def close(self) -> None:
        if self._client is not None:
            try:
                await self._client.aclose()
            except Exception:
                pass


_store: OverlayStore | "SupabaseOverlayStore" | None = None  # noqa: F821


def get_store() -> OverlayStore | "SupabaseOverlayStore":  # noqa: F821
    """Chọn backend theo settings.overlay_backend. Mặc định "redis" — không
    đổi hành vi của cấu hình đang chạy nào. "supabase" import trễ (lazy) để
    module này không bắt buộc kéo theo httpx khi chỉ dùng Redis.
    """
    global _store
    if _store is not None:
        return _store

    backend = settings.overlay_backend
    if backend == "supabase":
        from .supabase_store import SupabaseOverlayStore

        _store = SupabaseOverlayStore(
            settings.supabase_url, settings.supabase_service_role_key,
            settings.overlay_ttl_seconds,
        )
    elif backend == "memory":
        _store = OverlayStore("", settings.overlay_ttl_seconds)  # url rỗng → luôn RAM
    else:
        _store = OverlayStore(settings.redis_url, settings.overlay_ttl_seconds)
    return _store
