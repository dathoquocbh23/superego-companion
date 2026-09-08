"""
5 kịch bản vàng — mỗi kịch bản khoá MỘT tầng đã xây, chạy đầu-cuối qua
run_chat_turn() ở chế độ LLM_OFFLINE (tất định, không tốn token, không phụ
thuộc mạng). GĐ5, 07/09/2026.

Vì sao chỉ đọc GATE/CARD/CHIP, không đọc câu trả lời: offline trả một câu
tĩnh cố định (app/llm/client.py:_OFFLINE_SENTENCE) — nội dung câu chữ không
có ý nghĩa để assert. "Vàng" ở đây là QUỸ ĐẠO GATE + cấu trúc đầu ra, thứ
hoàn toàn tất định vì trích bằng chứng (GĐ2) và quyết định gate đều là hàm
thuần, không phụ thuộc LLM.

Mỗi test có docstring nêu rõ ĐANG BẢO VỆ REGRESSION NÀO — không phải test
cho có, mà test để một lần sửa sau này lỡ phá lại đúng chỗ cũ thì đỏ ngay.
"""
from __future__ import annotations

import uuid

import pytest

from app.overlay.model import Overlay
from app.overlay.store import get_store
from app.pipeline.runner import run_chat_turn


async def _phien_moi() -> str:
    sid = str(uuid.uuid4())
    await get_store().save(Overlay(session_id=sid))
    return sid


async def _mot_luot(sid: str, msg: str) -> dict:
    """Chạy một lượt, gom lại các sự kiện SSE thành một bản tóm tắt dễ assert."""
    out = {"gate": None, "message_type": None, "card": None, "chips": [], "tokens": 0}
    async for ev, data in run_chat_turn(sid, msg):
        if ev == "meta":
            out["gate"] = data["gate"]
            out["message_type"] = data["message_type"]
        elif ev == "card":
            out["card"] = data
        elif ev == "token":
            out["tokens"] += 1
        elif ev == "footer":
            out["chips"] = data["quickReplies"]
    return out


def _tien_to_he_thong(chip: str) -> bool:
    return chip[:2] in {"✓ ", "✗ ", "~ ", "? ", "— "}


# ═══════════════════════════════════════════════════════════════════════
# 1 — TẦNG ĐỜI SỐNG (GĐ1): đúng bug trong ảnh chụp 07/09/2026
# ═══════════════════════════════════════════════════════════════════════
@pytest.mark.asyncio
async def test_1_that_tinh_roi_buon_thoat_duoc_clarify():
    """Trước GĐ1: "thất tình" + "rất buồn" khớp ĐÚNG 0 node — gate kẹt ở
    CLARIFY vĩnh viễn, bot hỏi "Điều gì đang diễn ra trong bạn lúc này?" lặp
    3-4 lượt liền (ảnh chụp thật, không phải giả định).

    Sau GĐ1: tầng trigger/affect đời sống cho bot chỗ để nhắm, và đủ 3 node
    self-report mạnh thì REFLECT phải nổ — không được kẹt CLARIFY quá 2 lượt.
    """
    sid = await _phien_moi()

    l1 = await _mot_luot(sid, "Mình vừa gặp một chuyện và không biết nói với ai")
    assert l1["gate"] == "CLARIFY"

    l2 = await _mot_luot(sid, "Mình thất tình rồi huhu")
    assert l2["gate"] == "CLARIFY"          # còn 2 node mạnh, chưa đủ 3

    l3 = await _mot_luot(sid, "Mình đang rất buồn")
    assert l3["gate"] == "REFLECT", (
        "kẹt CLARIFY quá 2 lượt build-evidence — đúng lỗi đã sửa ở GĐ1"
    )
    assert l3["message_type"] == "REFLECT"
    assert l3["chips"] == ["✓ Đúng vậy", "✗ Không hẳn"], "REFLECT đơn phải hỏi xác nhận"

    ov = await get_store().get(sid)
    assert {"a-co-don", "t-quan-he", "a-buon"} <= set(ov.evidence)


