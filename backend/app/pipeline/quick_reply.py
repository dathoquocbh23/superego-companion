"""
Sinh quick replies — 3 đến 5 chip tuỳ tình huống. docx/11 Phần E.

Cạm bẫy: gợi ý mang tính mớm (iatrogenic suggestion). KHÔNG chip node
risk_adjacent, KHÔNG chip nội dung khủng hoảng / khẳng định bệnh lý.
Luôn có 1 chip thoát. Mỗi chip mang tiền tố hệ thống.

Vì sao số chip KHÔNG cố định (docx/11 §E1): đếm chip không bằng đếm lựa chọn.
08/09/2026 quan sát được 3 chip mà hai chip nội dung cùng một hướng ("Mình thấy
mình kém cỏi" / "Mình nghĩ mình chưa cố gắng") — học sinh thật ra chỉ có MỘT
lựa chọn nội dung và một nút im lặng. Ngược lại, có lượt cần thêm nhánh (bot
vừa GIẢ ĐỊNH điều gì đó thì phải chừa đường bác bỏ) và có lượt cần bớt đi
(đang nặng mà bày 5 nút là biến trò chuyện thành bài trắc nghiệm).

    tổng = n_nội_dung ∈ [2,4]  +  1 chip thoát   →   3..5
    ngoại lệ cứng: ESCALATE = 0 · REFLECT = 2–3 (xác nhận, không phải lựa chọn)
"""
from __future__ import annotations

import re

from app.config import settings
from app.gate.decide import BRIDGE, CLARIFY, ORIENT, REFLECT, SUPPORT, GateDecision
from app.graph.loader import GraphService
from app.overlay.model import Overlay
from app.safety import phrases
from app.safety.normalize import normalize_vi

ESCAPE_CLARIFY = phrases.CHIP_DECLINE + "Mình chưa muốn nói về chuyện này"
ESCAPE_GENERIC = phrases.CHIP_DECLINE + "Không hẳn vậy"

# §E3 — trần chip nội dung. Tổng luôn = n_nội_dung + 1 chip thoát.
CHIP_NOI_DUNG_MIN = 2
CHIP_NOI_DUNG_MAX = 4

# §E6 — trước lượt này, khả năng học sinh "đã thử rồi" là rất thấp; hiện chip
# đó ra sớm chỉ tổ mớm cho họ một trải nghiệm thất bại chưa từng có.
SUPPORT_DA_THU_MIN_TURN = 4

# §E3 — dấu hiệu học sinh vừa PHẢN ĐỐI lời khuyên. Lúc đó thu hẹp lựa chọn:
# bày thêm nút ra là bot đang mặc cả.
_PHAN_DOI = re.compile(
    r"(noi thi de|de noi thoi|lam khong noi|co lam duoc dau|"
    r"thu roi|da thu|khong an thua|khong tac dung|biet vay nhung|"
    r"khong giup gi|vo ich)"
)

# §E3 — họ đang tự kể được một đoạn dài; chen 4–5 nút vào là cắt lời.
_TIN_NHAN_DAI = 25


# Chip dự phòng theo dáng câu hỏi — dùng khi chip mô hình bị lọc sạch. Cố ý
# KHÔNG nhắc bất kỳ triệu chứng nào: đây là đường chạy khi mô hình đã viết ra
# thứ không an toàn, nên chỗ này phải sạch tuyệt đối.
_ASK = phrases.CHIP_ASK
_CHIP_DU_PHONG_MAC_DINH = [
    _ASK + "Chuyện đó có hay xảy ra không",
    _ASK + "Lúc đó mình nghĩ gì trong đầu",
]
_CHIP_DU_PHONG = {
    "SU_VIEC": [_ASK + "Chuyện mới xảy ra thôi", _ASK + "Chuyện này lâu rồi"],
    "LAP_LAI": [_ASK + "Gần như lúc nào cũng vậy", _ASK + "Chỉ thỉnh thoảng thôi"],
    "SUY_NGHI": [_ASK + "Lúc đó mình nghĩ nhiều lắm", _ASK + "Lúc đó mình không nghĩ gì"],
    "VE_MINH": [_ASK + "Mình nói với mình khá nặng", _ASK + "Mình không để ý chuyện đó"],
    "CHUAN_MUC": [_ASK + "Mình đặt mức khá cao", _ASK + "Mình không đặt mức nào cả"],
    "ANH_HUONG": [_ASK + "Có, ảnh hưởng nhiều", _ASK + "Không, mình vẫn ổn"],
}


