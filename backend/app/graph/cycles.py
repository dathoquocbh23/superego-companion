"""Dò vòng lặp đang hoạt hoá. docx/03 §6."""
from __future__ import annotations

from app.config import settings

from .loader import GraphService

# D12 — số chữ tối thiểu của một dòng INSIGHT_CARD. Dưới mức này thì nó là một
# mẩu cue, không phải một câu người ta nói.
MIN_TU_MOI_DONG = 3


def active_cycles(graph: GraphService, evidence: dict[str, float]) -> list[str]:
    """cycle HOẠT HOÁ khi số node của cycle có evidence ≥ ngưỡng ≥ min_nodes_to_activate.

    `evidence` : node_id → confidence hiện tại.
    """
    thr = settings.cycle_activation_confidence
    out: list[str] = []
    for c in graph.cycles:
        lit = sum(1 for nid in c.nodes if evidence.get(nid, 0.0) >= thr)
        if lit >= c.min_nodes_to_activate:
            out.append(c.id)
    return out


def cycle_verbatim_lines(
    graph: GraphService,
    cycle_id: str,
    verbatims: dict[str, str],
    confidences: dict[str, float],
) -> list[str]:
    """Dựng các dòng cho INSIGHT_CARD theo THỨ TỰ cycle.

    docx/11 phần D4:
      - chỉ lấy node có verbatim và confidence ≥ ngưỡng hoạt hoá
      - khử trùng lặp theo verbatim
      - tối đa 5 dòng
    Trả list rỗng nếu không đủ dữ liệu — caller quyết định fallback.

    D12 (08/09/2026) — verbatim phải ĐỦ DÀI. Verbatim sinh từ cue matcher là
    đúng cụm cue đã khớp, nên một cue hai chữ cho ra một dòng thẻ hai chữ. Thẻ
    thật đã hiện ra:

        "Mình vừa bị điểm kém một bài kiểm tra" -> "bài kiểm tra" -> ...

    Dòng giữa là một mẩu cụt, không phải một câu học sinh nói. Cả điểm nhấn của
    thẻ nằm ở chỗ "đây đúng là lời bạn" — một mẩu cụt phá đúng chỗ đó.
    """
    cycle = next((c for c in graph.cycles if c.id == cycle_id), None)
    if cycle is None:
        return []
    thr = settings.cycle_activation_confidence
    seen: set[str] = set()
    lines: list[str] = []
    for nid in cycle.nodes:
        vb = (verbatims.get(nid) or "").strip()
        if not vb or confidences.get(nid, 0.0) < thr:
            continue
        if len(vb.split()) < MIN_TU_MOI_DONG:        # D12
            continue
        key = vb.lower()
        if key in seen:
            continue
        seen.add(key)
        lines.append(vb)
        if len(lines) >= 5:
            break
    return lines
