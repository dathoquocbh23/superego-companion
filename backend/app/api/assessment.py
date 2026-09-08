"""GET/POST /api/assessment — bài Likert 10 câu + seed overlay. docx/06 §2.2–§2.3."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config import settings
from app.overlay.model import LIKERT_CONFIDENCE, Evidence, EvidenceSource
from app.overlay.store import get_store

router = APIRouter(prefix="/api", tags=["assessment"])


@lru_cache(maxsize=1)
def _assessment() -> dict:
    return yaml.safe_load(Path(settings.assessment_path).read_text(encoding="utf-8"))


class AssessmentSpec(BaseModel):
    scale: list[dict]
    items: list[dict]
    disclaimer: str


class AssessmentSubmit(BaseModel):
    session_id: str
    answers: dict[str, int]


class AssessmentResult(BaseModel):
    total: int
    average: float
    band: str
    band_label: str
    headline: str
    result_text: str
    next_actions: list[dict]
    disclaimer: str


@router.get("/assessment", response_model=AssessmentSpec)
async def get_assessment() -> AssessmentSpec:
    a = _assessment()
    return AssessmentSpec(scale=a["scale"], items=a["items"], disclaimer=a["disclaimer"].strip())


def _band_for(avg: float) -> dict:
    for b in _assessment()["bands"]:
        if b["min"] <= round(avg, 2) <= b["max"]:
            return b
    return _assessment()["bands"][0]


@router.post("/assessment", response_model=AssessmentResult)
async def submit_assessment(payload: AssessmentSubmit) -> AssessmentResult:
    a = _assessment()
    items = {str(it["id"]): it for it in a["items"]}

    scored = {k: v for k, v in payload.answers.items() if k in items and 1 <= int(v) <= 5}
    if not scored:
        raise HTTPException(status_code=400, detail="Chưa có câu trả lời hợp lệ.")

    total = sum(int(v) for v in scored.values())
    average = round(total / len(items), 2)
    band = _band_for(average)

    # seed overlay: mỗi câu → evidence LIKERT cho node tương ứng
    store = get_store()
    overlay = await store.get(payload.session_id)
    overlay.has_taken_assessment = True
    for qid, val in scored.items():
        node_id = items[qid]["node_id"]
        conf = LIKERT_CONFIDENCE.get(int(val), 0.0)
        if conf <= 0:
            continue
        overlay.merge(
            Evidence(
                node_id=node_id,
                confidence=conf,
                source=EvidenceSource.LIKERT,
                turn_ids=[0],
                verbatim="",
            )
        )
    await store.save(overlay)

    return AssessmentResult(
        total=total,
        average=average,
        band=band["id"],
        band_label=band["label"],
        headline=band["headline"],
        result_text=band["result_text"].strip(),
        next_actions=a["next_actions"],
        disclaimer=a["disclaimer"].strip(),
    )
