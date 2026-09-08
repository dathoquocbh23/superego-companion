"""POST /api/chat/stream — SSE. docx/06 §2.4."""
from __future__ import annotations

import json
import logging

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.overlay.store import get_store
from app.pipeline.runner import run_chat_turn

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["chat"])


class ChatRequest(BaseModel):
    session_id: str
    message: str


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post("/chat/stream")
async def chat_stream(req: ChatRequest) -> StreamingResponse:
    async def gen():
        try:
            async for event, data in run_chat_turn(req.session_id, req.message):
                yield _sse(event, data)
        except Exception:  # pragma: no cover — không bao giờ 500 trần cho người dùng
            logger.exception("chat_stream lỗi")
            yield _sse("meta", {"gate": "ERROR", "message_type": "REFLECT"})
            yield _sse("token", {"t": "Mình đang hơi chậm, bạn nhắn lại giúp mình nhé."})
            yield _sse("footer", {"quickReplies": [], "turn_id": -1})
            yield _sse("done", {})

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "Connection": "keep-alive"},
    )


@router.get("/chat/history/{session_id}")
async def chat_history(session_id: str) -> dict:
    """Chỉ để debug — trả lịch sử tạm trong overlay (không phải log)."""
    overlay = await get_store().get(session_id)
    return {"turn_count": overlay.turn_count, "history": overlay.history}
