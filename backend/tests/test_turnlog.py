"""Đẩy turn_logs lên Supabase (app/persistence/turnlog.py). GĐ6b.

Không chạm mạng. Test quan trọng nhất là test_khoa_cua_build_record_khop_cot():
nó khoá hợp đồng giữa build_record() và schema bảng — hai thứ ở hai file cách
xa nhau, lệch nhau là mất bản ghi mà không ai biết.
"""
import pytest

from app.persistence import turnlog as tl


# ── hợp đồng với build_record() và với schema bảng ───────────────────────
def test_khoa_cua_build_record_khop_cot():
    """001_init.sql mục D ghi "Khớp 1-1 với build_record()". Khoá lại bằng test.

    Thêm trường vào build_record mà quên thêm cột: trường đó im lặng biến mất.
    Đổi tên cột mà quên sửa _COLUMNS: PostgREST trả 400, mất cả bản ghi.
    """
    from app.overlay.model import Overlay
    from app.pipeline.context import PipelineContext
    from app.safety.crisis import check_crisis
    from app.telemetry.log import build_record

    ctx = PipelineContext(
        session_id="s", session_hash="abc123", user_message="chào",
        overlay=Overlay(session_id="s"), turn_id=1,
    )
    ctx.safety = check_crisis("chào")
    record = build_record(ctx)

    thua = set(record) - tl._COLUMNS
    thieu = tl._COLUMNS - set(record)
    assert not thua, f"build_record sinh trường không có cột: {sorted(thua)}"
    assert not thieu, f"cột khai báo nhưng build_record không sinh: {sorted(thieu)}"


def test_khong_co_truong_nao_dinh_danh_ca_nhan():
    """Ranh giới của cả thiết kế: turn_logs KHÔNG truy ngược về người được.

    Có user_id / session_id / nguyên văn ở đây là mất đúng lý do khiến bảng này
    dùng được thoải mái mà không phải bận tâm chuyện đồng ý.
    """
    cam = {"user_id", "session_id", "user_message", "response_text", "verbatim", "email"}
    assert not (tl._COLUMNS & cam)
    assert "session_hash" in tl._COLUMNS      # bản băm 6 ký tự, không đảo ngược


# ── payload gửi đi ───────────────────────────────────────────────────────
class _FakeResponse:
    def raise_for_status(self):
        return None


class _FakeClient:
    calls: list[dict] = []

    def __init__(self, *a, **kw):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def post(self, url, headers=None, json=None):
        _FakeClient.calls.append({"url": url, "json": json})
        return _FakeResponse()


@pytest.fixture
def store(monkeypatch):
    _FakeClient.calls = []
    monkeypatch.setattr(tl.httpx, "AsyncClient", _FakeClient)
    s = tl.TurnLogStore("https://x.supabase.co", "key")
    monkeypatch.setattr(type(s), "available", property(lambda self: True))
    return s


@pytest.mark.asyncio
async def test_bo_truong_khong_co_cot(store):
    """Trường lạ lọt vào là PostgREST trả 400 và mất CẢ lô."""
    assert await store.push([{"session_hash": "a", "turn_id": 1, "truong_la": 9}])
    gui = _FakeClient.calls[0]["json"][0]
    assert "truong_la" not in gui
    assert gui["session_hash"] == "a"


@pytest.mark.asyncio
async def test_moi_ban_ghi_cung_tap_khoa(store):
    """PGRST102 "All object keys must match" — cùng cái bẫy đã sập ở messages."""
    assert await store.push([
        {"session_hash": "a", "turn_id": 1},
        {"session_hash": "b", "turn_id": 2, "gate": "CLARIFY", "flags": ["x"]},
    ])
    gui = _FakeClient.calls[0]["json"]
    assert {frozenset(r) for r in gui} == {frozenset(tl._COLUMNS)}
    assert gui[0]["gate"] is None and gui[1]["gate"] == "CLARIFY"


@pytest.mark.asyncio
async def test_day_ca_lo_trong_mot_loi_goi(store):
    """Script nạp ngược đẩy theo lô 200 — không được thành 200 request."""
    assert await store.push([{"session_hash": str(i), "turn_id": i} for i in range(50)])
    assert len(_FakeClient.calls) == 1
    assert len(_FakeClient.calls[0]["json"]) == 50


@pytest.mark.asyncio
async def test_rong_thi_khong_goi_mang(store):
    assert await store.push([]) is False
    assert _FakeClient.calls == []


# ── hỏng thì thoái hoá, không làm hỏng lượt chat ─────────────────────────
class _BoomClient(_FakeClient):
    async def post(self, *a, **kw):
        raise RuntimeError("supabase chet")


@pytest.mark.asyncio
async def test_supabase_chet_thi_tu_tat_khong_raise(monkeypatch):
    monkeypatch.setattr(tl.httpx, "AsyncClient", _BoomClient)
    s = tl.TurnLogStore("https://x.supabase.co", "key")
    monkeypatch.setattr(type(s), "available", property(lambda self: not s._degraded))
    assert await s.push([{"session_hash": "a", "turn_id": 1}]) is False
    assert s._degraded is True
    assert await s.push([{"session_hash": "b", "turn_id": 2}]) is False


@pytest.mark.asyncio
async def test_thieu_cau_hinh_thi_im_lang():
    """conftest để SUPABASE_URL rỗng → no-op, không raise."""
    s = tl.TurnLogStore("", "")
    assert s.available is False
    assert await s.push([{"session_hash": "a", "turn_id": 1}]) is False


# ── log_turn vẫn ghi file VÀ trả bản ghi ─────────────────────────────────
def test_log_turn_van_ghi_file_va_tra_ban_ghi(tmp_path, monkeypatch):
    """File là nguồn chính, Supabase chỉ là bản sao — đừng đánh đổi cái nào."""
    import json

    from app.config import settings
    from app.overlay.model import Overlay
    from app.pipeline.context import PipelineContext
    from app.safety.crisis import check_crisis
    from app.telemetry.log import log_turn

    duong = tmp_path / "turns.jsonl"
    monkeypatch.setattr(settings, "log_path", duong)

    ctx = PipelineContext(
        session_id="s", session_hash="abc123", user_message="chào",
        overlay=Overlay(session_id="s"), turn_id=1,
    )
    ctx.safety = check_crisis("chào")

    record = log_turn(ctx)
    assert record is not None and record["session_hash"] == "abc123"
    assert json.loads(duong.read_text(encoding="utf-8").strip())["turn_id"] == 1
