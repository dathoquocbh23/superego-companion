"""
Sinh 2 chip gợi ý theo ngữ cảnh cho lượt CLARIFY (LLM), có lọc an toàn cứng.
docx/03 §7 — 7 luật, tránh gợi ý mang tính mớm (iatrogenic suggestion).

Chip CLARIFY là "câu trả lời học sinh có thể bấm" → KHÔNG mang tiền tố hệ thống,
để đi qua bước trích như một lượt bình thường. Chip thoát vẫn mang tiền tố "— ".
"""
from __future__ import annotations

import json
import logging
import re

from app.graph.loader import GraphService
from app.llm.client import LLMClient
from app.overlay.model import Overlay
from app.safety.crisis import check_crisis
from app.safety.normalize import normalize_vi
from app.skills.loader import SkillLoader

logger = logging.getLogger(__name__)

_FENCE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)
_OBJ = re.compile(r"\{.*\}", re.DOTALL)

# Cụm bị chặn trong chip (đã bỏ dấu) — chẩn đoán / tự hại / tuyệt vọng
_BANNED = [
    "tram cam", "lo au", "roi loan", "benh", "chan doan",
    "vo dung", "vo vong", "tuyet vong", "vo gia tri", "khong dang song",
    "muon chet", "tu tu", "tu hai", "bo cuoc", "buong xuoi",
    "sieu toi", "cau toan",
]


def _parse(text: str) -> list[str]:
    for cand in (text, *_FENCE.findall(text)):
        cand = cand.strip()
        if not cand:
            continue
        try:
            data = json.loads(cand)
        except json.JSONDecodeError:
            m = _OBJ.search(cand)
            if not m:
                continue
            try:
                data = json.loads(m.group(0))
            except json.JSONDecodeError:
                continue
        if isinstance(data, dict) and isinstance(data.get("chips"), list):
            return [str(c).strip() for c in data["chips"] if str(c).strip()]
    return []


def _risk_cues(graph: GraphService) -> list[str]:
    out: list[str] = []
    for nid in graph.evidence_node_ids:
        n = graph.node(nid)
        if n and n.risk_adjacent:
            out.extend(normalize_vi(c) for c in n.cues)
    return out


def _is_safe(chip: str, risk_cues: list[str]) -> bool:
    if not chip or len(chip) > 44:
        return False
    if len(chip.split()) > 9:
        return False
    if check_crisis(chip).tier is not None:
        return False
    norm = normalize_vi(chip)
    if any(b in norm for b in _BANNED):
        return False
    if any(rc and rc in norm for rc in risk_cues):
        return False
    return True


async def generate_clarify_chips(
    *,
    llm: LLMClient,
    skills: SkillLoader,
    graph: GraphService,
    overlay: Overlay,
    bot_question: str,
    user_message: str,
) -> list[str]:
    """Trả tối đa 2 chip đã lọc an toàn. Rỗng → caller dùng fallback tất định."""
    if getattr(llm, "offline", False) or not bot_question.strip():
        return []

    known = " · ".join(f'"{v}"' for v in overlay.speakable_verbatims().values()) or "(chưa có)"
    system = skills.build(
        "13_QUICKREPLY",
        BOT_QUESTION=bot_question.strip(),
        USER_MESSAGE=user_message.strip(),
        KNOWN_VERBATIMS=known,
        TURN_COUNT=overlay.turn_count,
        HAS_TAKEN_ASSESSMENT="có" if overlay.has_taken_assessment else "chưa",
    )
    try:
        raw = await llm.complete(
            system=system, user=bot_question.strip(),
            max_tokens=200, temperature=0.5, json_mode=True,
        )
    except Exception:
        logger.warning("quickreply: LLM lỗi — dùng fallback")
        return []

    risk_cues = _risk_cues(graph)
    out: list[str] = []
    for chip in _parse(raw):
        if _is_safe(chip, risk_cues) and chip.lower() not in {c.lower() for c in out}:
            out.append(chip)
        if len(out) == 2:
            break
    return out
