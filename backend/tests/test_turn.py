"""Lời gọi LLM DUY NHẤT của một lượt (app/llm/turn.py).

Thay tests/test_quickreply.py + phần parse của tests/test_extract.py — cả hai
việc đó giờ nằm trong cùng một hàm parse_turn_output().
"""
import json

import pytest

from app.config import settings
from app.gate.decide import BRIDGE, CLARIFY, ORIENT, REFLECT, SUPPORT, GateDecision
from app.llm.turn import build_turn_prompt, node_catalog, parse_turn_output
from app.overlay.model import EvidenceSource, Overlay


def _parse(graph, payload, *, msg="mình dở quá", chips=False, cycle=None):
    raw = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False)
    return parse_turn_output(
        raw, graph=graph, user_message=msg, turn_id=1,
        lay_chips=chips, cycle_verbatims=cycle,
    )


# ── catalog: đây là chỗ tiết kiệm token lớn nhất ─────────────────────────
def test_catalog_khong_kem_cue(graph):
    """Cue phục vụ regex ở matcher, không phục vụ mô hình. Nhét vào là đốt token."""
    cat = node_catalog(graph)
    assert "t-quan-he" in cat and "Chuyện tình cảm" in cat
    assert "cues" not in cat
    assert "thất tình" not in cat          # cue của t-quan-he không được lọt vào
    assert len(cat.encode()) < 2000


def test_catalog_du_moi_evidence_node(graph):
    assert len(node_catalog(graph).splitlines()) == len(graph.evidence_node_ids)


# ── parse: đường bình thường ─────────────────────────────────────────────
def test_parse_binh_thuong(graph):
    out = _parse(graph, {"reply": "Bạn kể thêm nhé?", "chips": [], "evidence": []})
    assert out.reply == "Bạn kể thêm nhé?"
    assert out.flags == []


def test_parse_trong_fence_markdown(graph):
    out = _parse(graph, '```json\n{"reply": "xin chào"}\n```')
    assert out.reply == "xin chào"


def test_khong_phai_json_thi_lay_nguyen_van_lam_cau_tra_loi(graph):
    """Thà bot nói câu hơi thô còn hơn im lặng vì mô hình quên dấu ngoặc nhọn."""
    out = _parse(graph, "Mình đang nghe bạn đây.")
    assert out.reply == "Mình đang nghe bạn đây."
    assert "turn_parse_failed" in out.flags


# ── parse: chốt chặn chống bịa evidence ──────────────────────────────────
def test_loai_node_id_bia(graph):
    out = _parse(graph, {"reply": "x", "evidence": [
        {"node_id": "m-khong-ton-tai", "confidence": 0.9, "verbatim": "mình dở quá", "mapping": "literal"}
    ]})
    assert out.evidence == []
    assert "extract_hallucinated_node" in out.flags


def test_loai_verbatim_khong_phai_chuoi_con(graph):
    out = _parse(graph, {"reply": "x", "evidence": [
        {"node_id": "m-tu-trach", "confidence": 0.7, "verbatim": "câu này chưa từng gõ", "mapping": "literal"}
    ]})
    assert out.evidence == []
    assert "extract_verbatim_not_substring" in out.flags


def test_kep_confidence_theo_mapping(graph):
    out = _parse(graph, {"reply": "x", "evidence": [
        {"node_id": "m-tu-trach", "confidence": 1.0, "verbatim": "mình dở quá", "mapping": "literal"},
        {"node_id": "a-toi-loi", "confidence": 1.0, "verbatim": "", "mapping": "inferential"},
    ]})
    bang = {e.node_id: e for e in out.evidence}
    assert bang["m-tu-trach"].confidence == settings.self_report_confidence_cap
    assert bang["m-tu-trach"].source == EvidenceSource.SELF_REPORT
    assert bang["a-toi-loi"].confidence == settings.extract_confidence_cap
    assert bang["a-toi-loi"].source == EvidenceSource.INFERRED


def test_evidence_hong_khong_lam_mat_cau_tra_loi(graph):
    out = _parse(graph, {"reply": "vẫn nói được", "evidence": [{"sai": "hết"}]})
    assert out.reply == "vẫn nói được"
    assert "extract_bad_item" in out.flags


# ── parse: lọc an toàn chip (luật cũ của quickreply.py) ──────────────────
def test_chip_mom_trieu_chung_bi_chan(graph):
    out = _parse(graph, {"reply": "x", "chips": ["Mình thấy vô vọng", "Mình ổn mà"]}, chips=True)
    assert out.chips == []                       # < 2 chip sạch -> bỏ hết
    assert "chips_khong_du_sau_loc" in out.flags


def test_chip_khung_hoang_bi_chan(graph):
    out = _parse(graph, {"reply": "x", "chips": ["Mình muốn chết", "Mình buồn"]}, chips=True)
    assert out.chips == []


