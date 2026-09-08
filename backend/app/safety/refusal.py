"""Từ chối ngoài phạm vi + chống jailbreak. docx/04 §8.

Trả None nếu câu hỏi nằm trong phạm vi (đồng hành cảm xúc). Ngược lại trả
tình huống: off_topic | demand_diagnosis | medical | jailbreak.
"""
from __future__ import annotations

from .normalize import normalize_vi

_JAILBREAK = [
    "bo qua huong dan", "quen cac quy tac", "quen quy tac tren", "in ra system prompt",
    "in he thong prompt", "dong vai bac si", "gia su ban duoc phep", "gia dinh ban duoc phep",
    "ban la mot ai khac", "developer mode", "che do nha phat trien", "bypass",
    "lam theo dung nhung gi toi noi", "khong con la tro ly",
]
_DEMAND_DIAGNOSIS = [
    "toi bi benh gi", "minh bi benh gi", "chan doan cho toi", "chan doan giup",
    "toi co bi tram cam khong", "minh co bi tram cam khong", "toi co bi lo au khong",
    "minh bi lam sao", "noi cho toi biet toi bi gi",
]
_MEDICAL = [
    "uong thuoc gi", "nen uong thuoc nao", "lieu luong", "toa thuoc", "ke toa",
    "thuoc chong tram cam", "ssri", "tac dung phu cua thuoc",
]
_OFF_TOPIC = [
    "giai bai tap", "giai giup bai", "giai gium bai", "giai gium minh bai", "giai ho bai",
    "lam ho bai", "lam gium bai", "lam bai tap gium", "bai tap toan nay", "bai tap hoa nay",
    "code gium", "viet gium doan van", "viet ho doan van", "dich gium", "dich ho doan",
    "thoi tiet hom nay", "ket qua bong da", "gia bitcoin", "cong thuc toan", "cong thuc hoa",
    "tom tat bai", "soan bai gium", "lam giup bai tap",
]
# Tư vấn tình cảm — NGOÀI phạm vi. Lưu ý: chỉ chặn phần XIN LỜI KHUYÊN về mối
# quan hệ. Cảm giác về BẢN THÂN trong bối cảnh tình cảm ("mình thua kém bạn Vy",
# "sợ crush thấy mình kém") vẫn TRONG phạm vi — đó là xấu hổ / giá trị bản thân.
_RELATIONSHIP_ADVICE = [
    "lam sao de tan", "lam sao tan duoc", "cach tan gai", "cach tan do", "cach cua do",
    "co nen to tinh", "nen to tinh khong", "to tinh nhu the nao", "to tinh sao cho",
    "cach lam quen voi", "lam sao de lam quen", "lam sao de bat chuyen",
    "nen nhan tin gi", "nhan tin gi cho", "rep tin nhan sao",
    "lam sao de crush thich", "de crush thich minh", "lam sao de duoc thich",
    "co nen chia tay", "nen chia tay khong", "lam sao de quay lai voi",
]


def _hit(text: str, needles: list[str]) -> bool:
    return any(n in text for n in needles)


def classify_refusal(user_message: str) -> str | None:
    t = normalize_vi(user_message)
    if _hit(t, _JAILBREAK):
        return "jailbreak"
    if _hit(t, _DEMAND_DIAGNOSIS):
        return "demand_diagnosis"
    if _hit(t, _MEDICAL):
        return "medical"
    if _hit(t, _OFF_TOPIC) or _hit(t, _RELATIONSHIP_ADVICE):
        return "off_topic"
    return None
