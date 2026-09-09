"""Chế độ chủ đề — docx/13 + docx/14.

Bộ test này canh đúng những chỗ file 14 đã chỉ ra là dễ hỏng:
    A-1  chip TÌM HIỂU bị gate tưởng là hội thoại chết máy
    B-2  REFLECT ngay sau bài Likert, không có verbatim nào để phản chiếu
    C-1  chip trỏ tới resource node phải ra BRIDGE_CARD, KHÔNG set bridge_offered
"""
from app.gate.decide import (
    BRIDGE, CLARIFY, ESCALATE, ORIENT, REFLECT, SUPPORT, decide_gate,
)
from app.graph.topics import get_topics
from app.overlay.model import Evidence, EvidenceSource, Overlay
from app.pipeline.quick_reply import build_quick_replies
from app.safety import phrases
from app.safety.chips import detect_chip
from app.safety.crisis import SafetyResult


def _ov(**kw) -> Overlay:
    return Overlay(session_id="t", **kw)


def _ev(node_id, conf=0.75, source=EvidenceSource.SELF_REPORT, vb="câu gốc"):
    return Evidence(node_id=node_id, confidence=conf, source=source, turn_ids=[1], verbatim=vb)


# ── nạp + validate ────────────────────────────────────────────────────────
def test_topics_nap_duoc_va_validate(graph):
    ts = get_topics()
    assert len(ts.topics) == 4


def test_moi_chip_tro_toi_node_co_that(graph):
    """docx/03 §7 luật 11 — chip là một lời hứa, bấm vào phải có nguyên văn."""
    for t in get_topics().topics.values():
        for c in t.learn_chips:
            assert graph.node(c.serves) is not None, f"{t.id}: chip «{c.text}» → {c.serves}"


def test_ca_4_chu_de_deu_bat_va_co_noi_dung(graph):
    """Chủ đề 3 đã trích nội dung 09/09/2026 (docx/13 §7) → cả 4 chủ đề đều hiện."""
    bat = {t.id for t in get_topics().enabled()}
    assert bat == {
        "hieu-sieu-toi", "nhan-dien-hoc-sinh", "anh-huong-suc-khoe", "khi-nao-tim-ho-tro",
    }
    t3 = get_topics().get("anh-huong-suc-khoe")
    assert t3.opening == "c-suc-khoe-va-sieu-toi"
    assert graph.node(t3.opening) is not None
    # docx/13 §12 — danh sách triệu chứng KHÔNG được là chip ở bất kỳ chủ đề nào.
    cam = {"c-dau-hieu-lo-au", "c-dau-hieu-tram-cam"}
    for t in get_topics().topics.values():
        assert not ({c.serves for c in t.learn_chips} & cam), t.id
    # nhưng 2 thẻ đó vẫn là node có thật, tới được qua explained_by.
    for nid in cam:
        assert graph.node(nid) is not None
        assert any(e.type == "explained_by" and e.to == nid for e in graph.edges)


def test_chu_de_bat_thi_phai_co_opening(graph):
    for t in get_topics().enabled():
        assert t.opening, f"{t.id} bật mà không có gì để nói"


# ── mở chủ đề ─────────────────────────────────────────────────────────────
def test_mo_chu_de_phat_the_khai_niem(graph):
    ov = _ov(topic_id="hieu-sieu-toi")
    d = decide_gate(graph, ov, SafetyResult(), None)
    assert d.gate == SUPPORT
    assert d.reason == "topic_opening"
    assert d.concept_node == "c-id-ego-superego"
    assert d.coping_node is None          # → runner đặt message_type = KNOWLEDGE_CARD


def test_mo_chu_de_3_phat_the_co_che(graph):
    """Chủ đề 3: thẻ mở đầu là cơ chế siêu tôi ↔ sức khoẻ, ra KNOWLEDGE_CARD."""
    ov = _ov(topic_id="anh-huong-suc-khoe")
    d = decide_gate(graph, ov, SafetyResult(), None)
    assert d.gate == SUPPORT
    assert d.reason == "topic_opening"
    assert d.concept_node == "c-suc-khoe-va-sieu-toi"
    assert d.coping_node is None


def test_chip_tim_hieu_chu_de_3_phat_dung_node(graph):
    ov = _ov(topic_id="anh-huong-suc-khoe", topic_opened=True)
    d = decide_gate(graph, ov, SafetyResult(), _chip_learn("Trầm cảm là gì?"))
    assert d.gate == SUPPORT
    assert d.reason == "topic_learn"
    assert d.concept_node == "c-tram-cam-la-gi"


