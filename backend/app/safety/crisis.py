"""
Phát hiện khủng hoảng tất định — chạy TRƯỚC mọi lời gọi LLM. docx/04 §1, §3, §4.

LLM không bao giờ được quyết định "đây có phải khủng hoảng không".
"""
from __future__ import annotations

from dataclasses import dataclass, field

from app.config import settings

import re

from . import phrases
from .normalize import contains_word, contains_word_accented, normalize_vi


def _matches_normalized(normalized: str, phrase: str) -> bool:
    """Khớp biên từ + tôn trọng ngữ cảnh phủ định (docx/04 §4)."""
    if not contains_word(normalized, phrase):
        return False
    negatives = phrases.NEGATIVE_CONTEXT.get(phrase)
    if not negatives:
        return True
    # còn ít nhất một lần xuất hiện KHÔNG bị theo sau bởi token phủ định?
    for m in re.finditer(r"(?<![\w])" + re.escape(phrase) + r"(?![\w])", normalized):
        tail = normalized[m.end():].lstrip()
        if not any(tail == neg or tail.startswith(neg + " ") for neg in negatives):
            return True
    return False


@dataclass
class SafetyResult:
    tier: int | None = None            # None | 1 | 2 | 3
    matched: list[str] = field(default_factory=list)
    forces_escalate: bool = False      # tier 1 / 2
    forces_bridge: bool = False        # tier 3

    @property
    def stops_pipeline(self) -> bool:
        """Tầng 1/2 → dừng pipeline ngay, không gọi LLM."""
        return self.forces_escalate


def _scan(normalized: str, raw: str, tier1_len_ok: bool) -> SafetyResult:
    matched: list[str] = []

    # --- TẦNG 1: nhóm còn dấu (không có ngoại lệ độ dài) ---
    for phrase in phrases.EXACT_ACCENTED_TIER1:
        if contains_word_accented(raw, phrase):
            matched.append(phrase)
    for phrase in phrases.NORMALIZED_TIER1:
        if _matches_normalized(normalized, phrase):
            matched.append(phrase)
    if matched:
        return SafetyResult(tier=1, matched=matched, forces_escalate=True)

    # --- TẦNG 2 (không có ngoại lệ độ dài) ---
    for phrase in phrases.NORMALIZED_TIER2:
        if _matches_normalized(normalized, phrase):
            matched.append(phrase)
    if matched:
        return SafetyResult(tier=2, matched=matched, forces_escalate=True)

    # --- TẦNG 3: kiệt quệ → ép BRIDGE. Có ngưỡng 600 ký tự ---
    for phrase in phrases.NORMALIZED_TIER3:
        if _matches_normalized(normalized, phrase):
            matched.append(phrase)
    if matched and tier1_len_ok:
        return SafetyResult(tier=3, matched=matched, forces_bridge=True)
    if matched and not tier1_len_ok:
        # đoạn văn dài kể chuyện — ghi nhận nhưng KHÔNG kích hoạt
        return SafetyResult(tier=None, matched=matched)

    return SafetyResult()


def check_crisis(user_message: str) -> SafetyResult:
    raw = user_message or ""
    normalized = normalize_vi(raw)
    tier3_len_ok = len(raw) <= settings.crisis_tier3_max_chars
    return _scan(normalized, raw, tier3_len_ok)