# ═══════════════════════════════════════════════════════════════════════
# 2 — LÕI VÒNG LẶP + POLICY EDGE: money shot của cả hệ thống
# ═══════════════════════════════════════════════════════════════════════
@pytest.mark.asyncio
async def test_2_vong_lap_cau_toan_den_insight_roi_toi_coping_dung():
    """Đủ 4/7 node của cycle-tu-phe-phan (min_nodes_to_activate=4) phải dựng
    INSIGHT_CARD; bấm "Đúng vậy" phải promote CONFIRMED và đi tới ĐÚNG coping
    theo policy edge ưu tiên cao nhất (m-tu-trach, priority=30 -> k-tu-tran-an)
    — không phải default_coping (k-nhan-dien-tu-phe-phan), và không phải
    coping bất kỳ nào khác có priority thấp hơn.
    """
    sid = await _phien_moi()

    l1 = await _mot_luot(sid, "Hôm nay thi được 6.5, mình dở quá")
    assert l1["gate"] == "CLARIFY"           # 2 node (t-diem-so, m-tu-trach), chưa đủ

    l2 = await _mot_luot(sid, "Ít nhất phải được top, không thì mình lo quá")
    assert l2["gate"] == "REFLECT"
    assert l2["message_type"] == "INSIGHT_CARD"
    assert l2["card"]["type"] == "INSIGHT_CARD"
    assert 3 <= len(l2["card"]["lines"]) <= 5
    assert l2["card"]["closing"], "INSIGHT_CARD phải có câu hỏi xác nhận"
    # docx/11 §E5 — thẻ ≥ 3 dòng thì có chip thứ ba. Nhị phân Đúng/Không hẳn ép
    # học sinh xác nhận cả dòng sai hoặc vứt cả mấy dòng đúng.
    assert l2["chips"] == ["✓ Đúng vậy", "~ Đúng một phần", "✗ Không hẳn"]

    ov = await get_store().get(sid)
    assert ov.active_cycles == ["cycle-tu-phe-phan"]

    l3 = await _mot_luot(sid, "✓ Đúng vậy")
    assert l3["gate"] == "SUPPORT"
    assert l3["message_type"] == "COPING_CARD"
    assert l3["card"]["title"] == "Thử đối xử với mình như với một người bạn", (
        "phải chọn k-tu-tran-an (priority 30 qua m-tu-trach) — sai policy edge "
        "là rơi về default_coping hoặc một coping ưu tiên thấp hơn, sai với "
        "chính điều người dùng vừa nói"
    )
    assert l3["card"]["source"], "coping card phải có nguồn trích dẫn"

    ov = await get_store().get(sid)
    for nid in ("m-tu-trach", "t-diem-so", "m-tieu-chuan-cao", "a-lo-lang"):
        assert ov.is_confirmed(nid), (
            f"{nid} thuộc cycle-tu-phe-phan đang active — "
            "bấm 'Đúng vậy' phải confirm MỌI node cycle đã có evidence, không riêng một node"
        )


@pytest.mark.asyncio
async def test_2b_dung_mot_phan_khong_mo_support_va_khoa_reflect():
    """docx/11 §E5 — chip thứ ba của INSIGHT_CARD.

    Bảo vệ ba thứ cùng lúc:
      · "Đúng một phần" KHÔNG promote CONFIRMED → gate SUPPORT không được mở
        (đưa kỹ năng dựa trên mẫu hình mới đúng một nửa là đúng kiểu sai mà cả
        tài liệu đang tránh);
      · nó nâng confidence vừa phải, không vứt bỏ như "Không hẳn";
      · REFLECT bị khoá vài lượt, nếu không thì lượt ngay sau bot dựng lại y
        hệt cái thẻ họ vừa nói là chưa khớp.
    """
    sid = await _phien_moi()
    await _mot_luot(sid, "Hôm nay thi được 6.5, mình dở quá")
    l2 = await _mot_luot(sid, "Ít nhất phải được top, không thì mình lo quá")
    assert l2["message_type"] == "INSIGHT_CARD"
    assert "~ Đúng một phần" in l2["chips"]

    l3 = await _mot_luot(sid, "~ Đúng một phần")
    assert l3["gate"] == "CLARIFY", "đúng MỘT PHẦN thì đi hỏi chỗ lệch, không đưa kỹ năng"
    assert l3["card"] is None

    ov = await get_store().get(sid)
    assert not any(ov.is_confirmed(n) for n in ov.evidence), (
        "không node nào được CONFIRMED — họ mới nói 'gần đúng'"
    )
    assert ov.confidence("m-tu-trach") >= 0.80, "nâng vừa phải, không vứt bỏ"
    assert ov.reflect_locked_until > ov.turn_count

    l4 = await _mot_luot(sid, "Chỗ mình lo là chuyện thi cử thôi")
    assert l4["gate"] != "REFLECT", "REFLECT còn trong thời gian khoá"