def test_chip_cac_dang_lo_au_co_va_di_kem_chip_chan_doan(graph):
    """Thêm theo yêu cầu khách (ngược docx/03 §7 luật 3). Điều kiện: chip
    c-khong-phai-chan-doan phải nằm ngay sau nó trong topics.yaml, và steer
    của thẻ phải cấm hỏi 'bạn thuộc dạng nào'."""
    t3 = get_topics().get("anh-huong-suc-khoe")
    ids = [c.serves for c in t3.learn_chips]
    assert "c-cac-dang-lo-au" in ids
    i = ids.index("c-cac-dang-lo-au")
    assert ids[i + 1] == "c-khong-phai-chan-doan"
    steer = graph.content_body("c-cac-dang-lo-au")["steer"].lower()
    assert "thuộc dạng nào" in steer and "không xác nhận" in steer
    d = decide_gate(graph, _ov(topic_id="anh-huong-suc-khoe", topic_opened=True),
                    SafetyResult(), _chip_learn("Lo âu có mấy dạng?"))
    assert d.gate == SUPPORT and d.concept_node == "c-cac-dang-lo-au"


def test_chu_de_mo_bang_bai_test_khong_phat_the(graph):
    """Chủ đề 2 mở bằng form Likert — không có lượt LLM nào ở gate."""
    ov = _ov(topic_id="nhan-dien-hoc-sinh")
    d = decide_gate(graph, ov, SafetyResult(), None)
    assert d.reason != "topic_opening"
    assert d.gate == CLARIFY


def test_khong_mo_lai_the_dau_o_luot_sau(graph):
    ov = _ov(topic_id="hieu-sieu-toi", topic_opened=True)
    d = decide_gate(graph, ov, SafetyResult(), None)
    assert d.reason != "topic_opening"


def test_chuyen_cua_hoc_sinh_thang_bai_giang(graph):
    """Đủ 3 node để phản chiếu thì REFLECT thắng thẻ mở đầu (docx/03 §5 4a)."""
    ov = _ov(topic_id="hieu-sieu-toi")
    for nid in ("m-tu-trach", "m-chua-du-tot", "m-hiem-hai-long"):
        ov.evidence[nid] = _ev(nid)
    d = decide_gate(graph, ov, SafetyResult(), None)
    assert d.gate == REFLECT


# ── chip TÌM HIỂU ─────────────────────────────────────────────────────────
def _chip_learn(text):
    return detect_chip(phrases.CHIP_LEARN + text)


def test_chip_tim_hieu_phat_dung_node_da_hua(graph):
    ov = _ov(topic_id="hieu-sieu-toi", topic_opened=True)
    d = decide_gate(graph, ov, SafetyResult(), _chip_learn("Vậy mình có đang bị gì không?"))
    assert d.gate == SUPPORT
    assert d.reason == "topic_learn"
    assert d.concept_node == "c-khong-phai-chan-doan"


def test_chip_tim_hieu_khong_bi_reflect_nuot_mat(graph):
    """docx/13 §5.5 — chip xử ở §0b, nếu để rơi xuống thì REFLECT thắng."""
    ov = _ov(topic_id="hieu-sieu-toi", topic_opened=True)
    for nid in ("m-tu-trach", "m-chua-du-tot", "m-hiem-hai-long"):
        ov.evidence[nid] = _ev(nid)
    d = decide_gate(graph, ov, SafetyResult(), _chip_learn("Vậy mình có đang bị gì không?"))
    assert d.reason == "topic_learn"


def test_chip_la_thi_khong_bia_the(graph):
    ov = _ov(topic_id="hieu-sieu-toi", topic_opened=True)
    d = decide_gate(graph, ov, SafetyResult(), _chip_learn("Câu này không có trong topics.yaml"))
    assert d.gate == CLARIFY
    assert d.reason == "topic_learn_khong_ro"


def test_chip_tim_hieu_van_thua_an_toan(graph):
    """Chọn chủ đề không tắt tầng khủng hoảng — docx/03 §4.1b luật 2."""
    ov = _ov(topic_id="hieu-sieu-toi", topic_opened=True)
    d = decide_gate(
        graph, ov,
        SafetyResult(tier=1, forces_escalate=True),
        _chip_learn("Vậy mình có đang bị gì không?"),
    )
    assert d.gate == ESCALATE


