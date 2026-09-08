"""
docx/11 D5–D7 + Phần E — sửa sau lần chạy thật 08/09/2026.

Lượt 1 thật ("hôm nay thi toán được 6.5 chán ghê") ra bốn lỗi độc lập:
  D5  target node chọn ngẫu nhiên theo thứ tự băm của `set`
  D6  nhãn node nội bộ ("đáng bị trách phạt") rò thẳng vào câu trả lời
  D7  chép nguyên văn bảng dáng câu hỏi, lại chọn nhầm dáng
  E   hai chip nội dung cùng một hướng → thực chất chỉ có 1 lựa chọn
"""
from __future__ import annotations

import pytest

from app.config import settings
from app.gate.decide import (
    CLARIFY, ORIENT, REFLECT, SUPPORT, BRIDGE,
    GateDecision, decide_gate, highest_information_gain_node,
)
from app.gate.directive import (
    ANH_HUONG, CHUAN_MUC, LAP_LAI, SUY_NGHI, SU_VIEC, VE_MINH, chon_dang_cau_hoi,
)
from app.graph.loader import load_graph
from app.llm.turn import parse_turn_output
from app.overlay.model import Evidence, EvidenceSource, Overlay
from app.pipeline.quick_reply import (
    CHIP_NOI_DUNG_MAX, CHIP_NOI_DUNG_MIN, build_quick_replies, ngan_sach_chip_noi_dung,
)
from app.safety import phrases
from app.safety.chips import detect_chip
from app.safety.crisis import SafetyResult
from app.safety.postcheck import find_label_leak, post_check
from app.safety.normalize import normalize_vi


@pytest.fixture(scope="module")
def graph():
    return load_graph()


def _ov(**kw) -> Overlay:
    return Overlay(session_id="s", **kw)


def _ev(nid: str, conf: float, src=EvidenceSource.SELF_REPORT, vb: str = "x") -> Evidence:
    return Evidence(node_id=nid, confidence=conf, source=src, turn_ids=[1], verbatim=vb)


def _nhan_phan_quyet(graph) -> list[str]:
    return [
        n.label
        for nid in graph.evidence_node_ids
        if (n := graph.node(nid)) and n.type in {"manifestation", "affect", "impact"}
    ]


# ═══════════════════════════════════════════════════════════════════════
# D5 — chọn TARGET phải TẤT ĐỊNH và không nhắm node kết luận nặng quá sớm
# ═══════════════════════════════════════════════════════════════════════
def test_d5_target_tat_dinh_va_dung_node(graph):
    """Lượt 1 chỉ có t-diem-so: cả 4 hàng xóm cùng điểm information gain.

    Bản cũ trả về theo thứ tự duyệt `set` → đổi theo PYTHONHASHSEED. Bản mới
    phải ra cùng một node, và phải là node ĐIỀU KIỆN (m-tieu-chuan-cao chạy VÀO
    t-diem-so) chứ không phải node HỆ QUẢ.
    """
    ov = _ov()
    ov.evidence["t-diem-so"] = _ev("t-diem-so", 0.75, vb="thi toán được 6.5")
    ket_qua = {highest_information_gain_node(graph, ov) for _ in range(50)}
    assert ket_qua == {"m-tieu-chuan-cao"}


def test_d5_late_stage_bi_chan_khi_overlay_con_mong(graph):
    """m-dang-bi-trach-phat là hàng xóm của t-diem-so nhưng bị khoá ở lượt 1."""
    assert graph.node("m-dang-bi-trach-phat").late_stage is True
    ov = _ov()
    ov.evidence["t-diem-so"] = _ev("t-diem-so", 0.75)
    assert highest_information_gain_node(graph, ov) != "m-dang-bi-trach-phat"

    # Đủ 3 node thì mở khoá — nhưng chỉ khi nó thắng về information gain.
    ov.evidence["m-tieu-chuan-cao"] = _ev("m-tieu-chuan-cao", 0.75)
    ov.evidence["m-chi-nho-loi-sai"] = _ev("m-chi-nho-loi-sai", 0.75)
    from app.gate.decide import _hop_le_lam_target
    assert _hop_le_lam_target(graph, ov, "m-dang-bi-trach-phat") is True


