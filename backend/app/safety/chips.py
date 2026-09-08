"""Nhận diện chip theo TIỀN TỐ hệ thống. docx/04 §5.

Chip do chính hệ thống phát ra → khi quay lại đã biết chắc ý định,
không gọi LLM để đoán lại.
"""
from __future__ import annotations

from dataclasses import dataclass

from . import phrases

CONFIRM_YES = "CONFIRM_YES"
CONFIRM_NO = "CONFIRM_NO"
# docx/11 §E5 — "Đúng một phần": họ nhận một phần thẻ phản chiếu, không phải cả
# thẻ. KHÔNG được coi như CONFIRM_YES: promote CONFIRMED ở đây là ghi vào
# overlay một sự xác nhận chưa hề xảy ra.
CONFIRM_PARTIAL = "CONFIRM_PARTIAL"
ASK = "ASK"
DECLINE = "DECLINE"

_PREFIX_TO_TYPE = {
    phrases.CHIP_CONFIRM_YES: CONFIRM_YES,
    phrases.CHIP_CONFIRM_NO: CONFIRM_NO,
    phrases.CHIP_CONFIRM_PARTIAL: CONFIRM_PARTIAL,
    phrases.CHIP_ASK: ASK,
    phrases.CHIP_DECLINE: DECLINE,
}


@dataclass
class ChipSignal:
    chip_type: str          # CONFIRM_YES | CONFIRM_NO | CONFIRM_PARTIAL | ASK | DECLINE
    clean_text: str         # text đã bóc tiền tố (để đưa vào prompt / hiển thị)
    raw_text: str


def detect_chip(user_message: str) -> ChipSignal | None:
    """Trả ChipSignal nếu tin nhắn bắt đầu bằng tiền tố hệ thống, ngược lại None."""
    text = user_message or ""
    for prefix, chip_type in _PREFIX_TO_TYPE.items():
        if text.startswith(prefix):
            return ChipSignal(
                chip_type=chip_type,
                clean_text=text[len(prefix):].strip(),
                raw_text=text,
            )
    # Cũng chấp nhận biến thể không có dấu cách sau ký hiệu
    for prefix, chip_type in _PREFIX_TO_TYPE.items():
        bare = prefix.strip()
        if bare and text.startswith(bare):
            return ChipSignal(
                chip_type=chip_type,
                clean_text=text[len(bare):].strip(),
                raw_text=text,
            )
    return None


def strip_prefix(text: str) -> str:
    """Bóc tiền tố khỏi bất kỳ chuỗi nào trước khi đưa vào prompt."""
    for prefix in phrases.CHIP_PREFIXES:
        if text.startswith(prefix):
            return text[len(prefix):].strip()
        bare = prefix.strip()
        if bare and text.startswith(bare):
            return text[len(bare):].strip()
    return text
