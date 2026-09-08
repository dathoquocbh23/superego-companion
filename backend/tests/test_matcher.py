"""Bộ trích bằng chứng TẤT ĐỊNH (app/evidence/matcher.py). Thay tests/test_extract.py.

Ca hồi quy quan trọng nhất nằm ở test_bat_duoc_hai_cau_da_lam_hong_demo():
hai câu đó là hai câu THẬT trong ảnh chụp 07/09/2026, lúc đó trích ra RỖNG nên
gate kẹt ở CLARIFY 4 lượt liền.
"""
from app.evidence.matcher import match_evidence


def _ids(graph, msg):
    return {e.node_id for e in match_evidence(graph, msg, 1)}


# ── hồi quy: đúng hai câu đã làm hỏng demo ────────────────────────────────
def test_bat_duoc_hai_cau_da_lam_hong_demo(graph):
    assert "t-quan-he" in _ids(graph, "Mình thất tình rồi huhu")
    assert "a-buon" in _ids(graph, "Mình đang rất buồn")


def test_van_bat_duoc_ca_hoc_tap_cu(graph):
    got = _ids(graph, "thi toán được 6.5 chán ghê, mình dở quá")
    assert "t-diem-so" in got
    assert "m-tu-trach" in got


# ── luật khớp ────────────────────────────────────────────────────────────
def test_khong_khop_thi_tra_rong(graph):
    assert match_evidence(graph, "hôm nay trời đẹp ghê", 1) == []
    assert match_evidence(graph, "", 1) == []


def test_khop_theo_bien_tu_khong_phai_substring(graph):
    """`tức` nằm trong `lập tức` KHÔNG được tính là tức giận.

    Đây là lý do mọi cue của tầng đời sống đều là cụm nhiều chữ.
    """
    assert "a-tuc-gian" not in _ids(graph, "mình làm ngay lập tức luôn")


def test_moi_node_chi_ra_mot_evidence(graph):
    ev = match_evidence(graph, "mình cãi nhau với bạn, giờ không ai chơi với mình", 1)
    assert len(ev) == len({e.node_id for e in ev})


def test_cue_dac_hieu_nhat_thang(graph):
    """Node có nhiều cue khớp thì cue DÀI NHẤT quyết định confidence."""
    ev = next(
        e for e in match_evidence(graph, "giờ không ai chơi với mình nữa", 1)
        if e.node_id == "t-ban-be"
    )
    assert ev.confidence == 0.75          # cue 4 chữ, không phải cue ngắn hơn


def test_verbatim_la_ca_menh_de_khong_phai_mau_cue(graph):
    """docx/11 D12 — verbatim đi thẳng lên INSIGHT_CARD.

    Cue "bài kiểm tra" từng cho ra một dòng thẻ đúng hai chữ, nằm giữa hai dòng
    tử tế. Cả điểm nhấn của thẻ là "đây đúng là lời bạn nói" — một mẩu cue phá
    đúng chỗ đó. Verbatim vẫn TUYỆT ĐỐI là chữ họ gõ, chỉ lấy trọn mệnh đề.
    """
    ev = next(
        e for e in match_evidence(graph, "Mình vừa bị điểm kém một bài kiểm tra", 1)
        if e.node_id == "t-diem-so"
    )
    assert ev.verbatim == "Mình vừa bị điểm kém một bài kiểm tra"


def test_verbatim_cat_o_ranh_gioi_menh_de(graph):
    ev = {e.node_id: e.verbatim for e in match_evidence(
        graph, "Ít nhất phải được top, không thì mình lo quá", 1)}
    assert ev["m-tieu-chuan-cao"] == "Ít nhất phải được top"
    assert ev["a-lo-lang"] == "không thì mình lo quá"


def test_verbatim_khong_cat_giua_so_thap_phan(graph):
    """"6.5" là một con số — cắt ở dấu chấm thì thành "thi được 6"."""
    ev = next(
        e for e in match_evidence(graph, "Hôm nay thi được 6.5, mình dở quá", 1)
        if e.node_id == "t-diem-so"
    )
    assert ev.verbatim == "Hôm nay thi được 6.5"


def test_verbatim_qua_dai_thi_lui_ve_cue(graph):
    """Một câu dài không được nuốt trọn cả thẻ."""
    dai = "hôm qua mình đi học về rồi ngồi nghĩ mãi về chuyện bài kiểm tra toán tuần trước mà không tài nào ngủ được"
    ev = [e for e in match_evidence(graph, dai, 1) if e.node_id == "t-diem-so"]
    if ev:
        assert len(ev[0].verbatim.split()) <= 12


# ── confidence theo độ đặc hiệu ──────────────────────────────────────────
def test_cue_mot_chu_duoi_nguong_reflect(graph):
    """Cue 1 CHỮ vào overlay được, nhưng MỘT MÌNH nó không đủ kích REFLECT.

    "điểm" là cue một chữ của t-diem-so: nhắc tới điểm số chưa nói lên điều gì
    về cách người ta tự nhìn mình. Cần thêm bằng chứng đặc hiệu hơn.
    """
    from app.config import settings

    ev = next(e for e in match_evidence(graph, "hôm nay trả điểm rồi", 1) if e.node_id == "t-diem-so")
    assert ev.confidence < settings.confidence_threshold


def test_cue_hai_chu_dat_nguong(graph):
    from app.config import settings

    ev = next(e for e in match_evidence(graph, "mình thấy cô đơn", 1) if e.node_id == "a-co-don")
    assert ev.confidence >= settings.confidence_threshold


def test_cue_dai_dat_tran_self_report(graph):
    from app.config import settings

    ev = next(
        e for e in match_evidence(graph, "mình không biết nói với ai cả", 1)
        if e.node_id == "a-co-don"
    )
    assert ev.confidence == settings.self_report_confidence_cap


# ── verbatim ─────────────────────────────────────────────────────────────
def test_verbatim_luon_la_chuoi_con_cua_tin_nhan(graph):
    msg = "Mình thất tình rồi huhu"
    for e in match_evidence(graph, msg, 1):
        assert e.verbatim == "" or e.verbatim in msg


def test_go_khong_dau_van_khop_nhung_khong_bia_verbatim(graph):
    """Khớp được ở tầng chuẩn hoá, nhưng KHÔNG chế ra chuỗi có dấu họ chưa gõ."""
    ev = match_evidence(graph, "minh that tinh roi", 1)
    assert {e.node_id for e in ev} == {"t-quan-he"}
    assert ev[0].verbatim == ""


def test_source_luon_la_self_report(graph):
    from app.overlay.model import EvidenceSource

    for e in match_evidence(graph, "mình rất buồn và hay tự trách", 1):
        assert e.source == EvidenceSource.SELF_REPORT
