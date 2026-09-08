from app.safety.postcheck import post_check


def test_blocks_diagnosis_language():
    r = post_check("Nghe bạn kể thì có vẻ bạn bị trầm cảm rồi đấy.")
    assert r.replaced
    assert "postcheck_diagnosis_blocked" in r.flags
    assert "không đủ khả năng" in r.text


def test_blocks_promise():
    r = post_check("Đừng lo, rồi mọi chuyện sẽ ổn thôi, mình đảm bảo.")
    assert r.replaced
    assert "postcheck_medical_promise_blocked" in r.flags


def test_blocks_internal_leak_node_id():
    r = post_check("Mình thấy node m-tu-trach của bạn đang cao.")
    assert r.replaced
    assert "postcheck_internal_leak_blocked" in r.flags


def test_blocks_gate_name_leak():
    r = post_check("Hệ thống đang ở gate REFLECT nên mình hỏi lại.")
    assert r.replaced


def test_trims_to_five_sentences():
    long = "Câu một. Câu hai. Câu ba. Câu bốn. Câu năm. Câu sáu. Câu bảy."
    r = post_check(long)
    assert not r.replaced
    assert "postcheck_length_trimmed" in r.flags
    assert r.text.count(".") <= 5


def test_clean_text_passes():
    r = post_check('Mình để ý là bạn nói "mình tệ thật". Bạn kể thêm được không?')
    assert not r.replaced
    assert r.flags == []


# ── 6.5 — câu hỏi đóng ở CLARIFY (docx/04 §6.5) ─────────────────────────
# Ca thật quan sát 07/09/2026: bot đáp lời phản kháng "nói thì dễ" bằng một
# câu hỏi đóng mớm sẵn kết luận.
_CA_THAT = (
    'Bạn nói "nói thì dễ" — có phải bạn đang cảm thấy khó khăn trong việc '
    "chấp nhận bản thân mình không?"
)


def test_clarify_doi_cau_hoi_dong_thanh_cau_hoi_mo():
    r = post_check(_CA_THAT, gate="CLARIFY")
    assert "postcheck_closed_question_swapped" in r.flags
    assert "có phải" not in r.text.lower()
    assert r.text.endswith("Lúc đó trong đầu bạn nghĩ gì?")


def test_clarify_giu_lai_cau_dan_dung_loi_nguoi_dung():
    """Chỉ đổi câu hỏi, không vứt cả đoạn — câu dẫn là phần làm người ta thấy
    được lắng nghe."""
    r = post_check(_CA_THAT, gate="CLARIFY")
    assert 'nói thì dễ' in r.text


def test_clarify_chan_duoi_phai_khong():
    r = post_check("Nghe như chuyện đó nặng với bạn, phải không?", gate="CLARIFY")
    assert "postcheck_closed_question_swapped" in r.flags


def test_reflect_van_duoc_hoi_xac_nhan():
    """REFLECT bắt buộc kết bằng câu hỏi xác nhận — không được đụng vào."""
    goc = 'Mình để ý là bạn hay nói "mình dở quá". Mình hiểu vậy có đúng không?'
    r = post_check(goc, gate="REFLECT")
    assert r.flags == []
    assert r.text == goc


def test_clarify_cau_hoi_mo_thi_de_yen():
    goc = "6.5 mà bạn nói \"chán ghê\". Bạn kỳ vọng mình được bao nhiêu?"
    r = post_check(goc, gate="CLARIFY")
    assert r.flags == []
    assert r.text == goc


def test_khong_truyen_gate_thi_khong_kiem_luat_65():
    r = post_check(_CA_THAT)
    assert "postcheck_closed_question_swapped" not in r.flags


# ── 6.6 — bịa trí nhớ xuyên phiên (docx/04 §6.6, docx/12 §2) ────────────
# Ca thật 07/09/2026: bot nói "Mình nhớ bạn từng nhắc đến chuyện điểm số",
# người dùng lập tức hỏi "hồi đó mình được bao nhiêu điểm nhỉ?" — và bot
# không trả lời được, vì bộ nhớ dài hạn KHÔNG lưu câu chữ.
def test_chan_bot_khoe_nho_chuyen_cu():
    r = post_check("Mình nhớ bạn từng nhắc đến chuyện điểm số. Lần này bạn muốn chia sẻ điều gì?")
    assert "postcheck_fake_memory_blocked" in r.flags
    assert r.replaced
    assert "không giữ lại nội dung" in r.text


def test_chan_lan_truoc_ban_noi():
    r = post_check("Lần trước bạn nói mình thi được 6.5 phải không?")
    assert "postcheck_fake_memory_blocked" in r.flags


def test_trich_dan_trong_cung_phien_van_duoc():
    """Trong CÙNG phiên bot vẫn trích dẫn được — bằng ngoặc kép, không phải
    bằng cụm 'lần trước'."""
    goc = 'Bạn nói "chán ghê" — bạn kỳ vọng mình được bao nhiêu?'
    r = post_check(goc, gate="CLARIFY")
    assert r.flags == []
    assert r.text == goc


def test_co_tri_nho_thi_duoc_nhac_chuyen_cu():
    """Có câu nguyên văn từ phiên trước => nhắc lại là ĐÚNG chức năng."""
    r = post_check("Lần trước bạn nói mình thi được 6.5. Lần này sao rồi?", co_tri_nho=True)
    assert "postcheck_fake_memory_blocked" not in r.flags
    assert not r.replaced


def test_khong_co_tri_nho_ma_van_khoe_thi_chan():
    r = post_check("Lần trước bạn nói mình thi được 6.5.", co_tri_nho=False)
    assert "postcheck_fake_memory_blocked" in r.flags
