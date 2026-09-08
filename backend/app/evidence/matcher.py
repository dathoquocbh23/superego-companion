"""
Trích bằng chứng TẤT ĐỊNH theo cue — KHÔNG tốn token. GĐ2, 07/09/2026.

Thay cho lời gọi LLM "extract" cũ (6.591 byte system prompt mỗi lượt). Lý do
đổi: khớp một câu tiếng Việt vào 31 node đã khai báo sẵn `cues` là bài toán
ĐỐI SÁNH, không phải bài toán SINH VĂN. Trả tiền cho một mô hình ngôn ngữ để
làm việc mà regex làm đúng hơn và nhanh hơn 1.300ms là lãng phí thuần tuý.

LLM vẫn còn phần việc của nó — suy ra cái nằm NGOÀI chữ nghĩa ("ba mẹ tốn tiền"
-> a-toi-loi). Phần đó giờ đi kèm lượt nói trong cùng một lời gọi (app/llm/turn.py)
và có hiệu lực từ lượt SAU. Cue bắt được ngay lượt này, nên chuyện trễ một lượt
chỉ ảnh hưởng tới suy diễn, không ảnh hưởng tới điều học sinh nói thẳng.
"""
from __future__ import annotations

import re

from app.graph.loader import GraphService
from app.overlay.model import Evidence, EvidenceSource
from app.safety.normalize import contains_word, normalize_vi

# Confidence theo ĐỘ ĐẶC HIỆU của cue khớp được.
#
# Trước đây mọi cue đều cho 0.70 — bằng đúng `confidence_threshold`. Nghĩa là
# một cue MỘT CHỮ ("cô đơn") lập tức được coi là bằng chứng mạnh ngang một cue
# năm chữ ("không biết nói với ai"). Sai: cue càng ngắn càng dễ khớp nhầm.
#
# Cue 1 chữ giờ nằm DƯỚI ngưỡng — nó vào overlay, hướng được câu hỏi tiếp theo,
# nhưng một mình nó không kích REFLECT. Phải có cue đặc hiệu hơn hoặc lượt sau
# nhắc lại thì mới đủ mạnh.
_CONF_1_TU = 0.65        # < confidence_threshold (0.70)
_CONF_2_TU = 0.72
_CONF_3_TU_TRO_LEN = 0.75   # = self_report_confidence_cap


def _confidence_cho(cue: str) -> float:
    so_tu = len(cue.split())
    if so_tu <= 1:
        return _CONF_1_TU
    if so_tu == 2:
        return _CONF_2_TU
    return _CONF_3_TU_TRO_LEN


# D12 — verbatim là CẢ MỆNH ĐỀ chứa cue, không phải riêng mẩu cue.
#
# Cue "bài kiểm tra" trước đây cho verbatim đúng hai chữ "bài kiểm tra", và
# INSIGHT_CARD hiện ra một dòng cụt giữa hai dòng tử tế:
#
#     "Mình vừa bị điểm kém một bài kiểm tra"  ->  "bài kiểm tra"  ->  ...
#
# Cả điểm nhấn của thẻ nằm ở chỗ "đây đúng là lời bạn nói". Một mẩu cue phá
# đúng chỗ đó. Lấy trọn mệnh đề thì dòng thẻ đọc lên nghe được, mà vẫn tuyệt
# đối là chữ họ gõ — không bịa thêm chữ nào.
# Dấu chấm / phẩy GIỮA HAI CHỮ SỐ không phải ranh giới mệnh đề — "6.5" là
# một con số, cắt ở đó thì verbatim thành "Hôm nay thi được 6".
_RANH_MENH_DE = re.compile(r"(?:(?<!\d)[.,]|[.,](?!\d))|[!?…;:\n]|\s—\s|\s-\s")

# Trần độ dài để một câu dài không nuốt trọn cả thẻ.
MAX_TU_VERBATIM = 12

# Liên từ mở đầu — cắt đi cho dòng thẻ đọc gọn.
_LIEN_TU_DAU = ("và ", "rồi ", "nhưng ", "mà ", "thì ", "nên ", "vì ", "với ")


def _verbatim_cho(user_message: str, cue: str) -> str:
    """Lấy nguyên văn HỌC SINH ĐÃ GÕ quanh cue này — trọn mệnh đề.

    Chỉ tìm khớp còn dấu. Học sinh gõ không dấu ("rat buon") thì cue vẫn khớp ở
    tầng chuẩn hoá nhưng KHÔNG lấy được verbatim — trả "" chứ không chế ra chuỗi
    có dấu mà họ chưa từng gõ. Verbatim là thứ REFLECT sẽ đặt trong ngoặc kép
    trước mặt người ta; bịa ở đây là hỏng đúng chỗ quan trọng nhất.
    """
    low = user_message.lower()
    idx = low.find(cue.lower())
    if idx < 0:
        return ""
    het = idx + len(cue)

    # Nới ra hai đầu tới ranh giới mệnh đề gần nhất.
    dau_menh_de = 0
    for m in _RANH_MENH_DE.finditer(user_message, 0, idx):
        dau_menh_de = m.end()
    m_cuoi = _RANH_MENH_DE.search(user_message, het)
    cuoi_menh_de = m_cuoi.start() if m_cuoi else len(user_message)

    cum = user_message[dau_menh_de:cuoi_menh_de].strip()
    for lt in _LIEN_TU_DAU:
        if cum.lower().startswith(lt):
            cum = cum[len(lt):].strip()
            break

    tu = cum.split()
    if len(tu) > MAX_TU_VERBATIM:
        # Quá dài thì lùi về đúng mẩu cue — thà ngắn còn hơn cắt giữa chừng
        # thành một câu người ta chưa từng nói.
        return user_message[idx:het]
    return cum or user_message[idx:het]


def match_evidence(
    graph: GraphService, user_message: str, turn_id: int
) -> list[Evidence]:
    """Mọi node có cue khớp trong tin nhắn. Mỗi node lấy cue ĐẶC HIỆU NHẤT."""
    norm_msg = normalize_vi(user_message or "")
    if not norm_msg:
        return []

    out: list[Evidence] = []
    for nid in graph.evidence_node_ids:
        node = graph.node(nid)
        if node is None:
            continue
        # Cue dài nhất thắng: "không ai chơi với" đặc hiệu hơn "nghỉ chơi".
        khop = [c for c in node.cues if contains_word(norm_msg, normalize_vi(c))]
        if not khop:
            continue
        cue = max(khop, key=lambda c: (len(c.split()), len(c)))
        out.append(
            Evidence(
                node_id=nid,
                confidence=_confidence_cho(cue),
                source=EvidenceSource.SELF_REPORT,
                turn_ids=[turn_id],
                verbatim=_verbatim_cho(user_message, cue),
            )
        )
    return out
