"""Lọc an toàn cho chip CLARIFY sinh theo ngữ cảnh (docx/03 §7)."""
import pytest

from app.llm.client import LLMClient
from app.llm.quickreply import _is_safe, _risk_cues, generate_clarify_chips
from app.overlay.model import Overlay


def test_risk_cues_include_vo_vong(graph):
    cues = _risk_cues(graph)
    assert any("vo vong" in c for c in cues)


@pytest.mark.parametrize(
    "chip",
    [
        "Mình mong ít nhất 8",
        "Không phải vì điểm",
        "Nghĩ tới ba mẹ",
        "Cũng không thường lắm",
    ],
)
def test_safe_chips_pass(graph, chip):
    assert _is_safe(chip, _risk_cues(graph))


@pytest.mark.parametrize(
    "chip",
    [
        "Mình thấy vô vọng",          # risk_adjacent cue
        "Chắc mình bị trầm cảm",      # chẩn đoán
        "Mình thấy mình vô dụng",     # mớm
        "Mình không muốn sống nữa",   # khủng hoảng
        "Mình muốn tự tử",            # khủng hoảng
        "Đây là một câu chip rất dài vượt quá giới hạn từ cho phép chắc chắn luôn",
    ],
)
def test_unsafe_chips_rejected(graph, chip):
    assert not _is_safe(chip, _risk_cues(graph))


@pytest.mark.asyncio
async def test_offline_returns_empty(graph, skills):
    llm = LLMClient()  # LLM_OFFLINE=true trong conftest
    assert llm.offline
    out = await generate_clarify_chips(
        llm=llm, skills=skills, graph=graph, overlay=Overlay(session_id="t"),
        bot_question="Bạn kỳ vọng mình được bao nhiêu?", user_message="thi được 6.5 chán ghê",
    )
    assert out == []


class FakeLLM(LLMClient):
    def __init__(self, payload):
        self.offline = False
        self._p = payload

    async def complete(self, **kw):
        return self._p


@pytest.mark.asyncio
async def test_filters_unsafe_from_llm(graph, skills):
    fake = FakeLLM('{"chips": ["Mình mong ít nhất 8", "Chắc mình bị trầm cảm"]}')
    out = await generate_clarify_chips(
        llm=fake, skills=skills, graph=graph, overlay=Overlay(session_id="t"),
        bot_question="Bạn kỳ vọng mình được bao nhiêu?", user_message="thi 6.5 chán ghê",
    )
    assert out == ["Mình mong ít nhất 8"]  # chip chẩn đoán bị loại → chỉ còn 1 → caller fallback
