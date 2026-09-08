"""
{GATE_DIRECTIVE} — nói cho mô hình biết LƯỢT NÀY phải đạt được gì. GĐ3, 07/09/2026.

Đối chiếu AGENT3_MENTOR_SKILL.md mục "🎯 CHỈ DẪN CÁ NHÂN HÓA / ĐỊNH HƯỚNG
PHƯƠNG PHÁP": hệ thống đã phân tích và đã quyết; prompt chỉ việc nói thẳng
quyết định đó ra, kèm lý do.

Vì sao cần: trước GĐ3, skill chỉ mô tả gate một cách TRỪU TƯỢNG ("bạn chưa đủ
hiểu để phản chiếu") và đưa 9 luật cấm. Mô hình biết không được làm gì, nhưng
không biết lượt này THẾ NÀO LÀ XONG VIỆC. Kết quả là câu an toàn và rỗng — đúng
thứ quan sát được ngày 07/09/2026: bốn lượt liền hỏi "điều gì đang diễn ra
trong bạn lúc này?".

Luật viết directive:
  - Nói ĐIỀU KIỆN HOÀN THÀNH, không nói điều cấm (phần cấm đã ở checklist).
  - Nêu lý do gate nổ, bằng tiếng người, để mô hình hiểu ngữ cảnh chứ không đoán.
  - 1–3 câu. Dài hơn là lại thành một bộ luật nữa.
"""
from __future__ import annotations

import re

from app.gate.decide import (
    BRIDGE, CLARIFY, ESCALATE, ORIENT, REFLECT, SUPPORT, GateDecision,
)
from app.graph.loader import GraphService
from app.overlay.model import EvidenceSource, Overlay
from app.safety.normalize import normalize_vi

# ── D7 (viết lại 08/09/2026) — DÁNG CÂU HỎI SUY RA TỪ NODE ĐANG NHẮM ─────
#
# Bản đầu (sáng 08/09) chọn dáng ĐỘC LẬP với target node. Hậu quả quan sát
# được ngay: directive nói hai điều đánh nhau —
#
#   "Lượt này cần hiểu rõ hơn về «Đặt tiêu chuẩn rất cao»"     (từ target)
#   "Dáng câu hỏi: hỏi vào SỰ VIỆC — chuyện gì đã xảy ra"      (từ dáng)
#
# Mô hình theo câu cụ thể hơn, tức đi mò SỰ VIỆC, và vì SỰ VIỆC là dáng mặc
# định nên nó mò mãi: 5 lượt liền "bạn kể thêm một lần cụ thể được không?"
# trong khi học sinh đã kể sự việc ngay từ lượt 1 (thi toán 6.5).
#
# Sửa: dáng SUY RA TỪ KIỂU của node đang nhắm, nên hai dòng luôn nói cùng một
# điều. Và không bao giờ lặp dáng của lượt trước.
#
# Bỏ luôn khoá "phải có manifestation SELF_REPORT mới được hỏi về bản thân".
# Khoá đó sai với chính plan — docx/03 §2 ghi rõ việc DUY NHẤT `INFERRED` được
# dùng là "chọn câu hỏi tiếp theo (gate CLARIFY)", và đường nâng cấp source là
# INFERRED --(bot hỏi, user trả lời khẳng định)--> SELF_REPORT. Cấm hỏi về node
# INFERRED là cắt đứt đúng cơ chế đó. Cái bị cấm là NÓI RA, và việc đó đã có
# post-check D6 lo.
SU_VIEC = "SU_VIEC"
LAP_LAI = "LAP_LAI"
SUY_NGHI = "SUY_NGHI"
VE_MINH = "VE_MINH"
CHUAN_MUC = "CHUAN_MUC"
ANH_HUONG = "ANH_HUONG"

