"""
LLM lượt 1 — TRÍCH bằng chứng → JSON. docx/06 §4, docx/11 phần D2.

Chốt chặn chống bịa:
  - node_id không có trong graph → loại, flag extract_hallucinated_node
  - verbatim không phải substring của user_message → loại
  - confidence vượt trần theo mapping → kẹp lại
  - parse JSON hỏng → trả rỗng, flag extract_parse_failed. KHÔNG crash.
"""
from __future__ import annotations

import json
import logging
import re

from pydantic import BaseModel, Field, ValidationError

from app.config import settings
from app.graph.loader import GraphService
from app.llm.client import LLMClient
from app.overlay.model import Evidence, EvidenceSource
from app.skills.loader import SkillLoader

logger = logging.getLogger(__name__)

_FENCE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)
_OBJ = re.compile(r"\{.*\}", re.DOTALL)


class RawExtracted(BaseModel):
    node_id: str
    confidence: float = Field(ge=0.0, le=1.0)
    verbatim: str = ""
    mapping: str = "inferential"


class ExtractionResult(BaseModel):
    evidence: list[Evidence] = Field(default_factory=list)
    flags: list[str] = Field(default_factory=list)


def _node_catalog(graph: GraphService) -> str:
    lines = []
    for nid in graph.evidence_node_ids:
        n = graph.node(nid)
        lines.append(f"- {nid} | {n.label} | cues: {', '.join(n.cues)}")
    return "\n".join(lines)


def _parse_json(text: str) -> dict | None:
    for candidate in (text, *_FENCE.findall(text)):
        candidate = candidate.strip()
        if not candidate:
            continue
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            m = _OBJ.search(candidate)
            if m:
                try:
                    return json.loads(m.group(0))
                except json.JSONDecodeError:
                    continue
    return None


def _normalize_for_substring(s: str) -> str:
    return re.sub(r"\s+", " ", s.lower()).strip()


def _offline_extract(graph: GraphService, user_message: str, turn_id: int) -> list[Evidence]:
    """Trích theo `cues` khi LLM offline — baseline luật, đủ để demo không cần API key."""
    from app.safety.normalize import contains_word, normalize_vi

    norm_msg = normalize_vi(user_message)
    low_msg = user_message.lower()
    out: list[Evidence] = []
    for nid in graph.evidence_node_ids:
        node = graph.node(nid)
        for cue in node.cues:
            if contains_word(norm_msg, normalize_vi(cue)):
                idx = low_msg.find(cue.lower())
                verbatim = user_message[idx: idx + len(cue)] if idx >= 0 else ""
                out.append(
                    Evidence(
                        node_id=nid, confidence=0.70,
                        source=EvidenceSource.SELF_REPORT,
                        turn_ids=[turn_id], verbatim=verbatim,
                    )
                )
                break
    return out


async def extract_evidence(
    *,
    llm: LLMClient,
    skills: SkillLoader,
    graph: GraphService,
    user_message: str,
    recent_turns: str,
    turn_id: int,
    turn_count: int,
    has_assessment: bool,
) -> ExtractionResult:
    system = skills.build(
        "01_EXTRACT_EVIDENCE",
        NODE_CATALOG=_node_catalog(graph),
        RECENT_TURNS=recent_turns or "(chưa có)",
        USER_MESSAGE=user_message,
        TURN_COUNT=turn_count,
        HAS_TAKEN_ASSESSMENT="có" if has_assessment else "chưa",
        # Bước TRÍCH không dùng trí nhớ — chỉ đọc tin nhắn hiện tại. Truyền
        # rỗng để chuỗi "{MEMORY_QUOTES}" không lọt nguyên vào prompt.
        MEMORY_QUOTES="(không dùng ở bước này)",
    )

    flags: list[str] = []

    if getattr(llm, "offline", False):
        return ExtractionResult(
            evidence=_offline_extract(graph, user_message, turn_id),
            flags=["extract_offline_cues"],
        )

    try:
        raw = await llm.complete(
            system=system, user=user_message, max_tokens=800, temperature=0.0, json_mode=True
        )
    except Exception:
        logger.exception("extract: LLM lỗi")
        return ExtractionResult(evidence=[], flags=["extract_llm_error"])

    data = _parse_json(raw)
    if data is None or "evidence" not in data:
        return ExtractionResult(evidence=[], flags=["extract_parse_failed"])

    valid_ids = set(graph.evidence_node_ids)
    haystack = _normalize_for_substring(user_message)
    out: list[Evidence] = []
    for item in data.get("evidence", []) or []:
        try:
            r = RawExtracted(**item)
        except ValidationError:
            flags.append("extract_bad_item")
            continue

        if r.node_id not in valid_ids:
            flags.append("extract_hallucinated_node")
            continue

        vb = (r.verbatim or "").strip()
        if vb and _normalize_for_substring(vb) not in haystack:
            flags.append("extract_verbatim_not_substring")
            continue

        literal = r.mapping.strip().lower() == "literal"
        source = EvidenceSource.SELF_REPORT if literal else EvidenceSource.INFERRED
        cap = settings.self_report_confidence_cap if literal else settings.extract_confidence_cap
        conf = min(max(r.confidence, 0.0), cap)

        out.append(
            Evidence(
                node_id=r.node_id,
                confidence=conf,
                source=source,
                turn_ids=[turn_id],
                verbatim=vb,
            )
        )

    return ExtractionResult(evidence=out, flags=flags)
