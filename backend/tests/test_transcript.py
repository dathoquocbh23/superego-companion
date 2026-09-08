"""Ghi hội thoại nguyên văn vào Supabase (app/persistence/transcript.py). GĐ6.

Không chạm mạng: thay httpx.AsyncClient bằng bản giả để bắt đúng payload gửi đi.
"""
import pytest

from app.persistence import transcript as tr


# ── tiêu đề ───────────────────────────────────────────────────────────────
def test_tieu_de_khop_luat_cua_frontend():
    """Cùng luật với titleFrom() ở frontend/src/lib/conversations.ts.

    Lệch nhau thì sidebar (localStorage) và Supabase hiện hai tiêu đề khác nhau
    cho cùng một phiên.
    """
    assert tr.title_from("hôm nay thi toán được 6.5") == "hôm nay thi toán được 6.5"
    assert tr.title_from("") == "Cuộc trò chuyện mới"
    assert tr.title_from("   ") == "Cuộc trò chuyện mới"
    assert tr.title_from("a  b\n c") == "a b c"          # gom khoảng trắng


def test_tieu_de_cat_42_ky_tu():
    dai = "x" * 60
    t = tr.title_from(dai)
    assert t == "x" * 42 + "…"


# ── tắt / thiếu cấu hình ─────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_thieu_cau_hinh_thi_im_lang_khong_no(monkeypatch):
    """conftest để SUPABASE_URL rỗng → mọi lời gọi phải là no-op, không raise."""
    store = tr.TranscriptStore("", "")
    assert store.available is False
    assert await store.ensure_conversation("s1", None) is None
    await store.set_title("c1", "x")
    await store.record_messages("c1", [{"role": "user", "message_type": "USER"}])


# ── payload gửi đi ────────────────────────────────────────────────────────
class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload

    def raise_for_status(self):
        return None


class _FakeClient:
    """Ghi lại mọi request thay vì gửi đi. Dùng làm context manager như httpx."""

    calls: list[dict] = []

    def __init__(self, *a, **kw):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def post(self, url, headers=None, params=None, json=None):
        _FakeClient.calls.append({"verb": "POST", "url": url, "params": params, "json": json})
        return _FakeResponse([{"id": "conv-123"}])

    async def patch(self, url, headers=None, params=None, json=None):
        _FakeClient.calls.append({"verb": "PATCH", "url": url, "params": params, "json": json})
        return _FakeResponse([])


@pytest.fixture
def store(monkeypatch):
    _FakeClient.calls = []
    monkeypatch.setattr(tr.httpx, "AsyncClient", _FakeClient)
    s = tr.TranscriptStore("https://x.supabase.co", "key")
    monkeypatch.setattr(type(s), "available", property(lambda self: True))
    return s


@pytest.mark.asyncio
async def test_upsert_theo_session_id(store):
    """Upsert chứ không insert thuần: overlay hết TTL rồi quay lại cùng
    session_id thì phải nối vào ĐÚNG hội thoại cũ, không đẻ hàng thứ hai."""
    cid = await store.ensure_conversation("sess-1", "user-1")
    assert cid == "conv-123"
    call = _FakeClient.calls[0]
    assert call["url"].endswith("/rest/v1/conversations")
    assert call["params"] == {"on_conflict": "session_id"}
    assert call["json"] == {"session_id": "sess-1", "user_id": "user-1"}


@pytest.mark.asyncio
async def test_ghi_hai_message_trong_MOT_loi_goi(store):
    """Tách hai request thì có lúc câu hỏi đã lưu mà câu trả lời chưa."""
    await store.record_messages("conv-123", [
        {"turn_id": 1, "role": "user", "message_type": "USER", "content": "chào"},
        {"turn_id": 1, "role": "assistant", "message_type": "REFLECT", "content": "ừ"},
    ])
    assert len(_FakeClient.calls) == 1
    gui = _FakeClient.calls[0]["json"]
    assert len(gui) == 2
    assert all(r["conversation_id"] == "conv-123" for r in gui)


@pytest.mark.asyncio
async def test_moi_hang_co_CUNG_tap_khoa(store):
    """Hồi quy PGRST102 "All object keys must match" (gặp thật 07/09/2026).

    PostgREST đòi mọi object trong một insert hàng loạt phải cùng tập khoá.
    Hàng `user` không có card/quick_replies, hàng `assistant` có → 400, mất cả
    lượt ghi. Lỗi này KHÔNG lộ ra ở test dùng một hàng.
    """
    await store.record_messages("conv-123", [
        {"turn_id": 1, "role": "user", "message_type": "USER", "content": "chào"},
        {"turn_id": 1, "role": "assistant", "message_type": "COPING_CARD",
         "content": "", "card": {"type": "COPING_CARD"}, "quick_replies": ["a"]},
    ])
    gui = _FakeClient.calls[0]["json"]
    assert len(gui) == 2
    assert {frozenset(r) for r in gui} == {frozenset(gui[0])}, "tập khoá phải giống hệt nhau"
    assert gui[0]["card"] is None and gui[1]["card"] == {"type": "COPING_CARD"}


@pytest.mark.asyncio
async def test_loai_message_type_ngoai_danh_sach(store):
    """CHECK constraint của bảng sẽ trả 400 và làm MẤT CẢ lượt ghi.

    Chặn ở Python để một gate mới thêm sau này không âm thầm phá đường lưu —
    đúng kiểu bẫy mà ORIENT suýt sập vào (nó phải map về REFLECT).
    """
    await store.record_messages("conv-123", [
        {"turn_id": 1, "role": "user", "message_type": "USER", "content": "a"},
        {"turn_id": 1, "role": "assistant", "message_type": "ORIENT", "content": "b"},
    ])
    gui = _FakeClient.calls[0]["json"]
    assert [r["message_type"] for r in gui] == ["USER"]


@pytest.mark.asyncio
async def test_toan_bo_message_hong_thi_khong_goi_mang(store):
    await store.record_messages("conv-123", [{"role": "assistant", "message_type": "XXX"}])
    assert _FakeClient.calls == []


@pytest.mark.asyncio
async def test_moi_gate_hien_co_deu_qua_duoc_whitelist():
    """Khoá ngược: mọi message_type runner sinh ra phải nằm trong CHECK constraint."""
    from app.pipeline.runner import MESSAGE_TYPE_BY_GATE

    for gate, mt in MESSAGE_TYPE_BY_GATE.items():
        assert mt in tr._MESSAGE_TYPES, f"{gate} -> {mt}"
    for mt in ("INSIGHT_CARD", "KNOWLEDGE_CARD"):   # runner đặt riêng, không qua bảng
        assert mt in tr._MESSAGE_TYPES


# ── hỏng thì thoái hoá, không làm hỏng lượt chat ─────────────────────────
class _BoomClient(_FakeClient):
    async def post(self, *a, **kw):
        raise RuntimeError("supabase chet")


@pytest.mark.asyncio
async def test_supabase_chet_thi_tu_tat_khong_raise(monkeypatch):
    monkeypatch.setattr(tr.httpx, "AsyncClient", _BoomClient)
    s = tr.TranscriptStore("https://x.supabase.co", "key")
    monkeypatch.setattr(type(s), "available", property(lambda self: not s._degraded))
    assert await s.ensure_conversation("s", None) is None
    assert s._degraded is True
    # đã thoái hoá → lần sau im lặng bỏ qua, không thử lại liên tục
    await s.record_messages("c", [{"role": "user", "message_type": "USER"}])
