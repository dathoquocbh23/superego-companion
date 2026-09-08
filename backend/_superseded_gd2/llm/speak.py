"""
LLM lượt 2 — DIỄN ĐẠT theo gate. docx/06 §5, docx/05.

Chỉ dựng prompt + tham số. Việc stream/không-stream do pipeline quyết định.
LLM bị ràng buộc bởi gate đã quyết ở bước GateDecide — không tự do đi đâu thì đi.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass

from app.gate.decide import BRIDGE, CLARIFY, REFLECT, SUPPORT, GateDecision
from app.graph.loader import GraphService
from app.overlay.model import Overlay
from app.skills.loader import SkillLoader

_FENCE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)
_OBJ = re.compile(r"\{.*\}", re.DOTALL)


@dataclass
class SpeakPrompt:
    skill: str
    system: str
    user: str
    max_tokens: int
    temperature: float
    stream: bool                # False cho chế độ cycle (cần JSON hoàn chỉnh)


def _verbatim_list(overlay: Overlay, node_ids: list[str] | None = None) -> str:
    vbs = overlay.speakable_verbatims()
    if node_ids:
        picked = [vbs[n] for n in node_ids if n in vbs]
        if picked:
            return " · ".join(f'"{v}"' for v in picked)
    return " · ".join(f'"{v}"' for v in vbs.values()) or "(chưa có)"


def _memory_quotes_block(overlay: Overlay, graph: GraphService) -> str:
    """Khối "ĐIỀU MÌNH CÒN NHỚ" cho 00_CORE_PERSONA.

    Đã lọc theo loại node ở `memory_quotes()` — lời tự phán xét không lọt tới
    đây. "(không có)" là tín hiệu cho LLM biết nó KHÔNG nhớ gì, phải nói thật.
    """
    from app.memory.service import memory_quotes

    quotes = memory_quotes(overlay, graph)
    if not quotes:
        return "(không có)"
    dong = [f'- Về {label.lower()}: "{vb}"' for label, vb in quotes]
    return "\n".join(dong)


def build_prompt(
    *,
    skills: SkillLoader,
    graph: GraphService,
    overlay: Overlay,
    decision: GateDecision,
    user_message: str,
    recent_turns: str,
    cycle_ordered_verbatims: list[str] | None = None,
    refusal_situation: str | None = None,
) -> SpeakPrompt:
    turn_count = overlay.turn_count
    has_assessment = "có" if overlay.has_taken_assessment else "chưa"
    common = dict(
        TURN_COUNT=turn_count,
        HAS_TAKEN_ASSESSMENT=has_assessment,
        MEMORY_QUOTES=_memory_quotes_block(overlay, graph),
    )
    recent = recent_turns or "(chưa có)"

    if refusal_situation is not None:
        system = skills.build(
            "99_REFUSAL", SITUATION=refusal_situation, USER_MESSAGE=user_message, **common
        )
        return SpeakPrompt("99_REFUSAL", system, user_message, 300, 0.4, stream=True)

    if decision.gate == CLARIFY:
        label = ""
        if decision.target_nodes:
            n = graph.node(decision.target_nodes[0])
            label = n.label if n else ""
        system = skills.build(
            "11_CLARIFY",
            TARGET_NODE_LABEL=label or "điều người dùng vừa nói",
            KNOWN_VERBATIMS=_verbatim_list(overlay),
            RECENT_TURNS=recent,
            USER_MESSAGE=user_message,
            **common,
        )
        return SpeakPrompt("11_CLARIFY", system, user_message, 400, 0.7, stream=True)

    if decision.gate == REFLECT:
        mode = decision.mode or "single"
        if mode == "cycle" and cycle_ordered_verbatims:
            vbs = " · ".join(f'"{v}"' for v in cycle_ordered_verbatims)
            pattern = "một vòng lặp: kỳ vọng cao → không đạt → tự phê phán → lại cố hơn"
        else:
            vbs = _verbatim_list(overlay, decision.target_nodes)
            pattern = "cách người dùng nói về mình đang khá nặng nề"
        system = skills.build(
            "12_REFLECT",
            VERBATIMS=vbs,
            PATTERN_DESCRIPTION=pattern,
            MODE=mode,
            RECENT_TURNS=recent,
            **common,
        )
        return SpeakPrompt("12_REFLECT", system, user_message, 400, 0.7, stream=(mode != "cycle"))

    if decision.gate == BRIDGE:
        res_node = graph.node(decision.resource_node) if decision.resource_node else None
        rtype = "ba mẹ" if (res_node and res_node.resource_kind == "gia-dinh") else (
            res_node.label if res_node else "người thật"
        )
        system = skills.build(
            "15_BRIDGE",
            RESOURCE_TYPE=rtype,
            TRIGGER_REASON=decision.reason,
            VERBATIMS=_verbatim_list(overlay),
            RECENT_TURNS=recent,
            **common,
        )
        return SpeakPrompt("15_BRIDGE", system, user_message, 300, 0.3, stream=True)

    if decision.gate == SUPPORT:
        # LLM chỉ viết 1 câu dẫn; nội dung thẻ là văn bản duyệt sẵn.
        #
        # TRƯỚC 07/09/2026 chỗ này dùng lại khung 12_REFLECT. Hỏng: luật của
        # REFLECT bắt "dùng lại verbatim", "mở đầu bằng Mình để ý là", và
        # "KẾT THÚC bằng câu hỏi xác nhận — bắt buộc". Với cùng bộ verbatim,
        # LLM sinh ra gần như y hệt câu REFLECT của lượt ngay trước, rồi hỏi
        # xác nhận lần hai đúng cái người dùng vừa bấm "Đúng vậy".
        coping = graph.node(decision.coping_node) if decision.coping_node else None
        body = graph.content_body(decision.coping_node) if decision.coping_node else None
        system = skills.build(
            "14_SUPPORT",
            VERBATIMS=_verbatim_list(overlay),
            COPING_TITLE=(body or {}).get("title") or (coping.label if coping else "một gợi ý nhỏ"),
            RECENT_TURNS=recent,
            **common,
        )
        return SpeakPrompt("14_SUPPORT", system, user_message, 160, 0.6, stream=True)

    raise ValueError(f"gate không diễn đạt được: {decision.gate}")


def parse_cycle_json(text: str) -> dict | None:
    for candidate in (text, *_FENCE.findall(text)):
        candidate = candidate.strip()
        if not candidate:
            continue
        try:
            data = json.loads(candidate)
        except json.JSONDecodeError:
            m = _OBJ.search(candidate)
            if not m:
                continue
            try:
                data = json.loads(m.group(0))
            except json.JSONDecodeError:
                continue
        if isinstance(data, dict) and "lines" in data:
            return {"lines": list(data.get("lines") or []), "closing": data.get("closing", "")}
    return None