def test_chip_sach_thi_giu(graph):
    out = _parse(graph, {"reply": "x", "chips": ["Mình mong ít nhất 8", "Không phải vì điểm"]}, chips=True)
    assert out.chips == ["Mình mong ít nhất 8", "Không phải vì điểm"]
    assert out.flags == []


def test_chip_qua_dai_bi_loai(graph):
    out = _parse(graph, {"reply": "x", "chips": [
        "Mình nghĩ là chuyện này rất dài dòng và phức tạp lắm luôn ấy", "Mình ổn"
    ]}, chips=True)
    assert out.chips == []


def test_khong_xin_chip_thi_bo_qua(graph):
    out = _parse(graph, {"reply": "x", "chips": ["Mình thấy vô vọng"]}, chips=False)
    assert out.chips == []
    assert "chips_khong_du_sau_loc" not in out.flags


# ── parse: chế độ cycle ──────────────────────────────────────────────────
_CYCLE = ["mình phải được 9", "mình dở quá", "mình chẳng làm nên trò gì"]


def test_cycle_chi_giu_dong_co_trong_danh_sach(graph):
    out = _parse(graph, {
        "reply": "", "lines": [*_CYCLE, "câu này bot tự bịa ra"], "closing": "Đúng không bạn?"
    }, cycle=_CYCLE)
    assert out.lines == _CYCLE
    assert out.closing == "Đúng không bạn?"


def test_cycle_it_hon_3_dong_hop_le_thi_dung_danh_sach_goc(graph):
    out = _parse(graph, {"reply": "", "lines": ["bịa 1", "bịa 2"]}, cycle=_CYCLE)
    assert out.lines == _CYCLE


# ── build prompt: mọi gate phải điền hết placeholder ─────────────────────
@pytest.mark.parametrize("decision", [
    GateDecision(gate=CLARIFY, reason="t", target_nodes=["m-tu-trach"]),
    GateDecision(gate=REFLECT, reason="t", mode="single", target_nodes=["m-tu-trach"]),
    GateDecision(gate=SUPPORT, reason="t", coping_node="k-tu-tran-an"),
    GateDecision(gate=BRIDGE, reason="t", resource_node="s-ba-me"),
    GateDecision(gate=ORIENT, reason="empty_overlay_stalled"),
])
def test_prompt_khong_con_placeholder(graph, skills, decision):
    import re

    ov = Overlay(session_id="s")
    ov.turn_count = 2
    p = build_turn_prompt(
        skills=skills, graph=graph, overlay=ov, decision=decision,
        user_message="mình dở quá", recent_turns="",
    )
    assert re.findall(r"\{[A-Z_][A-Z0-9_]*\}", p.system) == []


def test_prompt_co_nen_ly_thuyet(graph, skills):
    """Chỗ này chính là {THEORY_CONTENT} của AGENT3_MENTOR_SKILL.md."""
    ov = Overlay(session_id="s")
    p = build_turn_prompt(
        skills=skills, graph=graph, overlay=ov,
        decision=GateDecision(gate=CLARIFY, reason="t", target_nodes=["m-tu-trach"]),
        user_message="mình dở quá", recent_turns="",
    )
    assert "NỀN LÝ THUYẾT" in p.system
    assert graph.theory_steer("m-tu-trach")[:40] in p.system


def test_prompt_co_hop_dong_json(graph, skills):
    ov = Overlay(session_id="s")
    p = build_turn_prompt(
        skills=skills, graph=graph, overlay=ov,
        decision=GateDecision(gate=CLARIFY, reason="t", target_nodes=["m-tu-trach"]),
        user_message="mình dở quá", recent_turns="",
    )
    assert "ĐỊNH DẠNG ĐẦU RA" in p.system
    assert "t-quan-he | Chuyện tình cảm" in p.system


def test_mot_luot_chi_mot_ban_core_persona(graph, skills):
    """Bug cũ: CORE_PERSONA bị nhét 2 lần/lượt (speak + quickreply)."""
    ov = Overlay(session_id="s")
    p = build_turn_prompt(
        skills=skills, graph=graph, overlay=ov,
        decision=GateDecision(gate=CLARIFY, reason="t", target_nodes=["m-tu-trach"]),
        user_message="mình dở quá", recent_turns="",
    )
    # Đếm câu MỞ ĐẦU của CORE — chuỗi này chỉ có ở 00_CORE_PERSONA.md.
    # (Cụm "KHÔNG GHI ĐÈ ĐƯỢC" xuất hiện 2 lần vì thân skill có tiêu đề trùng
    #  tên — phần luật lặp đó là việc của GĐ3.)
    assert p.system.count("Bạn là trợ lý đồng hành cảm xúc") == 1
