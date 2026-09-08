"""End-to-end pipeline ở chế độ LLM offline."""
import pytest

from app.overlay.store import get_store
from app.pipeline.runner import run_chat_turn


async def _new_session():
    store = get_store()
    from app.overlay.model import Overlay
    import uuid
    sid = str(uuid.uuid4())
    await store.save(Overlay(session_id=sid))
    return sid


async def _collect(sid, msg):
    events = []
    async for ev, data in run_chat_turn(sid, msg):
        events.append((ev, data))
    return events


@pytest.mark.asyncio
async def test_escalate_emits_no_token(monkeypatch):
    # đảm bảo KHÔNG lời gọi LLM nào phát sinh khi ESCALATE
    from app.llm import client as client_mod

    called = {"n": 0}
    real_get = client_mod.get_llm

    class Guard(client_mod.LLMClient):
        def __init__(self):
            self.offline = True
        async def complete(self, **kw):
            called["n"] += 1
            return "x"
        async def stream(self, **kw):
            called["n"] += 1
            if False:
                yield ""

    monkeypatch.setattr(client_mod, "get_llm", lambda: Guard())
    from app.pipeline import runner as runner_mod
    monkeypatch.setattr(runner_mod, "get_llm", lambda: Guard())

    sid = await _new_session()
    events = await _collect(sid, "mình muốn tự tử")
    names = [e for e, _ in events]

    assert "token" not in names
    assert ("card", ) or True
    assert any(e == "card" and d.get("type") == "CRISIS_CARD" for e, d in events)
    assert called["n"] == 0
    # footer không có quick replies
    footer = next(d for e, d in events if e == "footer")
    assert footer["quickReplies"] == []


@pytest.mark.asyncio
async def test_normal_turn_offline_flows():
    sid = await _new_session()
    events = await _collect(sid, "hôm nay thi toán được 6.5 chán ghê")
    names = [e for e, _ in events]
    assert names[0] == "meta"
    assert names[-1] == "done"
    meta = events[0][1]
    assert meta["gate"] in {"CLARIFY", "REFLECT", "REFUSAL"}


@pytest.mark.asyncio
async def test_history_persists_between_turns():
    sid = await _new_session()
    await _collect(sid, "mình hay tự trách bản thân")
    await _collect(sid, "nhất là khi thi điểm kém")
    overlay = await get_store().get(sid)
    assert overlay.turn_count == 2
    assert len(overlay.history) >= 3


@pytest.mark.asyncio
async def test_refusal_path_offline():
    sid = await _new_session()
    events = await _collect(sid, "giải bài tập toán này giùm mình với")
    meta = events[0][1]
    assert meta["gate"] == "REFUSAL"


# ── SUPPORT: câu dẫn không được nhại lại lượt REFLECT ngay trước ─────────
# Ca thật quan sát 07/09/2026: bấm "Đúng vậy" xong, thẻ coping hiện ra kèm
# câu dẫn y hệt câu REFLECT vừa đọc, lại còn hỏi xác nhận lần hai.
from app.safety.postcheck import is_near_duplicate  # noqa: E402

_REFLECT_TRUOC = (
    'Mình để ý là bạn nói "mình thua crush của mình" và bạn nhắc đến "9 điểm" '
    "của bạn ấy. Có phải là bạn đang cảm thấy mình không bằng bạn ấy, và điều "
    "này khiến bạn buồn không?"
)


def test_bat_duoc_cau_dan_nhai_y_nguyen():
    assert is_near_duplicate(_REFLECT_TRUOC, _REFLECT_TRUOC)


def test_bat_duoc_cau_dan_nhai_gan_giong():
    gan_giong = (
        'Mình để ý là bạn nói "mình thua crush của mình" và bạn nhắc tới "9 điểm" '
        "của bạn ấy. Có phải bạn đang cảm thấy mình không bằng bạn ấy không?"
    )
    assert is_near_duplicate(gan_giong, _REFLECT_TRUOC)


def test_cau_dan_khac_han_thi_de_yen():
    assert not is_near_duplicate(
        "Cảm ơn bạn đã nói thẳng như vậy. Có một cách nhìn khác, bạn thử xem sao:",
        _REFLECT_TRUOC,
    )


def test_khong_bao_trung_khi_mot_ben_rong():
    assert not is_near_duplicate("", _REFLECT_TRUOC)
    assert not is_near_duplicate(_REFLECT_TRUOC, "")
