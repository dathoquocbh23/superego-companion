from app.config import settings
from app.gate.decide import (
    BRIDGE,
    CLARIFY,
    ESCALATE,
    REFLECT,
    SUPPORT,
    decide_gate,
    resolve_policy_edge,
)
from app.graph.cycles import active_cycles
from app.overlay.model import Evidence, EvidenceSource, Overlay
from app.safety.chips import ChipSignal
from app.safety.crisis import SafetyResult


def _ov(**kw) -> Overlay:
    return Overlay(session_id="t", **kw)


def _ev(node_id, conf, source=EvidenceSource.SELF_REPORT, vb="câu gốc"):
    return Evidence(node_id=node_id, confidence=conf, source=source, turn_ids=[1], verbatim=vb)


def test_escalate_beats_all(graph):
    ov = _ov()
    d = decide_gate(graph, ov, SafetyResult(tier=1, forces_escalate=True), None)
    assert d.gate == ESCALATE


def test_empty_overlay_is_clarify(graph):
    d = decide_gate(graph, _ov(), SafetyResult(), None)
    assert d.gate == CLARIFY
    assert d.reason == "empty_overlay"


def test_single_strong_node_does_not_reflect(graph):
    # D3 — cần >= 3 node >= 0.70 mới REFLECT chế độ đơn
    ov = _ov()
    ov.evidence["m-tu-trach"] = _ev("m-tu-trach", 0.75)
    d = decide_gate(graph, ov, SafetyResult(), None)
    assert d.gate == CLARIFY


def test_three_strong_nodes_reflect_single(graph):
    ov = _ov()
    for nid in ("m-tu-trach", "m-chua-du-tot", "m-hiem-hai-long"):
        ov.evidence[nid] = _ev(nid, 0.75)
    d = decide_gate(graph, ov, SafetyResult(), None)
    assert d.gate == REFLECT and d.mode == "single"


def test_cycle_activation_triggers_reflect_cycle(graph):
    ov = _ov()
    for nid in ("m-tieu-chuan-cao", "t-diem-so", "m-tu-trach", "a-gia-tri-thap"):
        ov.evidence[nid] = _ev(nid, 0.7)
    ov.active_cycles = active_cycles(graph, ov.confidences())
    assert ov.active_cycles == ["cycle-tu-phe-phan"]
    d = decide_gate(graph, ov, SafetyResult(), None)
    assert d.gate == REFLECT and d.mode == "cycle"


def test_no_support_before_reflect(graph):
    ov = _ov()
    ov.evidence["m-tu-trach"] = _ev("m-tu-trach", 0.95, EvidenceSource.CONFIRMED)
    # chưa từng REFLECT
    d = decide_gate(graph, ov, SafetyResult(), None)
    assert d.gate != SUPPORT


def test_support_after_reflect_with_confirmed(graph):
    ov = _ov(gates_used=["CLARIFY", "REFLECT"])
    ov.evidence["m-tu-trach"] = _ev("m-tu-trach", 0.95, EvidenceSource.CONFIRMED)
    d = decide_gate(graph, ov, SafetyResult(), None)
    assert d.gate == SUPPORT
    assert d.coping_node == "k-tu-tran-an"           # policy edge priority 30 thắng
    assert d.policy_edge_used == "m-tu-trach->k-tu-tran-an"


def test_bridge_on_two_impacts(graph):
    ov = _ov()
    for nid in ("i-roi-loan-giac-ngu", "i-mat-dong-luc", "i-ne-tranh"):
        ov.evidence[nid] = _ev(nid, 0.75)
    ov.evidence["r-suy-giam-chuc-nang"] = _ev("r-suy-giam-chuc-nang", 0.9)
    d = decide_gate(graph, ov, SafetyResult(), None)
    assert d.gate == BRIDGE
    assert d.resource_node in {"s-ba-me", "s-tu-van-hoc-duong", "s-gvcn"}


def test_bridge_only_offered_once(graph):
    ov = _ov(bridge_offered=True)
    ov.evidence["r-keo-dai"] = _ev("r-keo-dai", 0.9)
    d = decide_gate(graph, ov, SafetyResult(), None)
    assert d.gate != BRIDGE


def test_safety_tier3_forces_bridge(graph):
    d = decide_gate(graph, _ov(), SafetyResult(tier=3, forces_bridge=True), None)
    assert d.gate == BRIDGE


def test_vo_vong_confirmed_forces_bridge(graph):
    ov = _ov()
    ov.evidence["a-vo-vong"] = _ev("a-vo-vong", 0.95, EvidenceSource.CONFIRMED)
    d = decide_gate(graph, ov, SafetyResult(), None)
    assert d.gate == BRIDGE


def test_policy_edge_condition_kappa(graph):
    # i-ne-tranh -> k-chia-nho-muc-tieu chỉ áp dụng khi có m-dang-bi-trach-phat hoặc a-xau-ho
    ov = _ov()
    ov.evidence["i-ne-tranh"] = _ev("i-ne-tranh", 0.8)
    coping, _ = resolve_policy_edge(graph, ov)
    assert coping != "k-chia-nho-muc-tieu"  # điều kiện κ chưa thoả
    ov.evidence["a-xau-ho"] = _ev("a-xau-ho", 0.8)
    coping2, edge = resolve_policy_edge(graph, ov)
    assert coping2 == "k-chia-nho-muc-tieu"


def test_chip_confirm_no_returns_clarify(graph):
    chip = ChipSignal(chip_type="CONFIRM_NO", clean_text="Không hẳn", raw_text="✗ Không hẳn")
    d = decide_gate(graph, _ov(), SafetyResult(), chip)
    assert d.gate == CLARIFY