# ═══════════════════════════════════════════════════════════════════════
# D6 — nhãn node nội bộ không được lọt vào câu trả lời
# ═══════════════════════════════════════════════════════════════════════
def test_d6_bat_dung_cau_da_chay_that(graph):
    nhan = _nhan_phan_quyet(graph)
    that = (
        '6.5 mà bạn nói "chán ghê" — nghe như bạn đang thấy mình đáng bị trách '
        "phạt. Lúc nghĩ tới chuyện đó, bạn thấy mình là người thế nào?"
    )
    r = post_check(that, CLARIFY, node_labels=nhan)
    assert r.label_leak == "dang bi trach"
    assert "postcheck_node_label_leak" in r.flags
    assert r.text == phrases.SAFE_REPLACEMENT_LABEL_LEAK
    # Câu thay thế phải VẪN LÀ một lượt CLARIFY hợp lệ: có câu hỏi, không chẩn đoán.
    assert r.text.endswith("?")
    assert find_label_leak(normalize_vi(r.text), nhan) is None


@pytest.mark.parametrize("cau", [
    '6.5 mà bạn nói "chán ghê" — nghe như bạn đã mong một con số khác. Bạn kỳ vọng mình được bao nhiêu?',
    "Nghe như chuyện vừa xảy ra thôi. Chuyện gì đã xảy ra vậy bạn?",
    "Ừ, nói thì dễ thật. Chỗ nào là chỗ khó nhất khi bạn định làm?",
    "Cách bạn nói về mình lúc nãy khá nặng nề. Lúc đó bạn nghĩ gì?",
    "Nghe như con số đó với bạn không chỉ là điểm số. Lúc mở bài ra thấy 6.5, trong đầu bạn nghĩ gì về mình?",
    "Bạn kể thêm về chuyện tình cảm đó được không?",
])
def test_d6_khong_duong_tinh_gia(graph, cau):
    """Nhãn TRIGGER là chữ thường ngày — bot nói ra hoàn toàn bình thường."""
    r = post_check(cau, CLARIFY, node_labels=_nhan_phan_quyet(graph))
    assert r.label_leak is None, f"chặn nhầm câu hợp lệ: {r.label_leak}"


def test_d6_bat_cum_con_khong_chi_ca_nhan(graph):
    nhan = _nhan_phan_quyet(graph)
    assert find_label_leak(normalize_vi("Có vẻ bạn cảm thấy chưa đủ tốt."), nhan) == "chua du tot"
    assert find_label_leak(normalize_vi("Bạn đang khó tha thứ cho bản thân."), nhan) == "kho tha thu"


# ═══════════════════════════════════════════════════════════════════════
# D7 — dáng câu hỏi do CODE chọn, dáng "VỀ MÌNH" bị khoá
# ═══════════════════════════════════════════════════════════════════════
def test_d7_dang_theo_kieu_node_dang_nham(graph):
    """Dáng phải KHỚP với node đang nhắm — nếu không, directive nói hai điều
    đánh nhau và mô hình đi mò sự việc mãi (lỗi thật 08/09/2026)."""
    ov = _ov()
    ov.evidence["t-diem-so"] = _ev("t-diem-so", 0.75)
    ov.evidence["m-chua-du-tot"] = _ev("m-chua-du-tot", 0.55, EvidenceSource.INFERRED, vb="")

    # target = node đặt chuẩn mực -> hỏi "bao nhiêu thì đủ", đúng kịch bản lượt 1
    assert chon_dang_cau_hoi(graph, ov, "chán ghê", "m-tieu-chuan-cao")[0] == CHUAN_MUC
    assert chon_dang_cau_hoi(graph, ov, "chán ghê", "m-tu-trach")[0] == VE_MINH
    assert chon_dang_cau_hoi(graph, ov, "chán ghê", "a-lo-lang")[0] == SUY_NGHI
    assert chon_dang_cau_hoi(graph, ov, "chán ghê", "i-kho-tap-trung")[0] == ANH_HUONG
    assert chon_dang_cau_hoi(graph, ov, "chán ghê", "t-gia-dinh")[0] == SU_VIEC
    assert chon_dang_cau_hoi(graph, ov, "chán ghê", None)[0] == SU_VIEC


