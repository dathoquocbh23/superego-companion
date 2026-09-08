"""Pydantic model cho node / edge / cycle. docx/06 §6."""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

EVIDENCE_TYPES = {"manifestation", "trigger", "affect", "impact"}
CONTENT_TYPES = {"concept", "coping", "riskflag", "resource"}

NodeType = Literal[
    "manifestation", "trigger", "affect", "impact",
    "concept", "coping", "riskflag", "resource",
]
EdgeType = Literal[
    "triggers", "produces", "impairs", "reinforces",
    "explained_by", "addressed_by", "escalates_to",
]


class Node(BaseModel):
    id: str
    type: NodeType
    label: str
    likert_item: int | None = None
    risk_adjacent: bool = False
    # D5 — node mang PHAN QUYET ve gia tri ban than. Khong duoc lam target cua
    # CLARIFY khi overlay con qua it bang chung: nham vao no o luot 1 tuc la bot
    # di hoi "ban co thay minh dang bi phat khong" khi hoc sinh moi noi mot cau.
    late_stage: bool = False
    source_doc: str | None = None
    content_ref: str | None = None
    cues: list[str] = Field(default_factory=list)
    note: str | None = None
    trigger_condition: str | None = None
    resource_kind: str | None = None

    @property
    def is_evidence(self) -> bool:
        return self.type in EVIDENCE_TYPES

    @property
    def is_content(self) -> bool:
        return self.type in CONTENT_TYPES


class Edge(BaseModel):
    from_: str = Field(alias="from")
    to: str
    type: EdgeType
    priority: int | None = None
    condition: dict[str, Any] | None = None

    model_config = {"populate_by_name": True}


class Cycle(BaseModel):
    id: str
    label: str
    nodes: list[str]
    min_nodes_to_activate: int = 4


class BridgeConfig(BaseModel):
    default_resource: str = "s-ba-me"
    fallback_resources: list[str] = Field(default_factory=lambda: ["s-tu-van-hoc-duong", "s-gvcn"])
