"""Phân rã bộ nhớ theo thời gian. docx/12 §3.

Vì sao phải phân rã: một học sinh lo lắng hồi tháng 3 không có nghĩa là tháng
9 vẫn vậy. Bộ nhớ không quên thì bot sẽ đóng đinh người ta vào phiên bản cũ
của chính họ — đúng thứ mà cả dự án đang cố gỡ ra.
"""
from __future__ import annotations

from datetime import datetime, timezone


def decayed_confidence(
    confidence: float,
    last_seen: datetime,
    *,
    half_life_days: float,
    now: datetime | None = None,
) -> float:
    """Bán rã: sau `half_life_days` ngày, confidence còn một nửa.

    >>> from datetime import timedelta
    >>> t = datetime.now(timezone.utc) - timedelta(days=30)
    >>> round(decayed_confidence(0.8, t, half_life_days=30), 2)
    0.4
    """
    if half_life_days <= 0:
        return confidence
    ref = now or datetime.now(timezone.utc)
    if last_seen.tzinfo is None:
        last_seen = last_seen.replace(tzinfo=timezone.utc)
    days = max(0.0, (ref - last_seen).total_seconds() / 86_400)
    return round(confidence * (0.5 ** (days / half_life_days)), 4)
