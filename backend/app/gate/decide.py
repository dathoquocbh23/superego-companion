"""
Thuật toán 5 gate — luật cứng trên trạng thái graph. docx/03 §4–§5.

Ưu tiên (docx/11 phần D1 — ĐÃ SỬA):
    ESCALATE  >  BRIDGE  >  SUPPORT  >  REFLECT  >  CLARIFY (mặc định)

LLM chỉ DIỄN ĐẠT quyết định này, không tự chọn gate.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.config import settings
from app.graph.loader import GraphService
from app.overlay.model import EvidenceSource, Overlay
from app.safety.crisis import SafetyResult
from app.safety.chips import ChipSignal

ESCALATE = "ESCALATE"
ORIENT = "ORIENT"
BRIDGE = "BRIDGE"
SUPPORT = "SUPPORT"
REFLECT = "REFLECT"
CLARIFY = "CLARIFY"

GATE_PRIORITY = [ESCALATE, BRIDGE, SUPPORT, REFLECT, ORIENT, CLARIFY]

# ORIENT — van xả cho trường hợp CLARIFY chạy không tải. Xem _bi_giam_chan().
ORIENT_MIN_TURN = 2      # overlay rỗng tới lượt này thì thôi hỏi mò
STALL_LIMIT = 3          # số lượt CLARIFY liên tiếp không thu thêm được gì

# D5 — số node tối thiểu trong overlay trước khi được nhắm vào node `late_stage`.
LATE_STAGE_MIN_EVIDENCE = 3

# D10 — hỏi bao nhiêu lượt liền về CÙNG một node mà vẫn không có bằng chứng thì
# thôi, chuyển sang node khác. Không có luật này thì `highest_information_gain`
# trả về đúng node đó mọi lượt (nó vẫn là node "thiếu thông tin nhất"), và bot
# hỏi vòng quanh một chỗ — quan sát thật 08/09/2026: 5 lượt liền nhắm
# `m-tieu-chuan-cao`.
TARGET_HOI_LAI_TOI_DA = 2
TARGET_NE_TRONG = 3          # số lượt né node đó sau khi bỏ cuộc

# D5 — khoá phụ khi điểm information gain bằng nhau.
#
# Thứ tự PHỤ THUỘC vào việc đã có bối cảnh hay chưa (sửa 08/09/2026):
#
#   chưa có trigger nào  -> hỏi bối cảnh trước: trigger > manifestation > affect > impact
#   ĐÃ có trigger        -> đào sâu chỗ đang đứng: manifestation > affect > impact > trigger
#
# Vì sao: bản đầu để trigger đứng nhất vô điều kiện. Học sinh nói về điểm số,
# LLM suy ra `m-chua-du-tot`, mà node đó có cạnh sang `t-quan-he` — thế là
# frontier có một trigger mới và bot quay sang hỏi CHUYỆN TÌNH CẢM giữa một
# cuộc nói chuyện về bài kiểm tra. Đã có bối cảnh rồi thì việc cần làm là hiểu
# họ ĐỐI XỬ VỚI MÌNH thế nào trong bối cảnh đó — đúng thứ tài liệu nghiên cứu
# mô tả — chứ không phải đi thu thập thêm một bối cảnh nữa.
_TYPE_RANK_CHUA_CO_BOI_CANH = {"trigger": 0, "manifestation": 1, "affect": 2, "impact": 3}
_TYPE_RANK_DA_CO_BOI_CANH = {"manifestation": 0, "affect": 1, "impact": 2, "trigger": 3}


@dataclass
class GateDecision:
    gate: str
    reason: str
    target_nodes: list[str] = field(default_factory=list)
    mode: str | None = None                 # REFLECT: "single" | "cycle"
    resource_node: str | None = None        # BRIDGE
    coping_node: str | None = None          # SUPPORT
    concept_node: str | None = None         # SUPPORT
    policy_edge_used: str | None = None     # "from->to"
    extra: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
def _impact_count(graph: GraphService, overlay: Overlay) -> int:
    thr = settings.confidence_threshold
    return sum(
        1
        for nid, e in overlay.evidence.items()
        if (n := graph.node(nid)) and n.type == "impact" and e.confidence >= thr
    )


def _condition_met(cond: dict[str, Any] | None, overlay: Overlay) -> bool:
    if not cond:
        return True
    thr = settings.confidence_threshold
    if "any_of" in cond:
        return any(overlay.confidence(x) >= thr or overlay.has(x) for x in cond["any_of"])
    if "all_of" in cond:
        return all(overlay.confidence(x) >= thr or overlay.has(x) for x in cond["all_of"])
    return True


def resolve_policy_edge(graph: GraphService, overlay: Overlay) -> tuple[str, str | None]:
    """8 policy edge + điều kiện κ. docx/03 §5.

    Trả (coping_node_id, "from->to" | None). Fallback → default_coping.
    """
    candidates = []
    for e in graph.policy_edges():
        src_conf = overlay.confidence(e.from_)
        has_src = overlay.has(e.from_)
        if not has_src and src_conf <= 0:
            continue
        if not _condition_met(e.condition, overlay):
            continue
        candidates.append((e.priority or 0, src_conf, e))
    if not candidates:
        return graph.default_coping, None
    candidates.sort(key=lambda t: (t[0], t[1]), reverse=True)
    best = candidates[0][2]
    return best.to, f"{best.from_}->{best.to}"


def _concept_for_confirmed(graph: GraphService, confirmed_ids: list[str]) -> str | None:
    for nid in confirmed_ids:
        expl = graph.explained_by(nid)
        if expl:
            return expl[0]
    return None


def _hop_le_lam_target(graph: GraphService, overlay: Overlay, nid: str) -> bool:
    """Node này có được phép làm target của CLARIFY không.

    D5 — thêm luật `late_stage`: node mang phán quyết về giá trị bản thân
    (`m-dang-bi-trach-phat`, `m-co-loi-ky-vong`, `m-xau-ho-khuyet-diem`) bị cấm
    làm target khi overlay còn dưới LATE_STAGE_MIN_EVIDENCE node. Ngày
    08/09/2026 quan sát được: lượt 1, overlay đúng 1 node (`t-diem-so`), bot
    nhắm `m-dang-bi-trach-phat` rồi nói thẳng ra "nghe như bạn đang thấy mình
    đáng bị trách phạt".
    """
    node = graph.node(nid)
    if node is None or not node.is_evidence or node.risk_adjacent:
        return False
    if nid in overlay.suppressed_nodes and overlay.turn_count < overlay.suppressed_nodes[nid]:
        return False
    if node.late_stage and len(overlay.evidence) < LATE_STAGE_MIN_EVIDENCE:
        return False
    return True


def highest_information_gain_node(graph: GraphService, overlay: Overlay) -> str | None:
    """Chọn node để hỏi (gate CLARIFY). docx/03 §5, docx/11 D5.

    Ưu tiên node: (1) hàng xóm của node đã có evidence, (2) confidence thấp/chưa có,
    (3) nằm trên cycle mà các node khác đã sáng ≥ 2. Bỏ node risk_adjacent và node bị né.

    ⚠️ Khoá sắp xếp phải TẤT ĐỊNH tới tận phần tử cuối. Bản cũ trả về bộ ba
    `(on_hot_cycle, low, -cur)` rồi `sorted(reverse=True)`: ở lượt 1 cả 4 hàng
    xóm của `t-diem-so` cùng điểm `(0, 1, -0.0)`, nên thứ tự thực tế là thứ tự
    duyệt `set` — tức là đổi theo PYTHONHASHSEED, mỗi lần khởi động một khác.
    Ba khoá phụ dưới đây (type · likert_item · id) đảm bảo cùng input ra cùng
    target, mọi lần chạy.
    """
    if not overlay.evidence:
        return None

    thr = settings.confidence_threshold
    known = set(overlay.evidence)
    frontier: set[str] = set()
    for nid in known:
        frontier |= graph.neighbors(nid)
    frontier -= known

    # Node có cạnh CHẠY VÀO một node đã biết — xem khoá `nguoc_dong` dưới.
    _tien_de = {e.from_ for e in graph.edges if e.to in known and e.from_ in frontier}

    da_co_boi_canh = any(
        (n := graph.node(nid)) and n.type == "trigger" for nid in known
    )
    rank = _TYPE_RANK_DA_CO_BOI_CANH if da_co_boi_canh else _TYPE_RANK_CHUA_CO_BOI_CANH

    def khoa(nid: str) -> tuple:
        node = graph.node(nid)
        assert node is not None                      # đã lọc ở _hop_le_lam_target
        cur = overlay.confidence(nid)
        cyc = graph.cycle_for(nid)
        on_hot_cycle = 0
        if cyc:
            lit = sum(
                1 for x in cyc.nodes
                if x != nid and overlay.confidence(x) >= settings.cycle_activation_confidence
            )
            on_hot_cycle = 1 if lit >= 2 else 0
        low = 1 if cur < thr else 0
        # Hỏi ĐIỀU KIỆN trước, hỏi HỆ QUẢ sau. Node có cạnh ĐI VÀO node đã biết
        # (m-tieu-chuan-cao -> t-diem-so) là thứ có sẵn từ trước; node ở đầu ra
        # (t-diem-so -> m-tu-trach) là phản ứng — hỏi vào nó là đã ngầm cho rằng
        # phản ứng đó có xảy ra.
        nguoc_dong = 0 if nid in _tien_de else 1
        # Sắp XUÔI: dấu trừ ở hai khoá đầu vì "cao hơn = tốt hơn".
        return (
            -on_hot_cycle,
            -low,
            cur,
            rank.get(node.type, 9),
            nguoc_dong,
            node.likert_item if node.likert_item is not None else 99,
            nid,
        )

    ung_vien = [n for n in frontier if _hop_le_lam_target(graph, overlay, n)]
    if not ung_vien:
        return None
    return min(ung_vien, key=khoa)


# ---------------------------------------------------------------------------
def decide_gate(
    graph: GraphService,
    overlay: Overlay,
    safety: SafetyResult,
    chip: ChipSignal | None,
) -> GateDecision:
    # ── 0. CHIP (ý định đã biết chắc) ─────────────────────────────────
    if chip is not None:
        if chip.chip_type == "CONFIRM_NO":
            return GateDecision(
                gate=CLARIFY, reason="chip_confirm_no",
                target_nodes=[x for x in overlay.active_cycles] or [],
            )
        if chip.chip_type == "CONFIRM_PARTIAL":
            # docx/11 §E5 — "Đúng một phần" đi thẳng sang CLARIFY để hỏi CHỖ
            # NÀO chưa đúng. KHÔNG sang SUPPORT: chưa có gì CONFIRMED cả.
            return GateDecision(
                gate=CLARIFY, reason="chip_confirm_partial",
                target_nodes=[x for x in overlay.active_cycles] or [],
            )
        if chip.chip_type == "DECLINE":
            return GateDecision(gate=CLARIFY, reason="chip_decline")
        # CONFIRM_YES / ASK rơi xuống luồng chính (overlay đã cập nhật ở step trước)

    # ── 1. AN TOÀN ───────────────────────────────────────────────────
    if safety.forces_escalate:
        return GateDecision(gate=ESCALATE, reason=f"safety_tier_{safety.tier}")

    # ── 2. BẮC CẦU ──────────────────────────────────────────────────
    impacts = _impact_count(graph, overlay)
    vo_vong_confirmed = overlay.is_confirmed("a-vo-vong")
    if safety.forces_bridge or impacts >= 2 or overlay.has("r-keo-dai") or vo_vong_confirmed:
        if not overlay.bridge_offered:
            res = _pick_resource(graph, overlay)
            reason = (
                "safety_tier_3" if safety.forces_bridge
                else "vo_vong_confirmed" if vo_vong_confirmed
                else "keo_dai" if overlay.has("r-keo-dai")
                else "suy_giam_chuc_nang"
            )
            return GateDecision(
                gate=BRIDGE, reason=reason, resource_node=res,
                target_nodes=[res],
            )

    # ── 3. HỖ TRỢ (chỉ khi đã REFLECT + có CONFIRMED) ────────────────
    confirmed_ids = [
        nid for nid, e in overlay.evidence.items() if e.source == EvidenceSource.CONFIRMED
    ]
    if confirmed_ids and REFLECT in overlay.gates_used and SUPPORT not in _recent_gates(overlay, 1):
        coping, edge = resolve_policy_edge(graph, overlay)
        return GateDecision(
            gate=SUPPORT, reason="confirmed_after_reflect",
            target_nodes=[coping],
            coping_node=coping,
            concept_node=_concept_for_confirmed(graph, confirmed_ids),
            policy_edge_used=edge,
        )

    # ── 4. PHẢN CHIẾU ──────────────────────────────────────────────
    #     Bị khoá sau một "Đúng một phần": cycle vẫn sáng ở 0.80 nên nếu không
    #     khoá, lượt ngay sau đó bot dựng lại y hệt cái thẻ họ vừa nói là chưa
    #     đúng hẳn (docx/11 §E5).
    reflect_bi_khoa = overlay.turn_count < overlay.reflect_locked_until
    # D11 — REFLECT là một CÂU HỎI đang chờ trả lời. Người dùng trả lời bằng
    # lời (không bấm chip) thì việc tiếp theo là ĐỌC lời đó, không phải hỏi lại
    # đúng câu cũ. Không có luật này thì `active_cycles` vẫn sáng và `_cycle_done`
    # vẫn False (nó đòi đã đi qua SUPPORT), nên gate REFLECT nổ lại mọi lượt và
    # bot dựng lại y hệt cái thẻ — quan sát thật 08/09/2026, lượt 4 và lượt 5.
    if chip is None and REFLECT in _recent_gates(overlay, 1):
        reflect_bi_khoa = True

    if (
        not reflect_bi_khoa
        and overlay.active_cycles
        and not _cycle_done(graph, overlay, overlay.active_cycles[0])
    ):
        return GateDecision(
            gate=REFLECT, reason="cycle_activated", mode="cycle",
            target_nodes=[overlay.active_cycles[0]],
        )

    thr = settings.confidence_threshold
    strong = [
        nid for nid, e in overlay.evidence.items()
        if e.confidence >= thr and e.source in (EvidenceSource.SELF_REPORT, EvidenceSource.LIKERT)
    ]
    if not reflect_bi_khoa and len(strong) >= settings.min_nodes_for_reflect:  # D3
        strong.sort(key=lambda x: overlay.confidence(x), reverse=True)
        return GateDecision(
            gate=REFLECT, reason="min_nodes_reached", mode="single",
            target_nodes=strong[:3],
        )

    # ── 4b. ĐỊNH HƯỚNG LẠI (van chống giậm chân) ─────────────────
    if _bi_giam_chan(overlay):
        return GateDecision(
            gate=ORIENT,
            reason="empty_overlay_stalled" if not overlay.evidence else "clarify_stalled",
        )

    # ── 5. MẶC ĐỊNH: LÀM RÕ ───────────────────────────────────────
    target = highest_information_gain_node(graph, overlay)
    return GateDecision(
        gate=CLARIFY,
        reason="default" if overlay.evidence else "empty_overlay",
        target_nodes=[target] if target else [],
    )


def _bi_giam_chan(overlay: Overlay) -> bool:
    """Hội thoại đang chạy không tải — CLARIFY thêm lượt nữa cũng vô ích.

    Hai kiểu giậm chân, đều quan sát được thật ngày 07/09/2026:

      a) Overlay không có node NÓI ĐƯỢC nào qua nhiều lượt. Bot không nhắm
         được vào đâu, nên chỉ còn hỏi mở chung chung — "Điều gì đang diễn ra
         trong bạn lúc này?" ba lượt liền.
      b) Overlay có thứ gì đó nhưng KHÔNG lớn thêm sau 3 lượt CLARIFY liên
         tiếp. Câu hỏi vẫn đúng luật, chỉ là không moi thêm được gì.

    ⚠️ Cả hai đo trên `so_node_noi_duoc()`, KHÔNG phải `len(evidence)` (sửa
    08/09/2026). Bằng chứng LLM suy ra làm overlay phình lên mà bot không nói
    ra được gì — đo bằng tổng thì van xả này tưởng hội thoại đang tiến triển và
    không bao giờ mở. Quan sát thật: 5 lượt liền, overlay 4 node, đúng 1 node
    nói được, bot hỏi "kể thêm một lần cụ thể" tới lượt thứ năm.

    Điều kiện (b) bắt buộc phải kèm "3 lượt vừa rồi đều là CLARIFY": một hội
    thoại đang đi qua REFLECT → SUPPORT cũng không tăng evidence, nhưng nó đang
    tiến triển hoàn toàn bình thường, cắt ngang là hỏng.
    """
    # Vừa đưa menu xong thì thôi, đừng đưa hai lần liền.
    if overlay.gates_used and overlay.gates_used[-1] == ORIENT:
        return False
    if not overlay.so_node_noi_duoc():
        return overlay.turn_count >= ORIENT_MIN_TURN
    gan_day = overlay.gates_used[-STALL_LIMIT:]
    ket_o_clarify = len(gan_day) == STALL_LIMIT and all(g == CLARIFY for g in gan_day)
    return ket_o_clarify and overlay.stall_streak >= STALL_LIMIT


def _recent_gates(overlay: Overlay, n: int) -> list[str]:
    return overlay.gates_used[-n:] if overlay.gates_used else []


def _cycle_done(graph: GraphService, overlay: Overlay, cycle_id: str) -> bool:
    """Cycle đã được phản chiếu + xác nhận + đã đi qua SUPPORT → thôi nhắc lại."""
    if "SUPPORT" not in overlay.gates_used:
        return False
    cyc = next((c for c in graph.cycles if c.id == cycle_id), None)
    if cyc is None:
        return False
    evidenced = [n for n in cyc.nodes if overlay.has(n)]
    return bool(evidenced) and all(overlay.is_confirmed(n) for n in evidenced)


def _pick_resource(graph: GraphService, overlay: Overlay) -> str:
    """Chọn resource cho BRIDGE. docx/03 §5 — ưu tiên ba mẹ (có kịch bản mở lời)."""
    thr = settings.confidence_threshold
    if overlay.has("r-keo-dai"):
        for nid in graph.escalates_to("r-keo-dai"):
            return nid
    for src in ("r-suy-giam-chuc-nang", "a-vo-vong", "i-thu-minh"):
        if overlay.confidence(src) >= thr or overlay.has(src):
            targets = graph.escalates_to(src)
            if targets:
                return targets[0]
    return graph.bridge.default_resource