def test_d7_hoi_ve_node_inferred_duoc_phep(graph):
    """docx/03 §2 — việc DUY NHẤT `INFERRED` được dùng là chọn câu hỏi tiếp
    theo. Bản đầu khoá luôn cả việc HỎI, cắt đứt đúng đường
    INFERRED -> SELF_REPORT mà plan mô tả."""
    ov = _ov()
    ov.evidence["t-diem-so"] = _ev("t-diem-so", 0.75)
    ov.evidence["m-chua-du-tot"] = _ev("m-chua-du-tot", 0.55, EvidenceSource.INFERRED, vb="")
    assert chon_dang_cau_hoi(graph, ov, "mình không làm được như mình muốn", "m-chua-du-tot")[0] == VE_MINH


def test_d7_chua_co_gi_thi_khong_hoi_vao_con_nguoi(graph):
    ov = _ov()
    ov.evidence["t-diem-so"] = _ev("t-diem-so", 0.75)
    assert chon_dang_cau_hoi(graph, ov, "chán ghê", "m-tu-trach")[0] == SU_VIEC


def test_d7_dang_lap_lai_khi_ho_noi_hay_thay_vay(graph):
    ov = _ov()
    ov.evidence["t-diem-so"] = _ev("t-diem-so", 0.75)
    assert chon_dang_cau_hoi(graph, ov, "mình hay thấy vậy trong học tập", "t-gia-dinh")[0] == LAP_LAI


def test_d7_khong_lap_dang_hai_luot_lien(graph):
    """Đây là thứ đã hỏng: 5 lượt liền cùng một kiểu câu."""
    ov = _ov()
    ov.evidence["t-diem-so"] = _ev("t-diem-so", 0.75)
    ov.dang_da_dung = [SU_VIEC]
    khoa, _ = chon_dang_cau_hoi(graph, ov, "mình không làm được như mình muốn", None)
    assert khoa != SU_VIEC


def test_d7_dang_di_vao_directive(graph):
    from app.gate.directive import build_directive
    ov = _ov()
    ov.evidence["t-diem-so"] = _ev("t-diem-so", 0.75)
    d = build_directive(
        graph, ov,
        GateDecision(gate=CLARIFY, reason="default", target_nodes=["m-tieu-chuan-cao"]),
        user_message="hôm nay thi toán được 6.5 chán ghê",
    )
    assert "Dáng câu hỏi lượt này" in d
    assert "MỨC họ đặt ra cho bản thân" in d, "dáng phải khớp target m-tieu-chuan-cao"


# ═══════════════════════════════════════════════════════════════════════
# E3 — ngân sách chip: rộng khi mở, hẹp khi nặng
# ═══════════════════════════════════════════════════════════════════════
def test_e3_overlay_rong_luot_dau_thi_rong_cua(graph):
    ov = _ov(turn_count=1)
    assert ngan_sach_chip_noi_dung(graph, ov, "chán ghê") == CHIP_NOI_DUNG_MAX


def test_e3_mac_dinh_la_ba(graph):
    ov = _ov(turn_count=3)
    ov.evidence["t-diem-so"] = _ev("t-diem-so", 0.75)
    assert ngan_sach_chip_noi_dung(graph, ov, "mình lo lắm") == 3


def test_e3_hai_trigger_sang_thi_rong_cua(graph):
    ov = _ov(turn_count=3)
    ov.evidence["t-diem-so"] = _ev("t-diem-so", 0.75)
    ov.evidence["t-gia-dinh"] = _ev("t-gia-dinh", 0.75)
    assert ngan_sach_chip_noi_dung(graph, ov, "mệt quá") == CHIP_NOI_DUNG_MAX


def test_e3_riskflag_thi_thu_hep(graph):
    ov = _ov(turn_count=3)
    ov.evidence["t-diem-so"] = _ev("t-diem-so", 0.75)
    ov.evidence["r-keo-dai"] = _ev("r-keo-dai", 0.9)
    assert ngan_sach_chip_noi_dung(graph, ov, "mệt quá") == CHIP_NOI_DUNG_MIN


