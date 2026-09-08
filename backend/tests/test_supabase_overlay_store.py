"""Overlay store trên Supabase (app/overlay/supabase_store.py).

Landmine gốc: Render free tier không có Redis cục bộ. Không cấu hình
OVERLAY_BACKEND=supabase thì OverlayStore tự rơi về RAM-trong-tiến-trình ÂM
THẦM, và container khởi động lại là mọi phiên quên sạch — nặng hơn nhiều so
với mất turns.jsonl vì nó phá logic hội thoại đang sống, không chỉ số liệu.
"""
from datetime import datetime, timedelta, timezone

import pytest

from app.overlay.model import Evidence, EvidenceSource, Overlay
from app.overlay.supabase_store import SupabaseOverlayStore


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload

    def raise_for_status(self):
        return None


class _FakeClient:
    """Bàn làm việc giả: một 'bảng' overlay_state trong dict, khớp ngữ nghĩa
    upsert-theo-session_id thật của PostgREST (on_conflict=session_id)."""

    bang: dict[str, dict] = {}
    calls: list[dict] = []

    def __init__(self, *a, **kw):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def get(self, url, headers=None, params=None):
        _FakeClient.calls.append({"verb": "GET", "url": url, "params": params})
        sid = params["session_id"].removeprefix("eq.")
        row = _FakeClient.bang.get(sid)
        return _FakeResponse([row] if row else [])

    async def post(self, url, headers=None, params=None, json=None):
        _FakeClient.calls.append({"verb": "POST", "url": url, "params": params, "json": json})
        _FakeClient.bang[json["session_id"]] = {
            "data": json["data"],
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        return _FakeResponse([])


@pytest.fixture
def client_gia(monkeypatch):
    import app.overlay.supabase_store as mod

    _FakeClient.bang = {}
    _FakeClient.calls = []
    monkeypatch.setattr(mod.httpx, "AsyncClient", _FakeClient)
    return _FakeClient


@pytest.fixture
def store(client_gia):
    return SupabaseOverlayStore("https://x.supabase.co", "key", ttl_seconds=86_400)


def _overlay_co_evidence(session_id: str) -> Overlay:
    ov = Overlay(session_id=session_id)
    ov.merge(Evidence(
        node_id="t-quan-he", confidence=0.75, source=EvidenceSource.SELF_REPORT,
        turn_ids=[1], verbatim="thất tình",
    ))
    ov.turn_count = 1
    return ov


# ── vòng đời cơ bản ───────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_session_moi_tra_overlay_rong(store, client_gia):
    ov = await store.get("chua-tung-thay")
    assert ov.session_id == "chua-tung-thay"
    assert ov.evidence == {}


@pytest.mark.asyncio
async def test_save_roi_get_lai_dung_du_lieu_TRONG_CUNG_TIEN_TRINH(store):
    """Đây là đường phổ biến nhất: nhiều lượt chat trong một phiên, cùng
    tiến trình còn sống — không được đọc nhầm/mất evidence giữa các lượt."""
    goc = _overlay_co_evidence("s1")
    await store.save(goc)

    lai = await store.get("s1")
    assert lai.evidence.keys() == goc.evidence.keys()
    assert lai.evidence["t-quan-he"].verbatim == "thất tình"
    assert lai.turn_count == 1


@pytest.mark.asyncio
async def test_get_lien_tiep_phuc_vu_tu_RAM_khong_goi_mang_lai(store, client_gia):
    """Cache đọc — đây là chỗ giữ latency thấp cho đường phản hồi.

    get() đầu tiên (miss) phải hỏi mạng đúng 1 lần; các get() sau trong CÙNG
    tiến trình phục vụ từ RAM, KHÔNG round-trip thêm.
    """
    await store.save(_overlay_co_evidence("s1"))
    so_lan_truoc = len(client_gia.calls)

    await store.get("s1")
    await store.get("s1")
    await store.get("s1")

    assert len(client_gia.calls) == so_lan_truoc, "get() lặp lại không được chạm mạng"


# ── TTL kiểm ở tầng client (bảng không tự xoá) ───────────────────────────
@pytest.mark.asyncio
async def test_qua_ttl_thi_coi_nhu_chua_tung_co(client_gia):
    """Bảng KHÔNG tự xoá theo thời gian như Redis EX — khác Redis, TTL chỉ có
    ý nghĩa nếu client tự kiểm lúc đọc. Test này khoá đúng hành vi đó."""
    client_gia.bang["s-cu"] = {
        "data": Overlay(session_id="s-cu").model_dump(mode="json"),
        "updated_at": (datetime.now(timezone.utc) - timedelta(days=2)).isoformat(),
    }
    store = SupabaseOverlayStore("https://x.supabase.co", "key", ttl_seconds=86_400)  # 1 ngày
    ov = await store.get("s-cu")
    assert ov.evidence == {}          # coi như phiên mới, không phải lỗi


@pytest.mark.asyncio
async def test_chua_qua_ttl_thi_doc_binh_thuong(client_gia):
    client_gia.bang["s-moi"] = {
        "data": _overlay_co_evidence("s-moi").model_dump(mode="json"),
        "updated_at": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(),
    }
    store = SupabaseOverlayStore("https://x.supabase.co", "key", ttl_seconds=86_400)
    ov = await store.get("s-moi")
    assert "t-quan-he" in ov.evidence


# ── upsert đúng ngữ nghĩa ─────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_save_dung_upsert_theo_session_id(store, client_gia):
    await store.save(_overlay_co_evidence("s1"))
    call = client_gia.calls[0]
    assert call["url"].endswith("/rest/v1/overlay_state")
    assert call["params"] == {"on_conflict": "session_id"}
    assert call["json"]["session_id"] == "s1"


@pytest.mark.asyncio
async def test_ghi_de_khong_de_lai_du_lieu_cu(store):
    """Hai lượt liên tiếp: lượt 2 phải THAY, không CỘNG DỒN evidence sai cách
    (merge() đã lo phần trộn — ở đây chỉ kiểm store không tự ý giữ bản cũ)."""
    ov1 = _overlay_co_evidence("s1")
    await store.save(ov1)

    ov1.turn_count = 2
    ov1.merge(Evidence(
        node_id="a-buon", confidence=0.7, source=EvidenceSource.SELF_REPORT,
        turn_ids=[2], verbatim="rất buồn",
    ))
    await store.save(ov1)

    lai = await store.get("s1")
    assert lai.turn_count == 2
    assert set(lai.evidence) == {"t-quan-he", "a-buon"}


# ── hỏng thì thoái hoá, không làm hỏng lượt chat ─────────────────────────
class _BoomClient(_FakeClient):
    async def get(self, *a, **kw):
        raise RuntimeError("supabase chet")

    async def post(self, *a, **kw):
        raise RuntimeError("supabase chet")


@pytest.mark.asyncio
async def test_supabase_chet_thi_roi_ve_RAM_khong_raise(monkeypatch):
    import app.overlay.supabase_store as mod

    monkeypatch.setattr(mod.httpx, "AsyncClient", _BoomClient)
    store = SupabaseOverlayStore("https://x.supabase.co", "key", ttl_seconds=86_400)

    ov = _overlay_co_evidence("s1")
    await store.save(ov)                       # không raise, dù mạng chết
    assert store._degraded is True

    lai = await store.get("s1")                # phục vụ từ RAM cache, không mạng
    assert "t-quan-he" in lai.evidence


@pytest.mark.asyncio
async def test_thieu_cau_hinh_thi_luon_dung_RAM():
    store = SupabaseOverlayStore("", "", ttl_seconds=86_400)
    assert store.available is False
    ov = _overlay_co_evidence("s1")
    await store.save(ov)
    lai = await store.get("s1")
    assert "t-quan-he" in lai.evidence


# ── factory dispatch ──────────────────────────────────────────────────────
def test_factory_chon_dung_class_theo_backend(monkeypatch):
    """get_store() không được đổi hành vi mặc định khi chưa cấu hình gì."""
    import app.overlay.store as store_mod
    from app.overlay.store import OverlayStore

    monkeypatch.setattr(store_mod, "_store", None)
    monkeypatch.setattr(store_mod.settings, "overlay_backend", "redis")
    assert isinstance(store_mod.get_store(), OverlayStore)

    monkeypatch.setattr(store_mod, "_store", None)
    monkeypatch.setattr(store_mod.settings, "overlay_backend", "supabase")
    assert isinstance(store_mod.get_store(), SupabaseOverlayStore)

    monkeypatch.setattr(store_mod, "_store", None)
