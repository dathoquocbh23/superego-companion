"""Kiểm hậu kỳ — chặn ở đầu ra, trước khi gửi cho người dùng. docx/04 §6."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher

from app.config import settings

from . import phrases
from .normalize import normalize_vi

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?…])\s+")
# Ranh giới mệnh đề trong CÙNG một câu — dùng để tách câu dẫn khỏi câu hỏi.
_CLAUSE_SPLIT = re.compile(r"\s*[—–:;,]\s*")


@dataclass
class PostCheckResult:
    text: str
    flags: list[str] = field(default_factory=list)
    replaced: bool = False
    # D6 — cụm nhãn node bị rò, nếu có. Người gọi ĐƯỢC PHÉP gọi lại mô hình một
    # lần với cụm này trong chỉ dẫn cấm; `text` lúc đó đã là câu thay thế an
    # toàn, nên bỏ qua cũng không sinh ra đầu ra xấu.
    label_leak: str | None = None
    # D9 — câu này gần trùng câu CLARIFY của lượt trước. Cùng cơ chế thử lại
    # như label_leak: `text` đã là câu thay thế an toàn nếu người gọi bỏ qua.
    lap_cau_hoi: bool = False


def _has_any(normalized: str, needles: list[str]) -> str | None:
    for n in needles:
        if n in normalized:
            return n
    return None


def _leaks_internal(text: str, normalized: str) -> bool:
    for w in phrases.POSTCHECK_INTERNAL_WORDS:
        if w in normalized:
            return True
    # node_id dạng "m-tu-trach" — tiền tố + gạch nối + chữ
    for pre in phrases.NODE_ID_PREFIXES:
        if re.search(rf"(?<![\w]){re.escape(pre)}[a-z]+-[a-z-]+", text.lower()):
            return True
    # điểm confidence dạng 0.55 / 0,55 đứng cạnh từ khoá
    if re.search(r"\b0[.,]\d{2}\b", text) and ("tin" in normalized or "muc do" in normalized):
        return True
    return False


def nhan_node_thanh_cum(label: str, toi_thieu: int = 3) -> list[str]:
    """Nhãn node -> các cụm ≥ `toi_thieu` chữ cần chặn, đã chuẩn hoá bỏ dấu.

    Chặn nguyên cả nhãn là không đủ: nhãn `m-dang-bi-trach-phat` là "Nghĩ mình
    đáng bị trách phạt", còn thứ mô hình thật sự viết ra là "đáng bị trách
    phạt". Nên cắt nhãn thành mọi cụm con liên tiếp, rồi bỏ những cụm chỉ toàn
    chữ nối (xem LABEL_STOPWORDS) — "cam thay chua" không phải là rò nhãn.
    """
    tu = [t for t in normalize_vi(label or "").split() if t]
    if len(tu) < toi_thieu:
        return []
    cum: list[str] = []
    for i in range(len(tu) - toi_thieu + 1):
        for j in range(i + toi_thieu, len(tu) + 1):
            phan = tu[i:j]
            if all(t in phrases.LABEL_STOPWORDS for t in phan):
                continue
            # Cụm phải kết thúc bằng một từ MANG NGHĨA, nếu không "dang bi
            # trach" và "dang bi trach phat" đều khớp mà cụm ngắn thì mơ hồ hơn.
            if phan[-1] in phrases.LABEL_STOPWORDS or phan[0] in phrases.LABEL_STOPWORDS:
                continue
            cum.append(" ".join(phan))
    return cum


def find_label_leak(normalized: str, node_labels: list[str]) -> str | None:
    """Câu trả lời có chứa nhãn nội bộ của node nào không. D6.

    `node_labels` chỉ nên gồm nhãn của node PHÁN QUYẾT (manifestation / affect /
    impact). Nhãn trigger là chữ thường ngày — "kết quả học tập", "chuyện tình
    cảm" — bot nói ra hoàn toàn bình thường, đưa vào đây là tự chặn mình.
    """
    for label in node_labels:
        for cum in nhan_node_thanh_cum(label):
            if cum in normalized:
                return cum
    return None


def _truncate_sentences(text: str, max_sentences: int) -> tuple[str, bool]:
    parts = [p for p in _SENTENCE_SPLIT.split(text.strip()) if p]
    if len(parts) <= max_sentences:
        return text, False
    return " ".join(parts[:max_sentences]).strip(), True


def is_near_duplicate(a: str, b: str, nguong: float = 0.75) -> bool:
    """Hai câu có phải nói cùng một điều không (bỏ dấu, bỏ hoa thường).

    Dùng cho câu dẫn của SUPPORT: nó đứng NGAY DƯỚI câu REFLECT của lượt trước,
    trên cùng màn hình. Lặp lại là bot nghe như kẹt băng — và tệ hơn, nó hỏi
    xác nhận lại đúng cái người dùng vừa bấm "Đúng vậy".

    Prompt đã cấm (14_SUPPORT luật 3) nhưng LLM phá luật là chuyện thường, nên
    cần một chốt chặn không phụ thuộc mô hình.
    """
    x, y = normalize_vi(a or ""), normalize_vi(b or "")
    if not x or not y:
        return False
    return SequenceMatcher(None, x, y).ratio() >= nguong


def _swap_closed_question(text: str) -> tuple[str, bool]:
    """Đổi câu hỏi ĐÓNG cuối cùng thành một câu hỏi mở.

    Cố ý KHÔNG thay cả đoạn như 6.1–6.3: câu dẫn phía trước thường vẫn tốt
    (nó dùng lại lời người dùng), chỉ mỗi câu hỏi là hỏng. Vứt hết đi thì mất
    luôn phần duy nhất làm người ta thấy được lắng nghe.
    """
    parts = [p for p in _SENTENCE_SPLIT.split(text.strip()) if p]
    if not parts:
        return text, False
    last = parts[-1]
    if "?" not in last:
        return text, False
    if _has_any(normalize_vi(last), phrases.POSTCHECK_CLOSED_QUESTION) is None:
        return text, False

    # Câu dẫn và câu hỏi thường nằm CHUNG một câu, nối bằng gạch ngang:
    #   Bạn nói "nói thì dễ" — có phải bạn đang ... không?
    # Cắt ở ranh giới mệnh đề MUỘN NHẤT mà phần đuôi vẫn còn cụm đóng, để giữ
    # lại được nhiều câu dẫn nhất có thể.
    keep = ""
    for m in _CLAUSE_SPLIT.finditer(last):
        if _has_any(normalize_vi(last[m.end():]), phrases.POSTCHECK_CLOSED_QUESTION):
            keep = last[: m.start()].strip()
    if keep and keep[-1] not in ".!?…":
        keep += "."

    parts[-1] = f"{keep} {phrases.SAFE_OPEN_QUESTION}".strip() if keep else phrases.SAFE_OPEN_QUESTION
    return " ".join(parts).strip(), True


def post_check(
    text: str,
    gate: str | None = None,
    *,
    co_tri_nho: bool = False,
    node_labels: list[str] | None = None,
    cau_truoc: str = "",
) -> PostCheckResult:
    """Chạy trên TOÀN BỘ văn bản LLM sinh ra.

    `gate` chỉ dùng cho luật 6.5 (câu hỏi đóng): REFLECT được phép hỏi xác
    nhận, CLARIFY thì không. Bỏ trống = không kiểm luật đó.

    `co_tri_nho` = lượt này CÓ câu nguyên văn từ phiên trước đưa vào prompt.
    Có thì bot được nhắc chuyện cũ (luật 6.6 tha); không có mà vẫn nói
    "mình nhớ bạn từng…" thì đó là bịa — chặn.
    """
    raw = (text or "").strip()
    normalized = normalize_vi(raw)
    flags: list[str] = []

    # 6.1 — ngôn ngữ chẩn đoán → THAY THẾ TOÀN BỘ, không sửa vặt
    if _has_any(normalized, phrases.POSTCHECK_DIAGNOSIS):
        return PostCheckResult(
            text=phrases.SAFE_REPLACEMENT_DIAGNOSIS,
            flags=["postcheck_diagnosis_blocked"],
            replaced=True,
        )

    # 6.2 — khẳng định y khoa & hứa hẹn → thay thế toàn bộ
    if _has_any(normalized, phrases.POSTCHECK_MEDICAL_PROMISE):
        return PostCheckResult(
            text=phrases.SAFE_REPLACEMENT_DIAGNOSIS,
            flags=["postcheck_medical_promise_blocked"],
            replaced=True,
        )

    # 6.3 — rò rỉ nội bộ → thay thế toàn bộ
    if _leaks_internal(raw, normalized):
        return PostCheckResult(
            text=phrases.SAFE_REPLACEMENT_DIAGNOSIS,
            flags=["postcheck_internal_leak_blocked"],
            replaced=True,
        )

    # 6.6 — bịa trí nhớ xuyên phiên → thay thế toàn bộ bằng câu nói thật.
    #        Chỉ chặn khi bot KHÔNG có câu nào để nhớ. Có câu thì nhắc lại là
    #        đúng chức năng (docx/12 §5.1).
    if not co_tri_nho and _has_any(normalized, phrases.POSTCHECK_FAKE_MEMORY):
        return PostCheckResult(
            text=phrases.SAFE_REPLACEMENT_FAKE_MEMORY,
            flags=["postcheck_fake_memory_blocked"],
            replaced=True,
        )

    # 6.7 (D6) — rò NHÃN NODE → thay bằng một câu CLARIFY hợp lệ, và báo cụm
    #            bị rò để người gọi có thể thử lại một lần.
    leak = find_label_leak(normalized, node_labels or [])
    if leak:
        return PostCheckResult(
            text=phrases.SAFE_REPLACEMENT_LABEL_LEAK,
            flags=["postcheck_node_label_leak"],
            replaced=True,
            label_leak=leak,
        )

    # 6.8 (D9) — CLARIFY hỏi lại đúng câu của lượt trước. 08/09/2026 quan sát
    #            được 5 lượt liền cùng một khuôn: `Bạn nói "…" — bạn có thể kể
    #            thêm về một lần cụ thể mà bạn thấy như vậy không?`. Skill đã
    #            dặn "câu hỏi lượt này phải KHÁC HẲN lượt trước" nhưng lời dặn
    #            trong prompt không phải là chốt chặn.
    if gate == "CLARIFY" and cau_truoc and is_near_duplicate(raw, cau_truoc, 0.72):
        return PostCheckResult(
            text=phrases.SAFE_REPLACEMENT_LAP_CAU_HOI,
            flags=["postcheck_clarify_lap_cau_hoi"],
            replaced=True,
            lap_cau_hoi=True,
        )

    # 6.5 — CLARIFY: câu hỏi đóng / mớm xác nhận → đổi thành câu hỏi mở
    if gate == "CLARIFY":
        raw, swapped = _swap_closed_question(raw)
        if swapped:
            flags.append("postcheck_closed_question_swapped")

    # 6.4 — giới hạn độ dài
    trimmed, was_trimmed = _truncate_sentences(raw, settings.max_response_sentences)
    if was_trimmed:
        flags.append("postcheck_length_trimmed")

    return PostCheckResult(text=trimmed, flags=flags, replaced=False)
