"""Bộ nhớ dài hạn — kiểm các tính chất AN TOÀN, không phải kiểm CRUD.

Cái dễ hỏng ở đây không phải "có ghi được xuống DB không" mà là "bot có lấy
chuyện tháng trước ra nói như thể hôm nay không". docx/12 §5.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.config import settings
from app.gate.decide import REFLECT, decide_gate
from app.memory.decay import decayed_confidence
from app.memory.service import seed_overlay
from app.memory.store import MemoryNode
from app.overlay.model import Evidence, EvidenceSource, Overlay
from app.safety.crisis import check_crisis


def _now():
    return datetime.now(timezone.utc)


def _remembered(node_id: str, conf: float = 0.5) -> Evidence:
    return Evidence(
        node_id=node_id, confidence=conf, source=EvidenceSource.REMEMBERED, verbatim=""
    )


# ── chốt chặn: bộ test không được chạm Supabase thật ───────────────────
def test_bo_test_khong_cham_supabase():
    """`.env` thật có SUPABASE_* + MEMORY_ENABLED=true. conftest phải ghi đè.

    Thiếu chốt này thì bộ test âm thầm gọi mạng: chậm, và đỏ mỗi khi Supabase
    sập hoặc key xoay — đỏ vì lý do chẳng liên quan gì tới code.
    """
    assert settings.memory_ready is False
    assert settings.supabase_url == ""


# ── phân rã ────────────────────────────────────────────────────────────
def test_phan_ra_dung_ban_ra():
    t = _now() - timedelta(days=30)
    assert decayed_confidence(0.8, t, half_life_days=30) == pytest.approx(0.4, abs=0.01)


def test_phan_ra_moi_tinh_thi_giu_nguyen():
    assert decayed_confidence(0.8, _now(), half_life_days=30) == pytest.approx(0.8, abs=0.01)


def test_phan_ra_lau_qua_thi_gan_bang_khong():
    t = _now() - timedelta(days=365)
    assert decayed_confidence(0.9, t, half_life_days=30) < 0.01


# ── REMEMBERED không được phát ngôn ───────────────────────────────────
def test_remembered_khong_duoc_phat_ngon():
    assert _remembered("m-tu-trach").can_be_spoken is False


def test_remembered_khong_lot_vao_speakable_verbatims():
    ov = Overlay(session_id="s")
    ov.evidence["m-tu-trach"] = Evidence(
        node_id="m-tu-trach", confidence=0.5,
        source=EvidenceSource.REMEMBERED, verbatim="mình dở quá",
    )
    assert ov.speakable_verbatims() == {}


def test_tran_confidence_cua_remembered_duoi_nguong_reflect():
    """Node nhớ lại KHÔNG BAO GIỜ tự đủ mạnh để bot khẳng định."""
    assert settings.memory_seed_confidence_cap < settings.confidence_threshold
    e = _remembered("m-tu-trach", conf=0.99)
    ov = Overlay(session_id="s")
    ov.merge(e)
    assert ov.confidence("m-tu-trach") <= settings.memory_seed_confidence_cap


# ── REMEMBERED không tự kích REFLECT ──────────────────────────────────
def test_ba_node_nho_lai_van_khong_kich_reflect(graph):
    ov = Overlay(session_id="s")
    for nid in ("m-tu-trach", "m-chua-du-tot", "m-hiem-hai-long"):
        ov.merge(_remembered(nid))
    d = decide_gate(graph, ov, check_crisis("hôm nay bình thường"), None)
    assert d.gate != REFLECT


# ── lời hôm nay đè lời cũ ─────────────────────────────────────────────
def test_bang_chung_moi_de_len_bo_nho():
    ov = Overlay(session_id="s")
    ov.merge(_remembered("m-tu-trach", conf=0.5))
    ov.merge(Evidence(
        node_id="m-tu-trach", confidence=0.75,
        source=EvidenceSource.SELF_REPORT, verbatim="tại mình hết",
    ))
    e = ov.evidence["m-tu-trach"]
    assert e.source == EvidenceSource.SELF_REPORT
    assert e.can_be_spoken


def test_bo_nho_khong_de_len_bang_chung_moi():
    ov = Overlay(session_id="s")
    ov.merge(Evidence(
        node_id="m-tu-trach", confidence=0.75,
        source=EvidenceSource.SELF_REPORT, verbatim="tại mình hết",
    ))
    ov.merge(_remembered("m-tu-trach", conf=0.5))
    assert ov.evidence["m-tu-trach"].source == EvidenceSource.SELF_REPORT
    assert ov.confidence("m-tu-trach") == pytest.approx(0.75)


# ── seed_overlay ──────────────────────────────────────────────────────
async def test_khong_dang_nhap_thi_khong_nap_gi(graph):
    ov = Overlay(session_id="s")
    assert await seed_overlay(ov, None, graph) == 0
    assert ov.evidence == {}


async def test_memory_tat_thi_khong_nap_gi(graph):
    """Bộ nhớ tắt (conftest ép) → app chạy y như trước khi có tính năng."""
    ov = Overlay(session_id="s", user_id="u1")
    assert await seed_overlay(ov, "u1", graph) == 0
    assert ov.evidence == {}


async def test_khong_nap_node_risk_adjacent(graph, monkeypatch):
    """a-vo-vong là risk_adjacent — mở phiên đã nghiêng sẵn về vô vọng là mớm."""
    ov = Overlay(session_id="s", user_id="u1")

    class FakeStore:
        async def memory_enabled_for(self, uid):
            return True

        async def load(self, uid, limit):
            return [
                MemoryNode("a-vo-vong", 0.9, 5, _now()),
                MemoryNode("m-tu-trach", 0.8, 5, _now()),
            ]

    monkeypatch.setattr("app.memory.service.get_memory_store", lambda: FakeStore())
    monkeypatch.setattr(settings, "memory_enabled", True)
    monkeypatch.setattr(settings, "supabase_url", "https://x.supabase.co")
    monkeypatch.setattr(settings, "supabase_service_role_key", "k")

    assert await seed_overlay(ov, "u1", graph) == 1
    assert "a-vo-vong" not in ov.evidence
    assert ov.evidence["m-tu-trach"].source == EvidenceSource.REMEMBERED


async def test_node_qua_cu_thi_bo(graph, monkeypatch):
    ov = Overlay(session_id="s", user_id="u1")

    class FakeStore:
        async def memory_enabled_for(self, uid):
            return True

        async def load(self, uid, limit):
            # 0.8 sau 1 năm, bán rã 30 ngày → gần 0
            return [MemoryNode("m-tu-trach", 0.8, 3, _now() - timedelta(days=365))]

    monkeypatch.setattr("app.memory.service.get_memory_store", lambda: FakeStore())
    monkeypatch.setattr(settings, "memory_enabled", True)
    monkeypatch.setattr(settings, "supabase_url", "https://x.supabase.co")
    monkeypatch.setattr(settings, "supabase_service_role_key", "k")

    assert await seed_overlay(ov, "u1", graph) == 0


# ── memory_quotes: ranh giới NHỚ SỰ VIỆC vs NHẮC LỜI TỰ PHÁN XÉT ────────
# Đây là luật quan trọng nhất sau khi bộ nhớ bắt đầu lưu nguyên văn
# (004_verbatim.sql). docx/12 §5.1.
from app.memory.service import memory_quotes  # noqa: E402


def _nho(node_id: str, vb: str) -> Evidence:
    return Evidence(
        node_id=node_id, confidence=0.4,
        source=EvidenceSource.REMEMBERED, verbatim=vb,
    )


def test_nho_duoc_su_viec_trigger(graph):
    ov = Overlay(session_id="s")
    ov.evidence["t-diem-so"] = _nho("t-diem-so", "6.5")
    assert memory_quotes(ov, graph) == [("Kết quả học tập / điểm số", "6.5")]


def test_nho_duoc_anh_huong_impact(graph):
    ov = Overlay(session_id="s")
    ov.evidence["i-roi-loan-giac-ngu"] = _nho("i-roi-loan-giac-ngu", "mất ngủ")
    assert len(memory_quotes(ov, graph)) == 1


def test_KHONG_nhac_lai_loi_tu_che_manifestation(graph):
    """'mình dở quá' là lời tự phán xét — nhắc lại là đóng đinh người ta."""
    ov = Overlay(session_id="s")
    ov.evidence["m-tu-trach"] = _nho("m-tu-trach", "mình dở quá")
    assert memory_quotes(ov, graph) == []


def test_KHONG_nhac_lai_cam_xuc_affect(graph):
    ov = Overlay(session_id="s")
    ov.evidence["a-gia-tri-thap"] = _nho("a-gia-tri-thap", "mình kém cỏi")
    assert memory_quotes(ov, graph) == []


def test_KHONG_nhac_lai_node_risk_adjacent(graph):
    ov = Overlay(session_id="s")
    ov.evidence["a-vo-vong"] = _nho("a-vo-vong", "chẳng còn hy vọng")
    assert memory_quotes(ov, graph) == []


def test_chi_lay_nguon_remembered(graph):
    """Câu của CHÍNH phiên này không phải 'trí nhớ' — REFLECT lo phần đó."""
    ov = Overlay(session_id="s")
    ov.evidence["t-diem-so"] = Evidence(
        node_id="t-diem-so", confidence=0.75,
        source=EvidenceSource.SELF_REPORT, verbatim="6.5",
    )
    assert memory_quotes(ov, graph) == []


def test_khong_co_verbatim_thi_khong_liet_ke(graph):
    ov = Overlay(session_id="s")
    ov.evidence["t-diem-so"] = _nho("t-diem-so", "")
    assert memory_quotes(ov, graph) == []
