"""Chuẩn hoá tiếng Việt cho việc khớp phrase list. docx/04 §2."""
from __future__ import annotations

import re
import unicodedata

_WS = re.compile(r"\s+")


def normalize_vi(text: str) -> str:
    """Bỏ dấu, hạ chữ, gom khoảng trắng — để khớp phrase list.

    >>> normalize_vi("Tự tử")
    'tu tu'
    >>> normalize_vi("Từ từ đã bạn ơi")
    'tu tu da ban oi'
    """
    t = unicodedata.normalize("NFD", text.lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    t = t.replace("đ", "d").replace("Đ", "d")
    t = _WS.sub(" ", t).strip()
    return t


def contains_word(haystack_normalized: str, needle_normalized: str) -> bool:
    """Khớp theo BIÊN TỪ, không phải substring.

    Tránh "cat tay" khớp trong "cat tay ao".
    """
    if not needle_normalized:
        return False
    pattern = r"(?<![\w])" + re.escape(needle_normalized) + r"(?![\w])"
    return re.search(pattern, haystack_normalized) is not None


def contains_word_accented(raw_text: str, needle_accented: str) -> bool:
    """Khớp biên từ trên văn bản GỐC còn dấu (cho nhóm EXACT_ACCENTED)."""
    if not needle_accented:
        return False
    hay = _WS.sub(" ", raw_text.lower()).strip()
    pattern = r"(?<!\S)" + re.escape(needle_accented.lower()) + r"(?!\S)"
    return re.search(pattern, hay) is not None