# ── C-1: chip trỏ tới nguồn hỗ trợ ────────────────────────────────────────
def test_chip_nguon_ho_tro_ra_the_bridge(graph):
    ov = _ov(topic_id="khi-nao-tim-ho-tro", topic_opened=True)
    d = decide_gate(graph, ov, SafetyResult(), _chip_learn("Nói với ba mẹ thì mở lời sao?"))
    assert d.gate == BRIDGE
    assert d.resource_node == "s-ba-me"
    # runner chỉ set bridge_offered khi reason != "topic_learn" — người dùng tự
    # bấm đọc thử KHÔNG phải là hệ thống đã bắc cầu cho họ.
    assert d.reason == "topic_learn"


def test_chip_ky_nang_ra_the_coping(graph):
    ov = _ov(topic_id="khi-nao-tim-ho-tro", topic_opened=True)
    d = decide_gate(graph, ov, SafetyResult(), _chip_learn("Mình có thể tự làm gì ở nhà không?"))
    assert d.gate == SUPPORT
    assert d.coping_node == "k-tu-tran-an"


def test_chip_ngung_tu_huy_hoai_va_xa_stress(graph):
    """docx CÁC CÁCH KHẮC PHỤC TẠI NHÀ — 2 mục lớn thành chip (yêu cầu khách 09/09)."""
    ov = _ov(topic_id="khi-nao-tim-ho-tro", topic_opened=True)
    for text, node in [
        ("Làm sao ngừng tự hủy hoại bản thân?", "k-ngung-tu-huy-hoai"),
        ("Vì sao mình cứ tự phá như vậy?", "k-nguyen-nhan-goc-re"),
        ("Cách xả stress hiệu quả?", "k-xa-stress-nhanh"),
    ]:
        d = decide_gate(graph, ov, SafetyResult(), _chip_learn(text))
        assert d.gate == SUPPORT and d.coping_node == node, text
    # thẻ tổng quan phải gộp ĐỦ 6 chiến lược (feedback customer 09/09)
    body = graph.content_body("k-ngung-tu-huy-hoai")["body"]
    for n in ("1.", "2.", "3.", "4.", "5.", "6."):
        assert n in body, n
    # giữ nguyên từ của docx, không làm nhẹ thành "tự cản trở"
    assert "tự hủy hoại bản thân" in body.lower()
    assert graph.content_body("k-ngung-tu-huy-hoai")["title"] == "Cách ngừng tự hủy hoại bản thân"

    # xả stress: đủ 18 mục, giữ chữ "hiệu quả" trong tiêu đề, bỏ tên bệnh viện
    stress = graph.content_body("k-xa-stress-nhanh")
    assert "hiệu quả" in stress["title"]
    for n in ("1.", "9.", "13.", "18."):
        assert n in stress["body"], n
    assert "Tâm Anh" not in stress["body"] and "Bệnh viện" not in stress["body"]


# ── A-1: chế độ TÌM HIỂU không phải là giậm chân ──────────────────────────
def test_hai_luot_tim_hieu_khong_bi_coi_la_giam_chan(graph):
    """docx/14 ⚠️ A-1 — không trừ luot_tim_hieu thì lượt 2 đã bắn ORIENT."""
    ov = _ov(topic_id="hieu-sieu-toi", topic_opened=True, turn_count=3, luot_tim_hieu=2)
    d = decide_gate(graph, ov, SafetyResult(), None)
    assert d.gate == CLARIFY, "bot xin lỗi 'hỏi lòng vòng' giữa lúc đang đọc bình thường"


def test_giam_chan_that_van_bat_duoc(graph):
    """Không trừ nhầm: 3 lượt thật mà overlay vẫn rỗng thì vẫn phải ORIENT."""
    ov = _ov(turn_count=3, luot_tim_hieu=0)
    d = decide_gate(graph, ov, SafetyResult(), None)
    assert d.gate == ORIENT


# ── B-2: chỉ có bằng chứng Likert thì chưa phản chiếu ─────────────────────
def test_chi_co_likert_thi_khong_reflect(graph):
    """docx/03 §3.2 — evidence LIKERT có verbatim rỗng, không có gì để đọc lại."""
    ov = _ov()
    for nid in ("m-tu-trach", "m-chua-du-tot", "m-hiem-hai-long"):
        ov.evidence[nid] = _ev(nid, 0.80, EvidenceSource.LIKERT, vb="")
    d = decide_gate(graph, ov, SafetyResult(), None)
    assert d.gate == CLARIFY