def test_e3_vua_phan_doi_loi_khuyen_thi_thu_hep(graph):
    ov = _ov(turn_count=5, gates_used=[REFLECT, SUPPORT])
    ov.evidence["t-diem-so"] = _ev("t-diem-so", 0.75)
    assert ngan_sach_chip_noi_dung(graph, ov, "nói thì dễ chứ mình có làm được đâu") == CHIP_NOI_DUNG_MIN
    # Cùng câu đó nhưng lượt trước KHÔNG phải SUPPORT/BRIDGE thì không thu hẹp.
    ov2 = _ov(turn_count=5, gates_used=[CLARIFY])
    ov2.evidence["t-diem-so"] = _ev("t-diem-so", 0.75)
    assert ngan_sach_chip_noi_dung(graph, ov2, "nói thì dễ chứ mình có làm được đâu") == 3


def test_e3_tin_nhan_dai_thi_thu_hep(graph):
    ov = _ov(turn_count=3)
    ov.evidence["t-diem-so"] = _ev("t-diem-so", 0.75)
    dai = " ".join(["mình"] * 30)
    assert ngan_sach_chip_noi_dung(graph, ov, dai) == CHIP_NOI_DUNG_MIN


# ═══════════════════════════════════════════════════════════════════════
# E4 — số chip theo gate, luôn nằm trong 3..5 (trừ ESCALATE và REFLECT)
# ═══════════════════════════════════════════════════════════════════════
def test_e4_escalate_khong_chip(graph):
    chips, prov = build_quick_replies(graph, _ov(), GateDecision(gate="ESCALATE", reason="x"))
    assert chips == [] and prov == []


def test_e4_reflect_don_hai_chip_cycle_ba_chip(graph):
    d = GateDecision(gate=REFLECT, reason="x", mode="single", target_nodes=["m-tu-trach"])
    assert len(build_quick_replies(graph, _ov(), d)[0]) == 2
    d2 = GateDecision(gate=REFLECT, reason="x", mode="cycle", target_nodes=["cycle-tu-phe-phan"])
    chips, _ = build_quick_replies(graph, _ov(), d2, so_dong_the=4)
    assert chips == ["✓ Đúng vậy", "~ Đúng một phần", "✗ Không hẳn"]


def test_e4_support_them_chip_da_thu_ve_sau(graph):
    d = GateDecision(gate=SUPPORT, reason="x", coping_node="k-tu-tran-an")
    som, _ = build_quick_replies(graph, _ov(turn_count=2), d)
    assert len(som) == 3 and "Mình thử rồi, không ăn thua" not in som
    muon, prov = build_quick_replies(graph, _ov(turn_count=5), d)
    assert len(muon) == 4 and "Mình thử rồi, không ăn thua" in muon
    assert sum(1 for p in prov if p["is_escape"]) == 1


def test_e4_bridge_them_chip_khi_nguon_la_gia_dinh(graph):
    gd = GateDecision(gate=BRIDGE, reason="keo_dai", resource_node="s-ba-me")
    chips, _ = build_quick_replies(graph, _ov(), gd)
    assert len(chips) == 4 and "Mình chưa biết mở lời sao" in chips
    truong = GateDecision(gate=BRIDGE, reason="keo_dai", resource_node="s-gvcn")
    assert len(build_quick_replies(graph, _ov(), truong)[0]) == 3


def test_e4_orient_bon_hoac_nam(graph):
    d = GateDecision(gate=ORIENT, reason="empty_overlay_stalled")
    assert len(build_quick_replies(graph, _ov(), d)[0]) == 4
    ov = _ov()
    ov.evidence["t-diem-so"] = _ev("t-diem-so", 0.75)
    chips, _ = build_quick_replies(graph, ov, GateDecision(gate=ORIENT, reason="clarify_stalled"))
    assert len(chips) == 5 and chips[-1] == "Chuyện của mình khác cơ"


def test_e4_moi_gate_dung_mot_chip_thoat(graph):
    """Chip thoát luôn đúng một cái và luôn đứng cuối — trừ REFLECT/ORIENT."""
    for d in (
        GateDecision(gate=SUPPORT, reason="x", coping_node="k-tu-tran-an"),
        GateDecision(gate=BRIDGE, reason="keo_dai", resource_node="s-ba-me"),
        GateDecision(gate=CLARIFY, reason="default", target_nodes=["m-tu-trach"]),
    ):
        chips, prov = build_quick_replies(graph, _ov(turn_count=5), d)
        assert 3 <= len(chips) <= 5, f"{d.gate}: {len(chips)} chip"
        thoat = [p for p in prov if p["is_escape"]]
        assert len(thoat) == 1 and thoat[0]["text"] == chips[-1]


