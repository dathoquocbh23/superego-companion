"""POST /api/session — tạo phiên ẩn danh. docx/06 §2.1."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Header
from pydantic import BaseModel

from app.memory.auth import resolve_user_id
from app.persistence.transcript import get_transcript_store

from app.config import settings
from app.overlay.model import Overlay
from app.overlay.store import get_store

router = APIRouter(prefix="/api", tags=["session"])


class SessionResponse(BaseModel):
    session_id: str
    expires_in: int
    signed_in: bool = False


@router.post("/session", response_model=SessionResponse)
async def create_session(
    authorization: str | None = Header(default=None),
) -> SessionResponse:
    """Mở phiên. Có token Supabase hợp lệ thì phiên gắn với tài khoản, nếu
    không thì vẫn mở phiên ẩn danh như cũ — đăng nhập là TUỲ CHỌN."""
    session_id = str(uuid.uuid4())
    user_id = await resolve_user_id(authorization)
    overlay = Overlay(session_id=session_id, user_id=user_id)
    # Tạo hàng conversations NGAY ĐÂY, không đợi tin nhắn đầu: user_id chỉ được
    # phân giải ở lượt mở phiên (docx/12 §6), tạo muộn thì phải mang nó theo
    # thêm một chặng nữa mà chẳng được gì.
    overlay.conversation_id = await get_transcript_store().ensure_conversation(
        session_id, user_id
    )
    await get_store().save(overlay)
    return SessionResponse(
        session_id=session_id,
        expires_in=settings.overlay_ttl_seconds,
        signed_in=user_id is not None,
    )