# ═══════════════════════════════════════════════════════════════════════
# 3 — AN TOÀN THẮNG MỌI THỨ, BẤT KỂ OVERLAY ĐANG Ở ĐÂU
# ═══════════════════════════════════════════════════════════════════════
@pytest.mark.asyncio
async def test_3_escalate_ghi_de_bat_ke_trang_thai_truoc_do():
    """ESCALATE không phải một gate bình thường trong hàng đợi ưu tiên — nó
    phải cắt ngang NGAY LẬP TỨC dù overlay đã có evidence, đã ở REFLECT, hay
    đang giữa chừng một cycle. Test riêng "từ trạng thái rỗng" đã có ở
    test_pipeline.py; test này khoá đường KHÓ hơn — override MỘT TRẠNG THÁI
    ĐANG DỞ, không phải từ đầu.
    """
    sid = await _phien_moi()

    await _mot_luot(sid, "Hôm nay thi được 6.5, mình dở quá")
    truoc = await _mot_luot(sid, "Ít nhất phải được top, không thì mình lo quá")
    assert truoc["gate"] == "REFLECT"        # xác nhận đã có trạng thái để override

    khung_hoang = await _mot_luot(sid, "mình muốn tự tử")
    assert khung_hoang["gate"] == "ESCALATE"
    assert khung_hoang["message_type"] == "CRISIS_CARD"
    assert khung_hoang["tokens"] == 0, "ESCALATE không được gọi LLM"
    assert khung_hoang["card"]["type"] == "CRISIS_CARD"
    assert khung_hoang["chips"] == [], "CRISIS_CARD không kèm quick reply"

    ov = await get_store().get(sid)
    assert ov.crisis_shown is True
    assert ov.active_cycles == ["cycle-tu-phe-phan"], (
        "ESCALATE không được xoá evidence/cycle đã có — chỉ cắt ngang LƯỢT này"
    )


# ═══════════════════════════════════════════════════════════════════════
# 4 — VAN CHỐNG GIẬM CHÂN (GĐ4)
# ═══════════════════════════════════════════════════════════════════════
@pytest.mark.asyncio
async def test_4_chat_long_vong_thoat_duoc_qua_orient():
    """Trước GĐ4: overlay rỗng nhiều lượt thì CLARIFY hỏi mở mãi, không có
    lối ra. Sau GĐ4: tới lượt 2 rỗng phải bật ORIENT, kèm chip chủ đề TẤT
    ĐỊNH — bấm vào phải thoát được bế tắc ngay lượt kế, không lặp lại ORIENT.
    """
    sid = await _phien_moi()

    l1 = await _mot_luot(sid, "chào bạn")
    assert l1["gate"] == "CLARIFY"           # lượt đầu chưa tính là bế tắc

    l2 = await _mot_luot(sid, "cũng không có gì đâu")
    assert l2["gate"] == "ORIENT"
    assert len(l2["chips"]) == 4
    for c in l2["chips"]:
        assert not _tien_to_he_thong(c), (
            f"chip ORIENT {c!r} không được mang tiền tố hệ thống — mang vào là "
            "detect_chip() bắt được và runner BỎ QUA bước trích, bấm xong vẫn kẹt"
        )

    l3 = await _mot_luot(sid, l2["chips"][1])          # "Mình có chuyện tình cảm"
    assert l3["gate"] == "CLARIFY"
    assert l3["gate"] != "ORIENT", "bấm chip xong phải thoát bế tắc, không lặp thực đơn"

    ov = await get_store().get(sid)
    assert ov.evidence, "chip chủ đề bấm xong phải để lại ít nhất một node bằng chứng"
    assert ov.stall_streak == 0


# ═══════════════════════════════════════════════════════════════════════
# 5 — BIÊN TỪ CHỐI KHÔNG ĐƯỢC LÀM HỎNG TRẠNG THÁI SAU ĐÓ
# ═══════════════════════════════════════════════════════════════════════
@pytest.mark.asyncio
async def test_5_tu_choi_ngoai_pham_vi_khong_lam_hong_luot_sau():
    """Lượt từ chối CỐ Ý bỏ qua bước trích bằng chứng (docx: refusal dùng
    prompt riêng, không phải CLARIFY thật). Nguy cơ thật: nếu chỗ này cài sai,
    một lượt từ chối có thể làm turn_count lệch, hoặc để lại rác trong
    overlay khiến lượt SAU đó suy luận sai. Test khoá: sau một lượt từ chối,
    một tin nhắn thật phải được xử lý như chưa từng có gì bất thường.
    """
    sid = await _phien_moi()

    tu_choi = await _mot_luot(sid, "giải bài tập toán này giùm mình với")
    assert tu_choi["gate"] == "REFUSAL"
    assert tu_choi["message_type"] == "REFLECT"
    assert tu_choi["chips"] == [], "lượt từ chối không kèm chip — chip sẽ thuộc về lượt SAI"

    ov_giua = await get_store().get(sid)
    assert ov_giua.evidence == {}, "lượt từ chối không được để lại evidence bịa"
    assert ov_giua.turn_count == 1

    binh_thuong = await _mot_luot(sid, "mình dở quá, lúc nào cũng làm sai hết")
    assert binh_thuong["gate"] != "REFUSAL"
    assert binh_thuong["gate"] in {"CLARIFY", "REFLECT"}

    ov = await get_store().get(sid)
    assert ov.turn_count == 2, "turn_count phải tăng đều, không bị lượt từ chối làm lệch"
    assert "m-tu-trach" in ov.evidence, "lượt thật SAU từ chối phải trích bình thường"
