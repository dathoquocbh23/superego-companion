"""Gate ORIENT — van chống giậm chân (GĐ4, 07/09/2026).

Lỗi gốc: 07/09/2026 quan sát 4 lượt CLARIFY liên tiếp với overlay RỖNG suốt.
Hệ thống không có cách nào tự biết mình đang chạy không tải, nên cứ hỏi mãi
một câu mở vô đích. ORIENT là chốt chặn để chuyện đó không lặp lại.
"""
import re

import pytest

from app.gate.decide import (
    CLARIFY, ORIENT, REFLECT, STALL_LIMIT, GateDecision, decide_gate,
)
from app.evidence.matcher import match_evidence
from app.llm.turn import build_turn_prompt
from app.overlay.model import Overlay
from app.pipeline.quick_reply import build_quick_replies
from app.safety.crisis import check_crisis


def _gate(graph, overlay):
    return decide_gate(graph, overlay, check_crisis(""), None)


# ── kiểu (a): overlay rỗng qua nhiều lượt ────────────────────────────────
def test_luot_dau_van_hoi_binh_thuong(graph):
    """Lượt 1 chưa được kết luận là bế tắc — mới hỏi một câu thôi mà."""
    ov = Overlay(session_id="s")
    ov.turn_count = 1
    assert _gate(graph, ov).gate == CLARIFY


def test_overlay_rong_sang_luot_2_thi_dinh_huong_lai(graph):
    ov = Overlay(session_id="s")
    ov.turn_count = 2
    ov.gates_used = [CLARIFY]
    assert _gate(graph, ov).gate == ORIENT


def test_khong_dua_thuc_don_hai_luot_lien(graph):
    """ORIENT xong mà vẫn rỗng thì quay lại CLARIFY, không lặp thực đơn."""
    ov = Overlay(session_id="s")
    ov.turn_count = 3
    ov.gates_used = [CLARIFY, ORIENT]
    assert _gate(graph, ov).gate == CLARIFY


# ── kiểu (b): có evidence nhưng không lớn thêm ───────────────────────────
def test_ket_o_clarify_khong_thu_them_duoc_gi(graph):
    ov = Overlay(session_id="s")
    ov.turn_count = 6
    for e in match_evidence(graph, "mình thấy cô đơn", 1):
        ov.merge(e)
    ov.gates_used = [CLARIFY] * STALL_LIMIT
    ov.stall_streak = STALL_LIMIT
    assert _gate(graph, ov).gate == ORIENT


def test_dang_tien_trien_thi_de_yen(graph):
    """stall_streak cao nhưng gate gần đây KHÔNG phải CLARIFY → không cắt ngang.

    Hội thoại đi REFLECT → SUPPORT cũng không tăng evidence, nhưng nó đang chạy
    đúng thiết kế. Cắt ngang bằng thực đơn chủ đề là phá hỏng đúng lúc tốt nhất.
    """
    ov = Overlay(session_id="s")
    ov.turn_count = 6
    for e in match_evidence(graph, "mình thấy cô đơn", 1):
        ov.merge(e)
    ov.gates_used = [CLARIFY, REFLECT, CLARIFY]
    ov.stall_streak = 9
    assert _gate(graph, ov).gate != ORIENT


def test_chua_du_so_luot_ket_thi_chua_cat(graph):
    ov = Overlay(session_id="s")
    ov.turn_count = 4
    for e in match_evidence(graph, "mình thấy cô đơn", 1):
        ov.merge(e)
    ov.gates_used = [CLARIFY, CLARIFY]
    ov.stall_streak = 2
    assert _gate(graph, ov).gate != ORIENT


# ── chip chủ đề ─────────────────────────────────────────────────────────
def test_chip_chu_de_khong_mang_tien_to_he_thong(graph):
    """Chip ORIENT phải đi qua bước trích như tin nhắn thường.

    Mang tiền tố (✓ ✗ ? —) thì detect_chip() bắt được và runner BỎ QUA bước
    trích — người dùng chọn chủ đề xong overlay vẫn rỗng, kẹt lại đúng chỗ cũ.
    """
    from app.safety.chips import detect_chip

    chips, _ = build_quick_replies(graph, Overlay(session_id="s"),
                                   GateDecision(gate=ORIENT, reason="empty_overlay_stalled"))
    assert len(chips) == 4
    for c in chips:
        assert detect_chip(c) is None, c


def test_moi_chip_chu_de_deu_khop_duoc_mot_node(graph):
    """Chip mà không khớp cue nào thì bấm xong vẫn kẹt — vô nghĩa."""
    chips, prov = build_quick_replies(graph, Overlay(session_id="s"),
                                      GateDecision(gate=ORIENT, reason="empty_overlay_stalled"))
    for chip, p in zip(chips, prov):
        khop = {e.node_id for e in match_evidence(graph, chip, 1)}
        assert p["target_node"] in khop, f"{chip!r} -> {khop}"


def test_bam_chip_chu_de_thi_thoat_duoc_be_tac(graph):
    """Toàn cảnh: rỗng → ORIENT → bấm chip → overlay có node → CLARIFY có đích."""
    ov = Overlay(session_id="s")
    ov.turn_count = 2
    ov.gates_used = [CLARIFY]
    assert _gate(graph, ov).gate == ORIENT

    chips, _ = build_quick_replies(graph, ov, GateDecision(gate=ORIENT, reason="x"))
    ov.gates_used.append(ORIENT)
    ov.turn_count = 3
    for e in match_evidence(graph, chips[1], 3):      # "Mình có chuyện tình cảm"
        ov.merge(e)
    ov.stall_streak = 0

    d = _gate(graph, ov)
    assert d.gate == CLARIFY
    assert d.target_nodes, "phải nhắm được vào một node, không hỏi mò nữa"


# ── prompt ──────────────────────────────────────────────────────────────
def test_prompt_orient_day_du(graph, skills):
    ov = Overlay(session_id="s")
    ov.turn_count = 3
    p = build_turn_prompt(
        skills=skills, graph=graph, overlay=ov,
        decision=GateDecision(gate=ORIENT, reason="empty_overlay_stalled"),
        user_message="ừ", recent_turns="",
    )
    assert p.skill == "13_ORIENT"
    assert re.findall(r"\{[A-Z_][A-Z0-9_]*\}", p.system) == []
    assert "DỪNG hỏi" in p.system          # directive
    assert "ĐỊNH DẠNG ĐẦU RA" in p.system  # hợp đồng JSON


def test_orient_khong_xin_chip_tu_mo_hinh(graph, skills):
    """Chip là tất định. Để mô hình sinh thêm là mời nó đọc lại thực đơn."""
    ov = Overlay(session_id="s")
    p = build_turn_prompt(
        skills=skills, graph=graph, overlay=ov,
        decision=GateDecision(gate=ORIENT, reason="empty_overlay_stalled"),
        user_message="ừ", recent_turns="",
    )
    assert "để mảng rỗng" in p.system
