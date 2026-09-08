"""PipelineContext — trạng thái một lượt chat. docx/06 §3."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.gate.decide import GateDecision
from app.overlay.model import Evidence, Overlay
from app.safety.chips import ChipSignal
from app.safety.crisis import SafetyResult


@dataclass
class PipelineContext:
    session_id: str
    session_hash: str
    user_message: str
    overlay: Overlay
    turn_id: int

    safety: SafetyResult | None = None
    chip: ChipSignal | None = None
    extracted: list[Evidence] = field(default_factory=list)
    gate: GateDecision | None = None

    message_type: str = "REFLECT"
    response_text: str = ""
    card: dict[str, Any] | None = None
    quick_replies: list[str] = field(default_factory=list)
    chip_provenance: list[dict[str, Any]] = field(default_factory=list)
    flags: list[str] = field(default_factory=list)

    # đo lường
    latency_ms: dict[str, int] = field(default_factory=dict)
    tokens: dict[str, int] = field(default_factory=dict)
    input_len: int = 0
    input_is_chip: bool = False
    extract_failed: bool = False
    extract_hallucinated: list[str] = field(default_factory=list)