def _prov(text: str, gate: str, source_node: str | None, target_node: str | None, is_escape: bool) -> dict:
    return {
        "text": text,
        "gate": gate,
        "source_node": source_node,
        "target_node": target_node,
        "is_escape": is_escape,
    }


# ---------------------------------------------------------------------------
# §E3 — NGÂN SÁCH CHIP cho gate CLARIFY
# ---------------------------------------------------------------------------
def _co_riskflag(overlay: Overlay) -> bool:
    return overlay.has("r-keo-dai") or overlay.has("r-suy-giam-chuc-nang")


def _vua_phan_doi(overlay: Overlay, user_message: str) -> bool:
    gate_truoc = overlay.gates_used[-1] if overlay.gates_used else ""
    if gate_truoc not in (SUPPORT, BRIDGE):
        return False
    return bool(_PHAN_DOI.search(normalize_vi(user_message or "")))


def _dem_trigger_sang(graph: GraphService, overlay: Overlay) -> int:
    thr = settings.confidence_threshold
    return sum(
        1
        for nid, ev in overlay.evidence.items()
        if ev.confidence >= thr and (n := graph.node(nid)) and n.type == "trigger"
    )


def ngan_sach_chip_noi_dung(
    graph: GraphService, overlay: Overlay, user_message: str
) -> int:
    """TRẦN số chip nội dung mô hình được viết ở gate CLARIFY. docx/11 §E3.

    Trả về TRẦN chứ không phải con số chính xác: chỉ mô hình mới biết câu trả
    lời nó vừa viết có bước NEO (tức có GIẢ ĐỊNH) hay không, nên việc quyết
    "có thêm chip vai C không" thuộc về nó. Việc của hàm này là chặn trên, và
    ba điều kiện ép về 2 dưới đây là lớp GIẢM TẢI CẢM XÚC — càng nặng càng ít
    nút, cùng một logic với nhánh khủng hoảng (0 chip).
    """
    if _co_riskflag(overlay):
        return CHIP_NOI_DUNG_MIN
    if _vua_phan_doi(overlay, user_message):
        return CHIP_NOI_DUNG_MIN
    if len((user_message or "").split()) >= _TIN_NHAN_DAI:
        return CHIP_NOI_DUNG_MIN

    n = CHIP_NOI_DUNG_MIN + 1          # chừa chỗ cho vai C (bác bỏ tiền đề)
    rong_cua = _dem_trigger_sang(graph, overlay) >= 2 or (
        not overlay.evidence and overlay.turn_count <= 2
    )
    if rong_cua:
        n += 1                          # vai D (mở hướng khác)
    return min(n, CHIP_NOI_DUNG_MAX)