def test_mot_cau_noi_that_la_du_de_reflect(graph):
    """Chỉ cần MỘT node do họ tự nói là phản chiếu lại được."""
    ov = _ov()
    for nid in ("m-tu-trach", "m-chua-du-tot"):
        ov.evidence[nid] = _ev(nid, 0.80, EvidenceSource.LIKERT, vb="")
    ov.evidence["m-hiem-hai-long"] = _ev("m-hiem-hai-long", 0.75)
    d = decide_gate(graph, ov, SafetyResult(), None)
    assert d.gate == REFLECT


def test_likert_muc_4_khong_vao_duoc_overlay(graph):
    """docx/03 §3.1 — 0.65 < ngưỡng 0.70. Tick 'Khá đúng' 10 câu vẫn là CLARIFY."""
    ov = _ov()
    for nid in ("m-tu-trach", "m-chua-du-tot", "m-hiem-hai-long"):
        ov.evidence[nid] = _ev(nid, 0.65, EvidenceSource.LIKERT, vb="")
    d = decide_gate(graph, ov, SafetyResult(), None)
    assert d.gate == CLARIFY


# ── chip của chế độ chủ đề ────────────────────────────────────────────────
def test_chip_chu_de_du_ba_vai(graph):
    ov = _ov(topic_id="hieu-sieu-toi")
    d = decide_gate(graph, ov, SafetyResult(), None)
    chips, prov = build_quick_replies(graph, ov, d)

    tim_hieu = [c for c in chips if c.startswith(phrases.CHIP_LEARN)]
    thoat = [c for c in chips if c.startswith(phrases.CHIP_DECLINE)]
    bac_cau = [c for c in chips if not any(c.startswith(p) for p in phrases.CHIP_PREFIXES)]

    assert tim_hieu, "thiếu chip TÌM HIỂU"
    assert len(thoat) == 1, "luôn đúng MỘT chip thoát (docx/03 §7 luật 4)"
    assert len(bac_cau) == 1, "thiếu chip bắc cầu sang chuyện cá nhân"
    assert len(chips) <= 5


def test_chip_bac_cau_khong_mang_tien_to(graph):
    """docx/03 §7 luật 12 — chip bắc cầu phải đi qua bước trích như tin thường."""
    ov = _ov(topic_id="hieu-sieu-toi")
    d = decide_gate(graph, ov, SafetyResult(), None)
    chips, _ = build_quick_replies(graph, ov, d)
    bac_cau = get_topics().get("hieu-sieu-toi").bridge_chip
    assert bac_cau in chips
    assert detect_chip(bac_cau) is None


def test_khong_bay_lai_chip_vua_mo_ra_the(graph):
    ov = _ov(topic_id="hieu-sieu-toi", topic_opened=True)
    d = decide_gate(graph, ov, SafetyResult(), _chip_learn("Vậy mình có đang bị gì không?"))
    chips, _ = build_quick_replies(graph, ov, d)
    assert not any("có đang bị gì không" in c for c in chips)


# ── xoay chip TÌM HIỂU (09/09/2026) ───────────────────────────────────────
def _chips_tim_hieu(graph, ov, d):
    chips, _ = build_quick_replies(graph, ov, d)
    return [c[len(phrases.CHIP_LEARN):] for c in chips if c.startswith(phrases.CHIP_LEARN)]


def test_chu_de_1_co_du_sau_chip(graph):
    """6 mục lý thuyết của docx siêu tôi đều có chip (mục 2 là thẻ mở đầu)."""
    assert len(get_topics().get("hieu-sieu-toi").learn_chips) == 6


def test_chip_da_doc_tut_xuong_cuoi(graph):
    ov = _ov(topic_id="hieu-sieu-toi")
    d = decide_gate(graph, ov, SafetyResult(), None)
    dau = _chips_tim_hieu(graph, ov, d)

    # Đọc xong 2 thẻ đầu → lượt sau chúng nhường chỗ cho thẻ chưa đọc.
    ov.the_da_xem = ["c-sieu-toi-la-gi", "c-sieu-toi-trung-phat-la-gi"]
    sau = _chips_tim_hieu(graph, ov, d)

    assert dau[:2] == ["Cái siêu tôi là gì?", 'Còn "siêu tôi trừng phạt" là gì?']
    assert "Cái siêu tôi là gì?" not in sau
    assert 'Còn "siêu tôi trừng phạt" là gì?' not in sau