# ═══════════════════════════════════════════════════════════════════════
# E5 — "Đúng một phần"
# ═══════════════════════════════════════════════════════════════════════
def test_e5_chip_partial_nhan_dien_duoc():
    sig = detect_chip("~ Đúng một phần")
    assert sig is not None and sig.chip_type == "CONFIRM_PARTIAL"
    assert sig.clean_text == "Đúng một phần"


def test_e5_khong_promote_confirmed_va_khong_mo_support(graph):
    ov = _ov(turn_count=4, gates_used=[CLARIFY, REFLECT], active_cycles=["cycle-tu-phe-phan"])
    for nid in ("m-tu-trach", "t-diem-so", "m-tieu-chuan-cao", "a-lo-lang"):
        ov.evidence[nid] = _ev(nid, 0.72)

    ov.promote_partial(["m-tu-trach", "t-diem-so"], turn_id=4)
    assert ov.confidence("m-tu-trach") == settings.partial_confirm_confidence
    assert not ov.is_confirmed("m-tu-trach"), "đúng MỘT PHẦN không phải là CONFIRMED"

    from app.safety.chips import ChipSignal
    d = decide_gate(
        graph, ov, SafetyResult(tier=None),
        ChipSignal(chip_type="CONFIRM_PARTIAL", clean_text="Đúng một phần", raw_text="~ Đúng một phần"),
    )
    assert d.gate == CLARIFY and d.reason == "chip_confirm_partial"


def test_e5_khoa_reflect_sau_partial(graph):
    """Cycle vẫn sáng ở 0.80 — không khoá thì lượt sau dựng lại y hệt cái thẻ."""
    ov = _ov(turn_count=4, gates_used=[CLARIFY, REFLECT], active_cycles=["cycle-tu-phe-phan"])
    for nid in ("m-tu-trach", "t-diem-so", "m-tieu-chuan-cao", "a-lo-lang"):
        ov.evidence[nid] = _ev(nid, 0.80)
    ov.reflect_locked_until = ov.turn_count + settings.reflect_cooldown_turns

    d = decide_gate(graph, ov, SafetyResult(tier=None), None)
    assert d.gate != REFLECT

    # Hết hạn khoá, và lượt gần nhất không phải REFLECT (D11) -> mở lại.
    ov.turn_count = ov.reflect_locked_until
    ov.gates_used = [REFLECT, CLARIFY, CLARIFY]
    assert decide_gate(graph, ov, SafetyResult(tier=None), None).gate == REFLECT


def test_e5_directive_partial_hoi_cho_lech(graph):
    from app.gate.directive import build_directive
    d = build_directive(
        graph, _ov(),
        GateDecision(gate=CLARIFY, reason="chip_confirm_partial"),
        user_message="~ Đúng một phần",
    )
    assert "một phần" in d.lower() and "chưa khớp" in d


# ═══════════════════════════════════════════════════════════════════════
# E7 — luật an toàn chip
# ═══════════════════════════════════════════════════════════════════════
def _parse(graph, chips, toi_da=4):
    return parse_turn_output(
        {"reply": "x", "chips": chips, "evidence": []}.__repr__().replace("'", '"'),
        graph=graph, user_message="mình dở quá", turn_id=1,
        lay_chips=True, chip_toi_da=toi_da,
    )


def test_e7_chan_chip_kem_coi(graph):
    """Chip đã lọt ngày 08/09/2026 — danh sách cấm cũ chỉ có 'vô dụng'."""
    out = _parse(graph, ["Mình thấy mình kém cỏi", "Mình mong ít nhất 8"])
    assert "Mình thấy mình kém cỏi" not in out.chips
    assert out.chips == [], "còn dưới 2 chip sạch thì bỏ hết, dùng chip tất định"
    assert "chips_khong_du_sau_loc" in out.flags


def test_e7_bo_dau_cham_cuoi_chip(graph):
    out = _parse(graph, ["Mình mong ít nhất 8.", "Không phải vì điểm."])
    assert out.chips == ["Mình mong ít nhất 8", "Không phải vì điểm"]