_DANG_TEXT = {
    SU_VIEC: (
        "Dáng câu hỏi lượt này: hỏi vào SỰ VIỆC — chuyện gì đã xảy ra, lúc nào, "
        "với ai. Chưa hỏi vào bên trong họ."
    ),
    LAP_LAI: (
        "Dáng câu hỏi lượt này: chuyện này LẶP LẠI, nên hỏi vào hoàn cảnh — nó "
        "thường xảy ra lúc nào, trong tình huống nào."
    ),
    SUY_NGHI: (
        "Dáng câu hỏi lượt này: hỏi CÂU CHẠY QUA ĐẦU họ ngay khoảnh khắc đó — "
        "một câu cụ thể, không phải một nhận định về bản thân."
    ),
    VE_MINH: (
        "Dáng câu hỏi lượt này: hỏi họ thấy MÌNH là người thế nào trong chuyện "
        "đó — về con người họ, không phải về suy nghĩ thoáng qua."
    ),
    CHUAN_MUC: (
        "Dáng câu hỏi lượt này: hỏi vào MỨC họ đặt ra cho bản thân — bao nhiêu "
        "thì họ thấy được, thế nào là đủ."
    ),
    ANH_HUONG: (
        "Dáng câu hỏi lượt này: hỏi chuyện đó đang ẢNH HƯỞNG tới sinh hoạt hằng "
        "ngày của họ ra sao — ăn, ngủ, học, gặp bạn."
    ),
}

# Dáng đi tiếp khi dáng chọn ra đã dùng trong VÀI LƯỢT GẦN ĐÂY. Hỏi lại đúng
# một kiểu câu hai lượt liền là dấu hiệu rõ nhất cho người dùng thấy bot không
# nghe. Bậc kế phải NHẢY XA: cho VE_MINH -> SUY_NGHI thì hai câu vẫn na ná nhau
# (đã thấy thật), nên chúng đứng cách nhau trong vòng dưới đây.
_DANG_KE = {
    SU_VIEC: SUY_NGHI,
    SUY_NGHI: CHUAN_MUC,
    CHUAN_MUC: VE_MINH,
    VE_MINH: ANH_HUONG,
    ANH_HUONG: LAP_LAI,
    LAP_LAI: SU_VIEC,
}

# Số lượt gần nhất mà một dáng không được lặp lại.
DANG_NE_TRONG = 2

# Node đặt chuẩn mực — hỏi vào "bao nhiêu thì đủ" tự nhiên hơn hỏi "bạn thấy
# mình thế nào".
_NODE_CHUAN_MUC = {"m-tieu-chuan-cao", "m-phai-hoan-hao", "m-hiem-hai-long"}

# "mấy tuần nay", "lúc nào cũng", "lần nào cũng"… — dấu hiệu chuyện lặp lại.
_LAP_LAI_RE = re.compile(
    r"\b(luc nao cung|lan nao cung|hom nao cung|ngay nao cung|bao gio cung|"
    r"toan la|cu bi|hay bi|hay thay|thuong xuyen|suot ngay|may tuan|may thang|"
    r"lau roi|tu truoc toi gio|van the|van vay|mai ma van)\b"
)


def chon_dang_cau_hoi(
    graph: GraphService,
    overlay: Overlay,
    user_message: str,
    target_node: str | None = None,
) -> tuple[str, str]:
    """(khoá dáng, câu chỉ dẫn) cho {GATE_DIRECTIVE}. docx/11 D7.

    Dáng đi theo KIỂU của node đang nhắm, để nó không đánh nhau với câu
    "lượt này cần hiểu rõ hơn về «…»" đứng ngay trước nó.
    """
    node = graph.node(target_node) if target_node else None
    norm = normalize_vi(user_message or "")

    if node is None:
        dang = SU_VIEC
    elif node.type == "trigger":
        dang = SU_VIEC
    elif node.type == "impact":
        dang = ANH_HUONG
    elif node.type == "affect":
        dang = SUY_NGHI
    elif node.id in _NODE_CHUAN_MUC:
        dang = CHUAN_MUC
    else:                                    # manifestation
        dang = VE_MINH

    # Họ vừa nói "chuyện này hay xảy ra" mà bị hỏi "chuyện gì đã xảy ra" là lỗi
    # đọc-không-kỹ rõ nhất — ưu tiên đọc câu của họ hơn kiểu node.
    if dang == SU_VIEC and _LAP_LAI_RE.search(norm):
        dang = LAP_LAI

    # Chưa biết gì ngoài một mẩu bối cảnh thì đừng hỏi vào con người họ.
    if dang in (VE_MINH, SUY_NGHI) and len(overlay.evidence) < 2:
        dang = SU_VIEC

    # Né mọi dáng đã dùng trong DANG_NE_TRONG lượt gần nhất; đi tối đa một vòng
    # rồi thôi (dù sao cũng phải chọn một cái).
    gan_day = overlay.dang_da_dung[-DANG_NE_TRONG:]
    for _ in range(len(_DANG_KE)):
        if dang not in gan_day:
            break
        dang = _DANG_KE[dang]

    return dang, _DANG_TEXT[dang]