def test_doc_het_mot_vong_gap_du_moi_muc_ly_thuyet(graph):
    """Bấm mãi thì mọi mục lý thuyết của chủ đề đều tới lượt được bày ra."""
    topic = get_topics().get("hieu-sieu-toi")
    ov = _ov(topic_id="hieu-sieu-toi")
    d = decide_gate(graph, ov, SafetyResult(), None)
    da_gap: set[str] = set()

    for _ in range(len(topic.learn_chips) + 2):
        hien = _chips_tim_hieu(graph, ov, d)
        if not hien:
            break
        da_gap.update(hien)
        # giả lập: bấm chip đầu tiên -> thẻ đó vào danh sách đã xem
        dau = next(c for c in topic.learn_chips if c.text == hien[0])
        ov.the_da_xem.append(dau.serves)

    assert da_gap == {c.text for c in topic.learn_chips}


def test_xoay_chip_la_tat_dinh(graph):
    """Cùng trạng thái -> cùng bộ chip. Random thì test và kịch bản docx/14 vô nghĩa."""
    ov = _ov(topic_id="hieu-sieu-toi", the_da_xem=["c-sieu-toi-la-gi"])
    d = decide_gate(graph, ov, SafetyResult(), None)
    assert _chips_tim_hieu(graph, ov, d) == _chips_tim_hieu(graph, ov, d)


def test_khong_bay_chip_trieu_chung(graph):
    """docx/03 §7 luật 3 — không mời học sinh bấm để đọc danh sách triệu chứng."""
    cam = {"c-dau-hieu-tram-cam", "c-dau-hieu-lo-au", "c-lo-au-keo-dai"}
    for t in get_topics().topics.values():
        assert not ({c.serves for c in t.learn_chips} & cam)


def test_the_dau_hieu_toi_duoc_qua_explained_by(graph):
    """docx/13 §12 — thẻ triệu chứng chỉ lên qua SUPPORT khi node CONFIRMED."""
    for nid in ("c-dau-hieu-lo-au", "c-dau-hieu-tram-cam"):
        srcs = [e.from_ for e in graph.edges if e.type == "explained_by" and e.to == nid]
        assert srcs, f"{nid} không có đường nào tới được"
        for s in srcs:
            assert graph.node(s) is not None


# ── bài test: bot phải NHỚ kết quả (bug 09/09/2026) ───────────────────────
from app.llm.turn import _khoi_bai_test


def _ov_da_lam_test(**kw) -> Overlay:
    ov = _ov(
        has_taken_assessment=True,
        assessment_band_label="Mức đáng chú ý",
        assessment_average=3.4,
        **kw,
    )
    # 3 câu chọn "Hoàn toàn đúng" (0.80) + 1 câu "Khá đúng" (0.65)
    for nid in ("m-tu-trach", "m-chua-du-tot", "m-hiem-hai-long"):
        ov.evidence[nid] = _ev(nid, 0.80, EvidenceSource.LIKERT, vb="")
    ov.evidence["m-tieu-chuan-cao"] = _ev("m-tieu-chuan-cao", 0.65, EvidenceSource.LIKERT, vb="")
    return ov


def test_chua_lam_test_thi_noi_chua_lam(graph):
    assert _khoi_bai_test(_ov()) == "chưa làm"


def test_prompt_mang_theo_ket_qua_that(graph):
    """Trước 09/09 chỗ này chỉ là "có" — nên bot hỏi ngược "bạn đánh giá gì vậy?"."""
    khoi = _khoi_bai_test(_ov_da_lam_test())
    assert "Mức đáng chú ý" in khoi and "3.4" in khoi
    assert "Tôi thường tự trách bản thân khi mắc lỗi." in khoi


def test_chi_liet_ke_cau_chon_hoan_toan_dung(graph):
    """docx/03 §3.1 — mức 4 (0.65) là CHƯA CHẮC, không được kể như lời tự thú."""
    khoi = _khoi_bai_test(_ov_da_lam_test())
    assert "Tôi luôn đặt ra tiêu chuẩn rất cao cho bản thân." not in khoi


def test_luot_dau_sau_bai_test_hoi_vao_ket_qua(graph):
    ov = _ov_da_lam_test()
    d = decide_gate(graph, ov, SafetyResult(), None)
    assert d.reason == "assessment_debrief"
    assert d.target_nodes and ov.evidence[d.target_nodes[0]].confidence >= 0.80


def test_chi_hoi_vao_bai_test_dung_mot_lan(graph):
    """Hỏi mãi về cùng một câu Likert đọc như đang truy bài."""
    ov = _ov_da_lam_test(assessment_debriefed=True)
    d = decide_gate(graph, ov, SafetyResult(), None)
    assert d.reason != "assessment_debrief"