def test_e7_nhan_toi_da_theo_ngan_sach(graph):
    bon = ["Mình mong ít nhất 8", "Mình không đặt mức nào cả",
           "Không phải vì điểm", "Chuyện ở nhà mới mệt"]
    assert len(_parse(graph, bon, toi_da=4).chips) == 4
    assert len(_parse(graph, bon, toi_da=2).chips) == 2
    assert len(_parse(graph, bon, toi_da=3).chips) == 3

# ═══════════════════════════════════════════════════════════════════════
# D6 đầu-cuối — thử lại MỘT lần khi rò nhãn, rồi mới chịu câu thay thế
# ═══════════════════════════════════════════════════════════════════════
import json
import uuid

from app.overlay.store import get_store
from app.pipeline import runner as runner_mod


class _LLMGia:
    """Trả lần lượt các chuỗi đã cho; lần gọi thừa thì lặp lại chuỗi cuối."""

    def __init__(self, *dap_an: str):
        self.dap_an = list(dap_an)
        self.so_lan = 0

    async def complete(self, **_kw) -> str:
        i = min(self.so_lan, len(self.dap_an) - 1)
        self.so_lan += 1
        return self.dap_an[i]


def _json(reply: str, chips: list[str] | None = None) -> str:
    return json.dumps({"reply": reply, "chips": chips or [], "evidence": []}, ensure_ascii=False)


async def _chay(sid: str, msg: str) -> dict:
    out: dict = {"gate": None, "chips": [], "text": "", "flags": None}
    async for ev, data in runner_mod.run_chat_turn(sid, msg):
        if ev == "meta":
            out["gate"] = data["gate"]
        elif ev == "token":
            out["text"] += data["t"]
        elif ev == "footer":
            out["chips"] = data["quickReplies"]
    return out


RO_NHAN = '6.5 mà bạn nói "chán ghê" — nghe như bạn đang thấy mình đáng bị trách phạt. Bạn nghĩ gì?'
SACH = '6.5 mà bạn nói "chán ghê" — nghe như bạn đã mong một con số khác. Bạn kỳ vọng mình được bao nhiêu?'


@pytest.mark.asyncio
async def test_d6_thu_lai_mot_lan_roi_dung_cau_sach(monkeypatch):
    gia = _LLMGia(
        _json(RO_NHAN, ["Mình thấy mình kém cỏi", "Mình nghĩ mình chưa cố gắng"]),
        _json(SACH, ["Mình mong ít nhất 8", "Mình không đặt mức nào cả", "Không phải vì điểm"]),
    )
    monkeypatch.setattr(runner_mod, "get_llm", lambda: gia)
    sid = str(uuid.uuid4())
    await get_store().save(Overlay(session_id=sid))

    r = await _chay(sid, "hôm nay thi toán được 6.5 chán ghê")
    assert gia.so_lan == 2, "phải gọi lại đúng một lần"
    assert "đáng bị trách phạt" not in r["text"]
    assert r["text"] == SACH
    # Chip của lượt thử lại được dùng, và chip bẩn của lượt đầu bị vứt.
    assert "Mình thấy mình kém cỏi" not in r["chips"]
    assert 3 <= len(r["chips"]) <= 5
    assert r["chips"][-1].startswith(phrases.CHIP_DECLINE)


@pytest.mark.asyncio
async def test_d6_thu_lai_van_ro_thi_dung_cau_thay_the(monkeypatch):
    gia = _LLMGia(_json(RO_NHAN), _json(RO_NHAN))
    monkeypatch.setattr(runner_mod, "get_llm", lambda: gia)
    sid = str(uuid.uuid4())
    await get_store().save(Overlay(session_id=sid))

    r = await _chay(sid, "hôm nay thi toán được 6.5 chán ghê")
    assert r["text"] == phrases.SAFE_REPLACEMENT_LABEL_LEAK
    assert "đáng bị trách phạt" not in r["text"]
    # Vẫn phải còn chip để họ đi tiếp — rơi về chip tất định.
    assert len(r["chips"]) == 3 and r["chips"][-1].startswith(phrases.CHIP_DECLINE)
