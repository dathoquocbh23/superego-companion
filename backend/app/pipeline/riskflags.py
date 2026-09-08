"""Suy ra RiskFlag từ nội dung + trạng thái overlay. docx/02 §3.3."""
from __future__ import annotations

import re

from app.config import settings
from app.graph.loader import GraphService
from app.overlay.model import Evidence, EvidenceSource, Overlay
from app.safety.normalize import normalize_vi

# "≥ 2 tuần" — các cách học sinh hay diễn đạt mốc thời gian kéo dài
_KEO_DAI = re.compile(
    r"\b("
    r"may tuan|vai tuan|nhieu tuan|"
    r"[2-9] tuan|1[0-9] tuan|hai tuan|ba tuan|bon tuan|"
    r"may thang|vai thang|ca thang|[1-9] thang|mot thang|hai thang|"
    r"lau roi|tu lau|bao lau nay|suot thoi gian qua|do gio"
    r")\b"
)


def infer_riskflags(graph: GraphService, overlay: Overlay, user_message: str, turn_id: int) -> list[str]:
    """Gắn evidence cho r-keo-dai / r-suy-giam-chuc-nang khi thoả điều kiện.

    Trả danh sách flag đã set trong lượt này.
    """
    set_now: list[str] = []
    norm = normalize_vi(user_message)

    if _KEO_DAI.search(norm) and not overlay.has("r-keo-dai"):
        overlay.evidence["r-keo-dai"] = Evidence(
            node_id="r-keo-dai",
            confidence=0.9,
            source=EvidenceSource.SELF_REPORT,
            turn_ids=[turn_id],
            verbatim="",
        )
        set_now.append("r-keo-dai")

    thr = settings.confidence_threshold
    impacts = [
        nid for nid, e in overlay.evidence.items()
        if (n := graph.node(nid)) and n.type == "impact" and e.confidence >= thr
    ]
    if len(impacts) >= 2 and not overlay.has("r-suy-giam-chuc-nang"):
        overlay.evidence["r-suy-giam-chuc-nang"] = Evidence(
            node_id="r-suy-giam-chuc-nang",
            confidence=0.9,
            source=EvidenceSource.SELF_REPORT,
            turn_ids=[turn_id],
            verbatim="",
        )
        set_now.append("r-suy-giam-chuc-nang")

    return set_now
