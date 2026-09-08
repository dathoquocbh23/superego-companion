from app.safety.normalize import contains_word, contains_word_accented, normalize_vi


def test_normalize_strips_accents_and_d():
    assert normalize_vi("Tự Trách Bản Thân") == "tu trach ban than"
    assert normalize_vi("đau đớn") == "dau don"


def test_tu_tu_vs_tu_tu_collision():
    # cả hai đều normalize thành "tu tu"
    assert normalize_vi("tự tử") == "tu tu"
    assert normalize_vi("từ từ") == "tu tu"


def test_accented_match_distinguishes_them():
    assert contains_word_accented("mình muốn tự tử", "tự tử")
    assert not contains_word_accented("từ từ đã bạn ơi", "tự tử")


def test_word_boundary_not_substring():
    # biên từ: "cat tay" không khớp khi dính liền chữ khác
    assert not contains_word(normalize_vi("cattayao"), "cat tay")
    assert contains_word(normalize_vi("mình hay cắt tay"), "cat tay")


def test_cat_tay_ao_is_negative_context():
    # docx/04 §4 — "cắt tay áo" KHÔNG được kích hoạt khủng hoảng
    from app.safety.crisis import check_crisis

    assert not check_crisis("mình cắt tay áo cho gọn rồi mặc đi học").forces_escalate
    assert check_crisis("mình hay cắt tay khi buồn").forces_escalate
