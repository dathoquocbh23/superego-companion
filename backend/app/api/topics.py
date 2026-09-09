"""GET /api/topics — 4 chủ đề cửa vào cho màn chào. docx/13 §5.4.

Vì sao là endpoint chứ không hardcode ở frontend: câu chữ 4 thẻ nằm cùng chỗ
với `opening` và `learn_chips` trong `topics.yaml`. Tách ra hai nơi thì sớm muộn
tiêu đề trên thẻ nói một đằng, nội dung bấm vào ra một nẻo.

KHÔNG cần đăng nhập — đây là thực đơn chung, không phải dữ liệu của ai.

CHỈ trả chủ đề `enabled`. Chủ đề chưa trích xong nội dung (hiện là "Ảnh hưởng
đến sức khoẻ tinh thần") phải KHÔNG HIỆN, chứ không phải hiện rồi bấm vào mới
báo lỗi: thà giấu một ô còn hơn bày ra để bot bịa.

KHÔNG trả `learn_chips` / `opening`: đó là chuyện nội bộ của backend. Frontend
chỉ cần đủ để vẽ thẻ; chip sẽ theo phản hồi của lượt chat mà về.
"""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.graph.topics import get_topics

router = APIRouter(prefix="/api", tags=["topics"])


class TopicCard(BaseModel):
    id: str
    title: str
    subtitle: str
    # true = chủ đề mở bằng bài Likert 10 câu, frontend nhúng form thay vì gửi
    # một lượt chat. Xem docx/13 §5.7.
    opens_assessment: bool


@router.get("/topics", response_model=list[TopicCard])
async def list_topics() -> list[TopicCard]:
    return [
        TopicCard(
            id=t.id,
            title=t.title,
            subtitle=t.subtitle,
            opens_assessment=t.mo_bang_bai_test,
        )
        for t in get_topics().enabled()
    ]
