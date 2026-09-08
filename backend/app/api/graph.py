"""GET /api/graph/labels — nhãn tiếng Việt của evidence node. docx/12 §8.

Vì sao cần endpoint này: màn hình "bot nhớ gì về mình" đọc `user_memory` THẲNG
từ Supabase bằng anon key + RLS (an toàn hơn đi vòng qua service_role ở
backend). Nhưng bảng đó chỉ có `node_id`; nhãn người đọc được nằm trong
`domain_graph.yaml` phía backend. Endpoint này bắc cầu đúng phần đó.

KHÔNG cần đăng nhập: đây là ontology chung, không phải dữ liệu của ai.
Vẫn KHÔNG trả `cues` — cues là gợi ý cho bước trích, lộ ra là mớm.
"""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.graph.loader import get_graph

router = APIRouter(prefix="/api/graph", tags=["graph"])

# Nhóm để màn hình bộ nhớ xếp mục, bằng lời thường — KHÔNG dùng từ chuyên môn
# ("manifestation", "affect"…) vì màn này là người dùng đọc.
NHOM = {
    "manifestation": "Cách bạn hay nhìn về mình",
    "trigger": "Lúc chuyện thường xảy ra",
    "affect": "Cảm xúc đi kèm",
    "impact": "Ảnh hưởng tới sinh hoạt",
}


class NodeLabel(BaseModel):
    label: str
    nhom: str


@router.get("/labels", response_model=dict[str, NodeLabel])
async def labels() -> dict[str, NodeLabel]:
    g = get_graph()
    out: dict[str, NodeLabel] = {}
    for nid in g.evidence_node_ids:
        n = g.node(nid)
        if n is None:
            continue
        out[nid] = NodeLabel(label=n.label, nhom=NHOM.get(n.type, "Khác"))
    return out
