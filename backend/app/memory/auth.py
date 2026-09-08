"""Xác thực token Supabase → user_id. docx/12 §6.

Cố tình KHÔNG tự verify chữ ký JWT: project Supabase mới ký bằng khoá bất đối
xứng và xoay khoá định kỳ, nên tự verify là phải nuôi thêm cache JWKS + xử lý
xoay khoá — nhiều chỗ sai hơn là lợi. Hỏi thẳng Supabase một lần lúc MỞ PHIÊN
(không phải mỗi lượt chat) thì rẻ và luôn đúng.
"""
from __future__ import annotations

import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

_TIMEOUT = httpx.Timeout(4.0, connect=2.0)


async def resolve_user_id(access_token: str | None) -> str | None:
    """Trả user_id nếu token hợp lệ, ngược lại None (→ phiên ẩn danh).

    Token hỏng KHÔNG phải lỗi: app vẫn phải chạy được khi chưa đăng nhập.
    """
    if not access_token or not settings.supabase_url:
        return None
    token = access_token.removeprefix("Bearer ").strip()
    if not token:
        return None

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as c:
            r = await c.get(
                f"{settings.supabase_url.rstrip('/')}/auth/v1/user",
                headers={
                    "Authorization": f"Bearer {token}",
                    # anon key không có ở backend; service key hợp lệ cho apikey
                    "apikey": settings.supabase_service_role_key,
                },
            )
        if r.status_code != 200:
            return None
        return r.json().get("id")
    except Exception:
        logger.warning("Không xác thực được token Supabase — coi như ẩn danh")
        return None
