"""Nối bộ nhớ dài hạn vào Overlay. docx/12 §5.

HAI LUẬT KHÔNG ĐƯỢC PHÁ:

1. Bộ nhớ chỉ để bot BIẾT NÊN HỎI GÌ, không bao giờ để KHẲNG ĐỊNH VỀ CON NGƯỜI.
   (Từ 07/09/2026 bot NHỚ được sự việc — "bạn kể thi được 6.5" — nhưng vẫn
   KHÔNG được nhắc lại lời tự phán xét. Xem `memory_quotes()` bên dưới.)
   Evidence nạp vào mang source=REMEMBERED: `can_be_spoken` là False và trần
   confidence (0.50) nằm dưới `confidence_threshold` (0.70), nên node nhớ lại
   không bao giờ tự đủ mạnh để kích REFLECT hay dựng INSIGHT_CARD. Nó chỉ vào
   `frontier` của `highest_information_gain_node()` — tức là bot hỏi trúng chỗ
   hơn, chứ không nói "lần trước bạn bảo bạn kém cỏi".

2. Bằng chứng HÔM NAY luôn thắng bằng chứng CŨ.
   REMEMBERED xếp hạng -1 trong `_SOURCE_RANK`, dưới cả INFERRED. Học sinh nói
   khác đi so với tháng trước thì lời hôm nay đè lên, không phải cãi nhau với
   bộ nhớ.
"""
from __future__ import annotations

import logging

from app.config import settings
from app.graph.loader import GraphService
from app.memory.decay import decayed_confidence
from app.memory.store import get_memory_store
from app.overlay.model import Evidence, EvidenceSource, Overlay

logger = logging.getLogger(__name__)

# Node dưới ngưỡng này sau khi phân rã thì thôi nạp — nhiễu nhiều hơn tín hiệu.
_MIN_SEED_CONFIDENCE = 0.15


async def seed_overlay(overlay: Overlay, user_id: str | None, graph: GraphService) -> int:
    """Nạp bộ nhớ dài hạn vào overlay của phiên MỚI. Trả số node đã nạp."""
    if not user_id or not settings.memory_ready or overlay.memory_seeded:
        return 0

    store = get_memory_store()
    overlay.memory_seeded = True          # thử một lần thôi, kể cả khi tắt/lỗi
    if not await store.memory_enabled_for(user_id):
        return 0

    seeded = 0
    for node in await store.load(user_id, settings.memory_max_seed_nodes):
        # Node đã bị gỡ khỏi graph (đổi ontology giữa chừng) → bỏ, không dựng
        # evidence trỏ vào hư không.
        n = graph.node(node.node_id)
        if n is None or not n.is_evidence:
            continue
        # risk_adjacent KHÔNG BAO GIỜ nạp từ bộ nhớ: mở phiên mà đã nghiêng sẵn
        # về "vô vọng" là mớm đúng thứ nguy hiểm nhất.
        if n.risk_adjacent:
            continue

        conf = decayed_confidence(
            node.confidence, node.last_seen, half_life_days=settings.memory_half_life_days
        )
        if conf < _MIN_SEED_CONFIDENCE:
            continue

        overlay.merge(
            Evidence(
                node_id=node.node_id,
                confidence=conf,
                source=EvidenceSource.REMEMBERED,
                turn_ids=[],
                # Nguyên văn CÓ được giữ từ 004_verbatim.sql. Nó nằm trong
                # Evidence để `memory_quotes()` lọc, KHÔNG để REFLECT dùng —
                # `can_be_spoken` của REMEMBERED vẫn là False.
                verbatim=node.verbatim,
            )
        )
        seeded += 1

    if seeded:
        logger.info("Nạp %d node từ bộ nhớ dài hạn", seeded)
    return seeded


async def record_turn(
    overlay: Overlay,
    user_id: str | None,
    session_hash: str,
    turn_id: int,
    extracted: list[Evidence],
) -> None:
    """Ghi bằng chứng của lượt này vào bộ nhớ dài hạn.

    Chỉ ghi thứ HỌC SINH THỰC SỰ NÓI trong lượt này. Không ghi lại REMEMBERED
    (nếu không bộ nhớ tự bơm chính nó lên mỗi phiên, càng ngày càng chắc chắn
    về một điều chưa từng được xác nhận lại).
    """
    if not user_id or not settings.memory_ready:
        return

    nodes = [
        {
            "node_id": e.node_id,
            "confidence": round(e.confidence, 2),
            "source": e.source.value,
            # SQL còn lọc lần nữa: chỉ nguồn người dùng tự nói mới được giữ
            # câu chữ (004_verbatim.sql hàng rào 1). Gửi thừa cũng không lọt.
            "verbatim": e.verbatim or "",
        }
        for e in extracted
        if e.source != EvidenceSource.REMEMBERED
    ]
    # CONFIRMED sinh ra từ chip "Đúng vậy" không đi qua `extracted` — lấy thêm
    # từ overlay để cái người ta vừa gật đầu không bị rơi mất.
    confirmed = [
        {"node_id": nid, "confidence": round(ev.confidence, 2),
         "source": ev.source.value, "verbatim": ev.verbatim or ""}
        for nid, ev in overlay.evidence.items()
        if ev.source == EvidenceSource.CONFIRMED and turn_id in ev.turn_ids
    ]
    seen = {n["node_id"] for n in nodes}
    nodes.extend(c for c in confirmed if c["node_id"] not in seen)

    if nodes:
        await get_memory_store().record(user_id, session_hash, turn_id, nodes)


def memory_quotes(overlay: Overlay, graph: GraphService) -> list[tuple[str, str]]:
    """Câu nguyên văn từ phiên TRƯỚC mà bot được phép nhắc lại.

    Đây là ranh giới quan trọng nhất của tính năng nhớ-câu-chữ. Lọc theo LOẠI
    node, không theo confidence:

      ✅ trigger / impact = SỰ VIỆC. "thi được 6.5", "khó ngủ", "ba mẹ mắng".
         Nhắc lại là hữu ích và vô hại — đó là chuyện đã xảy ra.

      ❌ manifestation / affect = LỜI TỰ PHÁN XÉT. "mình kém cỏi", "mình dở quá".
         Nhắc lại là đóng đinh người ta vào phiên bản cũ của chính họ, đúng thứ
         cả sản phẩm đang cố gỡ ra. Một đứa trẻ tháng trước thấy mình vô dụng
         không có nghĩa hôm nay vẫn vậy — và câu đầu tiên nó nghe không nên là
         lời nó từng nói lúc tệ nhất.

    Đổi phạm vi bằng `MEMORY_RECALL_NODE_TYPES`. Mở rộng sang manifestation /
    affect thì mở lại đúng rủi ro mớm đã nêu ở docx/12 §5.
    """
    cho_phep = set(settings.memory_recall_node_types)
    out: list[tuple[str, str]] = []
    for nid, ev in overlay.evidence.items():
        if ev.source != EvidenceSource.REMEMBERED or not ev.verbatim:
            continue
        n = graph.node(nid)
        if n is None or n.type not in cho_phep or n.risk_adjacent:
            continue
        out.append((n.label, ev.verbatim))
    return out
