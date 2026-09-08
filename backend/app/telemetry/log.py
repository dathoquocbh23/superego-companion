"""
Log có cấu trúc → data/turns.jsonl. docx/08.

⚠️ KHÔNG BAO GIỜ ghi: user_message, verbatim, response_text, session_id gốc, PII.
Chỉ ghi metadata + định danh node. Nuốt lỗi — log hỏng không được làm hỏng lượt chat.
"""
from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone

from app.config import settings
from app.pipeline.context import PipelineContext

logger = logging.getLogger(__name__)


def session_hash(session_id: str) -> str:
    return hashlib.sha256(session_id.encode()).hexdigest()[:6]


def _text_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:4]


def build_record(ctx: PipelineContext) -> dict:
    ov = ctx.overlay
    g = ctx.gate
    safety = ctx.safety

    sentences = len([s for s in ctx.response_text.replace("!", ".").replace("?", ".").split(".") if s.strip()])

    return {
        "turn_id": ctx.turn_id,
        "session_hash": ctx.session_hash,
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),

        # An toàn
        "safety_tier": safety.tier if safety else None,
        "safety_matched": (safety.matched if safety and safety.tier == 3 else []),

        # Đầu vào
        "input_len": ctx.input_len,
        "input_is_chip": ctx.input_is_chip,
        "chip_type": ctx.chip.chip_type if ctx.chip else None,

        # Trích bằng chứng
        "extracted": [
            {"node_id": e.node_id, "confidence": round(e.confidence, 2)} for e in ctx.extracted
        ],
        "extract_failed": ctx.extract_failed,
        "extract_hallucinated": ctx.extract_hallucinated,

        # Overlay SAU lượt này
        "overlay_size": len(ov.evidence),
        "overlay_by_source": ov.by_source_counts(),
        "active_cycles": ov.active_cycles,

        # Quyết định
        "gate": g.gate if g else None,
        "gate_reason": g.reason if g else None,
        "target_nodes": g.target_nodes if g else [],
        "policy_edge_used": g.policy_edge_used if g else None,

        # Đầu ra
        "message_type": ctx.message_type,
        "response_len": len(ctx.response_text),
        "response_sentences": sentences,
        "postcheck_flags": [f for f in ctx.flags if f.startswith("postcheck_")],

        # Quick replies
        "chip_provenance": [
            {
                "text_hash": _text_hash(p.get("text", "")),
                "gate": p.get("gate"),
                "source_node": p.get("source_node"),
                "target_node": p.get("target_node"),
                "is_escape": p.get("is_escape", False),
            }
            for p in ctx.chip_provenance
        ],

        # Hiệu năng
        "latency_ms": ctx.latency_ms,
        "tokens": ctx.tokens,
        "flags": ctx.flags,
    }


def log_turn(ctx: PipelineContext) -> dict | None:
    """Ghi một dòng vào data/turns.jsonl, trả bản ghi vừa dựng.

    Caller đẩy tiếp lên Supabase (app/persistence/turnlog.py, tự retry lỗi
    tạm thời). File hữu ích để đọc nhanh lúc chạy local, nhưng KHÔNG PHẢI lưới
    an toàn khi deploy lên host đĩa tạm thời (Render free tier): container
    khởi động lại là file mất cùng lúc với RAM. Coi Supabase là nơi lưu thật.
    """
    try:
        record = build_record(ctx)
    except Exception:  # pragma: no cover
        logger.exception("build_record failed")
        return None
    try:
        settings.log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(settings.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception:  # pragma: no cover
        # Ghi file hỏng KHÔNG được ngăn việc đẩy lên Supabase — hai đường độc lập.
        logger.exception("log_turn failed")
    return record
