import pytest

from app.llm.client import LLMClient
from app.llm.extract import extract_evidence
from app.overlay.model import EvidenceSource


class FakeLLM(LLMClient):
    def __init__(self, payload: str):
        self.offline = False
        self._payload = payload

    async def complete(self, **kw):
        return self._payload


@pytest.mark.asyncio
async def test_verbatim_must_be_substring(graph, skills):
    fake = FakeLLM('{"evidence":[{"node_id":"m-tu-trach","confidence":0.7,"verbatim":"mình tệ thật","mapping":"literal"}]}')
    res = await extract_evidence(
        llm=fake, skills=skills, graph=graph,
        user_message="hôm nay mình vui lắm",  # KHÔNG chứa verbatim
        recent_turns="", turn_id=1, turn_count=1, has_assessment=False,
    )
    assert res.evidence == []
    assert "extract_verbatim_not_substring" in res.flags


@pytest.mark.asyncio
async def test_hallucinated_node_dropped(graph, skills):
    fake = FakeLLM('{"evidence":[{"node_id":"m-khong-ton-tai","confidence":0.5,"verbatim":"abc","mapping":"literal"}]}')
    res = await extract_evidence(
        llm=fake, skills=skills, graph=graph,
        user_message="abc def", recent_turns="", turn_id=1, turn_count=1, has_assessment=False,
    )
    assert res.evidence == []
    assert "extract_hallucinated_node" in res.flags


@pytest.mark.asyncio
async def test_literal_maps_self_report_capped(graph, skills):
    fake = FakeLLM('{"evidence":[{"node_id":"m-tu-trach","confidence":0.99,"verbatim":"mình tệ thật","mapping":"literal"}]}')
    res = await extract_evidence(
        llm=fake, skills=skills, graph=graph,
        user_message="mình tệ thật chứ sao", recent_turns="", turn_id=2, turn_count=2, has_assessment=False,
    )
    assert len(res.evidence) == 1
    ev = res.evidence[0]
    assert ev.source == EvidenceSource.SELF_REPORT
    assert ev.confidence <= 0.75


@pytest.mark.asyncio
async def test_inferential_maps_inferred_capped(graph, skills):
    fake = FakeLLM('{"evidence":[{"node_id":"a-toi-loi","confidence":0.9,"verbatim":"ba mẹ tốn tiền","mapping":"inferential"}]}')
    res = await extract_evidence(
        llm=fake, skills=skills, graph=graph,
        user_message="ba mẹ tốn tiền học thêm cho mình", recent_turns="", turn_id=3, turn_count=3, has_assessment=False,
    )
    assert res.evidence[0].source == EvidenceSource.INFERRED
    assert res.evidence[0].confidence <= 0.60


@pytest.mark.asyncio
async def test_bad_json_returns_empty(graph, skills):
    fake = FakeLLM("xin chào mình không phải JSON")
    res = await extract_evidence(
        llm=fake, skills=skills, graph=graph,
        user_message="abc", recent_turns="", turn_id=1, turn_count=1, has_assessment=False,
    )
    assert res.evidence == []
    assert "extract_parse_failed" in res.flags