# Lý do gate nổ, diễn đạt cho mô hình đọc. Không dùng lại chuỗi `reason` thô —
# "suy_giam_chuc_nang" không nói lên điều gì với một mô hình ngôn ngữ.
_LY_DO_BRIDGE = {
    "safety_tier_3": "có dấu hiệu cần chú ý về an toàn",
    "vo_vong_confirmed": "họ đã xác nhận cảm giác vô vọng",
    "keo_dai": "chuyện này đã kéo dài nhiều tuần",
    "suy_giam_chuc_nang": "chuyện này đã ảnh hưởng tới sinh hoạt hằng ngày của họ",
}


def _da_biet_gi(graph: GraphService, overlay: Overlay, bo_qua: str | None = None) -> str:
    """Tóm tắt điều bot ĐÃ ghi nhận — để nó đừng hỏi lại thứ đã biết."""
    nhan: list[str] = []
    for nid, ev in overlay.evidence.items():
        if nid == bo_qua or not ev.can_be_spoken:
            continue
        node = graph.node(nid)
        if node and node.is_evidence and not node.risk_adjacent:
            nhan.append(node.label.lower())
    if not nhan:
        return ""
    return "; ".join(nhan[:4])


def build_directive(
    graph: GraphService,
    overlay: Overlay,
    decision: GateDecision,
    *,
    refusal_situation: str | None = None,
    user_message: str = "",
) -> str:
    if refusal_situation is not None:
        return (
            "Người dùng vừa yêu cầu một thứ nằm ngoài việc của bạn. Lượt này CHỈ "
            "từ chối ngắn gọn, tử tế, rồi mời họ quay lại chuyện của chính họ. "
            "Không phân tích tâm lý họ, không giảng giải vì sao bạn từ chối."
        )

    gate = decision.gate
    target = decision.target_nodes[0] if decision.target_nodes else None
    node = graph.node(target) if target else None
    da_biet = _da_biet_gi(graph, overlay, bo_qua=target)

    if gate == ESCALATE:  # pragma: no cover — ESCALATE không gọi LLM
        return "Lớp an toàn đã xử lý. Bạn không viết gì ở lượt này."

    if gate == ORIENT:
        so_luot = overlay.turn_count
        vi_sao = (
            f"Đã {so_luot} lượt mà bạn vẫn chưa nắm được điều gì cụ thể về người này"
            if not overlay.evidence
            else "Ba lượt hỏi vừa rồi không thu thêm được gì mới"
        )
        return (
            f"{vi_sao} — cách hỏi hiện tại KHÔNG hiệu quả và hỏi thêm cũng vậy. "
            "Lượt này DỪNG hỏi: nói thật là mình chưa nắm được, rồi mời họ chỉ "
            "hướng. Hệ thống đã hiện sẵn chip chủ đề bên dưới, đừng đọc lại "
            "chúng. Xong việc = họ bấm được một chủ đề, hoặc tự nói ra chuyện "
            "của mình."
        )

    if gate == CLARIFY:
        if decision.reason == "chip_confirm_no":
            return (
                "Người dùng vừa bấm \"Không hẳn\" — điều bạn đoán ở lượt trước là "
                "SAI. Lượt này lùi hẳn lại: hỏi một câu mở để chính họ nói ra điều "
                "đúng. Xong việc = họ tự mô tả lại bằng lời của họ. Tuyệt đối "
                "không đoán lại một phiên bản khác."
            )
        if decision.reason == "chip_confirm_partial":
            return (
                "Người dùng vừa bấm \"Đúng một phần\" — thẻ bạn đưa ra ĐÚNG một "
                "phần và SAI một phần, họ chưa nói phần nào. Lượt này hỏi đúng "
                "một câu: chỗ nào trong đó chưa khớp với họ. Xong việc = họ chỉ "
                "ra được dòng lệch. Không bào chữa cho thẻ, không dựng lại thẻ "
                "khác, không khuyên gì."
            )
        if decision.reason == "chip_decline":
            return (
                "Người dùng vừa nói họ chưa muốn nói về chuyện đó. Tôn trọng "
                "hẳn: lượt này chuyển sang thứ khác họ có thể đang muốn nói, hoặc "
                "hỏi xem họ muốn nói về gì. Xong việc = họ thấy được tôn trọng, "
                "không bị kéo lại chủ đề vừa từ chối."
            )
        _, dang = chon_dang_cau_hoi(graph, overlay, user_message, target)
        if not overlay.evidence or decision.reason == "empty_overlay":
            return (
                "Bạn CHƯA biết gì về chuyện đang xảy ra với người này. Lượt này "
                "phải moi ra được MỘT SỰ VIỆC CỤ THỂ: chuyện gì đã xảy ra, khi "
                "nào, với ai. Xong việc = bạn cầm được một chi tiết có thật để "
                "lượt sau bám vào. Chưa đủ để phản chiếu bất cứ điều gì — đừng thử. "
                f"{dang}"
            )
        muc_tieu = f"«{node.label}»" if node else "điều họ vừa nhắc tới"
        phan_da_biet = (
            f"Bạn đã ghi nhận: {da_biet}. Đừng hỏi lại những thứ đó. " if da_biet else ""
        )
        return (
            f"{phan_da_biet}Lượt này cần hiểu rõ hơn về {muc_tieu} — nhưng hỏi vào "
            "TRẢI NGHIỆM THẬT của họ, không hỏi vào cái nhãn đó, và TUYỆT ĐỐI không "
            "nhắc lại cụm chữ trong dấu «». Xong việc = họ kể thêm một chi tiết mới "
            f"mà bạn chưa có. {dang}"
        )

    if gate == REFLECT:
        if decision.mode == "cycle":
            return (
                "Nhiều mắt xích của một vòng lặp đã sáng cùng lúc. Lượt này xâu "
                "chuỗi chúng lại theo ĐÚNG THỨ TỰ đã cho, dùng nguyên văn lời họ, "
                "rồi hỏi xem bạn hiểu có đúng không. Xong việc = họ nhìn thấy cái "
                "vòng, không phải nghe một lời nhận xét về bản thân."
            )
        so = len(decision.target_nodes) or 1
        return (
            f"Đã đủ bằng chứng ({so} điều chính họ tự nói ra). Lượt này nêu THỬ "
            "mẫu hình bạn thấy, bằng chính lời họ, rồi xin xác nhận. Xong việc = "
            "họ gật hoặc lắc được. Chưa phải lúc khuyên gì cả."
        )

    if gate == SUPPORT:
        body = graph.content_body(decision.coping_node) if decision.coping_node else None
        tieu_de = (body or {}).get("title", "một gợi ý")
        return (
            f"Người dùng vừa XÁC NHẬN điều bạn phản chiếu ở lượt trước. Thẻ "
            f"«{tieu_de}» sẽ hiện ngay bên dưới câu bạn viết. Lượt này bạn CHỈ "
            "viết một câu dẫn nối sang thẻ đó. Xong việc = một câu, đọc lên thấy "
            "tự nhiên nối tiếp cái gật đầu của họ."
        )

    if gate == BRIDGE:
        res = graph.node(decision.resource_node) if decision.resource_node else None
        ai = res.label.lower() if res else "một người thật"
        ly_do = _LY_DO_BRIDGE.get(decision.reason, "chuyện này đã vượt quá điều bạn giúp được")
        return (
            f"Hệ thống thấy {ly_do}. Lượt này khuyến khích họ nói chuyện với "
            f"{ai} — giọng bình thường, như gợi ý một việc nhỏ, KHÔNG làm to "
            "chuyện và không doạ. Xong việc = họ thấy việc đó khả thi, không "
            "thấy mình đang bị đẩy đi."
        )

    return "Tiến hành bình thường theo luật của skill này."