# ---------------------------------------------------------------------------
def build_quick_replies(
    graph: GraphService,
    overlay: Overlay,
    decision: GateDecision,
    *,
    so_dong_the: int = 0,
) -> tuple[list[str], list[dict]]:
    gate = decision.gate

    # CRISIS_CARD không kèm quick replies (docx/04 §7)
    if gate == "ESCALATE":
        return [], []

    # REFLECT → chip XÁC NHẬN, không phải chip lựa chọn: 2, hoặc 3 khi thẻ đủ
    # dài để "đúng một phần" là một câu trả lời thật (docx/11 §E5). Thẻ 4 dòng
    # thường đúng 3 sai 1; ép nhị phân thì học sinh bấm "Đúng vậy" cho xong và
    # overlay CONFIRMED một thứ chưa hề được xác nhận thật.
    if gate == REFLECT:
        yes = phrases.CHIP_CONFIRM_YES + "Đúng vậy"
        partial = phrases.CHIP_CONFIRM_PARTIAL + "Đúng một phần"
        no = phrases.CHIP_CONFIRM_NO + "Không hẳn"
        tgt = decision.target_nodes[0] if decision.target_nodes else None
        chips = [yes, no] if so_dong_the < 3 else [yes, partial, no]
        return chips, [_prov(c, gate, tgt, tgt, False) for c in chips]

    # ORIENT — thực đơn chủ đề. CỐ Ý không mang tiền tố hệ thống: chúng phải đi
    # qua bước trích như một tin nhắn thường, để cue khớp và overlay có cái để
    # bám vào ngay lượt sau. Câu chữ đã chọn cho khớp cue trong domain_graph:
    #   "điểm số" -> t-diem-so · "chuyện tình cảm" -> t-quan-he
    #   "chuyện với bạn bè" -> t-ban-be · "chuyện gia đình" -> t-gia-dinh
    if gate == ORIENT:
        chu_de = [
            ("Mình đang áp lực chuyện điểm số", "t-diem-so"),
            ("Mình có chuyện tình cảm", "t-quan-he"),
            ("Mình có chuyện với bạn bè", "t-ban-be"),
            ("Chuyện gia đình làm mình mệt", "t-gia-dinh"),
        ]
        # §E4 — chip thứ 5 chỉ khi họ ĐÃ nói gì đó mà vẫn giậm chân: lúc ấy 4 ô
        # chủ đề nhiều khả năng không chứa nổi chuyện của họ. Overlay còn rỗng
        # thì 4 ô là một thực đơn sạch, thêm ô "chuyện khác" chỉ làm loãng.
        if overlay.evidence:
            chu_de.append(("Chuyện của mình khác cơ", None))
        return (
            [t for t, _ in chu_de],
            [_prov(t, gate, None, n, False) for t, n in chu_de],
        )

    if gate == BRIDGE:
        res = decision.resource_node
        chips: list[tuple[str, str | None]] = [
            ("Mình sợ họ không hiểu", None),
            ("Thử nói với thầy cô dễ hơn", "s-gvcn"),
        ]
        # §E4 — chỉ khi nguồn là gia đình. Đó là lúc "mở lời" khó nhất, và cũng
        # là chỗ tài liệu có sẵn kịch bản mở lời để trả cho lượt sau.
        node = graph.node(res) if res else None
        if node is not None and node.resource_kind == "gia-dinh":
            chips.append(("Mình chưa biết mở lời sao", None))
        esc = phrases.CHIP_DECLINE + "Để mình nghĩ đã"
        prov = [_prov(t, gate, res, tn, False) for t, tn in chips]
        prov.append(_prov(esc, gate, res, None, True))
        return [t for t, _ in chips] + [esc], prov

    if gate == SUPPORT:
        # "Nói thì dễ" = chưa thử, thấy khó làm → lượt sau hỏi chỗ nào khó.
        # "Mình thử rồi, không ăn thua" = ĐÃ thử, không hiệu quả → lượt sau
        # TUYỆT ĐỐI không đưa kỹ năng thứ hai. Hai đường đi khác hẳn nhau nên
        # phải là hai nút khác nhau (docx/11 §E6).
        noi_dung = ["Nghe cũng hợp lý", "Nói thì dễ"]
        if overlay.turn_count >= SUPPORT_DA_THU_MIN_TURN:
            noi_dung.append("Mình thử rồi, không ăn thua")
        esc = phrases.CHIP_DECLINE + "Đổi chuyện khác đi"
        prov = [_prov(c, gate, decision.coping_node, None, False) for c in noi_dung]
        prov.append(_prov(esc, gate, decision.coping_node, None, True))
        return [*noi_dung, esc], prov

    # CLARIFY — đường DỰ PHÒNG, chỉ chạy khi chip mô hình bị lọc sạch. Giữ ở
    # mức tối thiểu 3: hai chip + chip thoát.
    #
    # Chip dự phòng phải TRẢ LỜI ĐƯỢC câu bot vừa hỏi, nên nó đi theo DÁNG của
    # lượt (docx/11 D7). Bản cũ dùng hai chip cố định cho mọi dáng, và thực tế
    # đã hiện ra cảnh bot hỏi "Bạn kỳ vọng mình được bao nhiêu?" rồi chìa ra
    # chip "Chuyện đó có hay xảy ra không" — hai câu không dính gì nhau.
    chips_out: list[str] = []
    prov = []
    target = decision.target_nodes[0] if decision.target_nodes else None
    dang = overlay.dang_da_dung[-1] if overlay.dang_da_dung else ""

    generic = _CHIP_DU_PHONG.get(dang, _CHIP_DU_PHONG_MAC_DINH)
    for text in generic:
        chips_out.append(text)
        prov.append(_prov(text, gate, target, None, False))

    chips_out.append(ESCAPE_CLARIFY)
    prov.append(_prov(ESCAPE_CLARIFY, gate, target, None, True))
    return chips_out[:3], prov[:3]
