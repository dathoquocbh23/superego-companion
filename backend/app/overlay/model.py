"""Mô hình bằng chứng + overlay. docx/03 §1–§3, docx/11 phần D2."""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field

from app.config import settings


class EvidenceSource(str, Enum):
    REMEMBERED = "REMEMBERED"   # nạp từ bộ nhớ dài hạn của phiên TRƯỚC
    LIKERT = "LIKERT"
    SELF_REPORT = "SELF_REPORT"
    INFERRED = "INFERRED"
    CONFIRMED = "CONFIRMED"


# Thứ tự mạnh dần — dùng khi merge.
# REMEMBERED YẾU NHẤT, yếu hơn cả INFERRED: bất cứ điều gì học sinh nói HÔM NAY
# đều đè được lên thứ bot nhớ từ tháng trước. Người ta có quyền đổi khác đi.
_SOURCE_RANK = {
    EvidenceSource.REMEMBERED: -1,
    EvidenceSource.INFERRED: 0,
    EvidenceSource.LIKERT: 1,
    EvidenceSource.SELF_REPORT: 2,
    EvidenceSource.CONFIRMED: 3,
}

# Confidence khởi tạo theo nguồn. docx/03 §3
LIKERT_CONFIDENCE = {5: 0.80, 4: 0.65, 3: 0.40, 2: 0.15, 1: 0.15, 0: 0.0}
SELF_REPORT_INIT = 0.75
CONFIRMED_INIT = 0.95


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Evidence(BaseModel):
    node_id: str
    confidence: float
    source: EvidenceSource
    turn_ids: list[int] = Field(default_factory=list)
    verbatim: str = ""            # ⚠️ BẮT BUỘC với SELF_REPORT / CONFIRMED
    updated_at: datetime = Field(default_factory=_now)

    @property
    def can_be_spoken(self) -> bool:
        """INFERRED tuyệt đối không được phát ngôn. docx/03 §2.

        REMEMBERED cũng không: bot mở lời bằng "lần trước bạn thấy mình kém
        cỏi" là vừa mớm vừa dựng lại một phiên bản cũ của người ta. Bộ nhớ chỉ
        dùng để bot BIẾT NÊN HỎI GÌ, không bao giờ để khẳng định.
        """
        return self.source not in (EvidenceSource.INFERRED, EvidenceSource.REMEMBERED)

    def cap(self) -> float:
        if self.source == EvidenceSource.REMEMBERED:
            return settings.memory_seed_confidence_cap
        if self.source == EvidenceSource.INFERRED:
            return settings.extract_confidence_cap
        if self.source == EvidenceSource.SELF_REPORT:
            return settings.self_report_confidence_cap
        return 1.0


class Overlay(BaseModel):
    session_id: str
    # Chủ phiên, nếu đã đăng nhập. None = phiên ẩn danh (mặc định, docx/00 §4).
    user_id: str | None = None
    memory_seeded: bool = False
    # Hàng `conversations` của phiên này trên Supabase (GĐ6). None = chưa tạo
    # được hoặc tính năng đang tắt — mọi chỗ dùng đều phải chịu được None.
    conversation_id: str | None = None
    evidence: dict[str, Evidence] = Field(default_factory=dict)
    active_cycles: list[str] = Field(default_factory=list)
    turn_count: int = 0
    gates_used: list[str] = Field(default_factory=list)
    bridge_offered: bool = False
    has_taken_assessment: bool = False
    # Kết quả bài Likert, giữ để MỌI lượt sau còn nhắc lại được (bug 09/09/2026:
    # trước đây chỉ có cờ boolean nên bot quên sạch bài test ngay lượt kế tiếp).
    # Cả hai đều là chữ NGUYÊN VĂN của assessment.yaml.
    assessment_band_label: str | None = None
    assessment_headline: str | None = None
    assessment_average: float | None = None
    # Đã hỏi vào kết quả bài test chưa. Một lần thôi: hỏi mãi về cùng một câu
    # Likert là kiểu giậm chân khó chịu nhất, vì nó có vẻ như bot đang truy bài.
    assessment_debriefed: bool = False
    crisis_shown: bool = False
    # node bị né tạm thời sau CHIP_DECLINE: node_id -> lượt được phép hỏi lại
    suppressed_nodes: dict[str, int] = Field(default_factory=dict)
    # ── Chống giậm chân (GĐ4, 07/09/2026) ─────────────────────────────
    # Kích thước overlay ở CUỐI lượt trước, và số lượt liên tiếp nó KHÔNG lớn
    # thêm. Ngày 07/09/2026 quan sát được 4 lượt CLARIFY liền với overlay rỗng
    # suốt: hệ thống không có cách nào tự biết mình đang chạy không tải.
    evidence_size_prev: int = 0
    stall_streak: int = 0
    # ── Chế độ chủ đề (docx/13, 09/09/2026) ───────────────────────────
    # `topic_id` None = vào bằng ô nhập, không qua thẻ chủ đề nào.
    topic_id: str | None = None
    topic_opened: bool = False        # đã phát thẻ mở đầu của chủ đề chưa
    # Số lượt ở chế độ TÌM HIỂU (mở chủ đề + bấm chip kiến thức). Trừ ra khi
    # xét giậm chân: chip TÌM HIỂU không mang cue nên overlay đứng yên, nhưng
    # đó KHÔNG phải hội thoại chết máy — người dùng đang đọc đúng thứ họ vừa
    # bấm hỏi. Không trừ thì tới lượt 2 bot đã xin lỗi "mình hỏi hơi lòng
    # vòng". Xem docx/03 §5 `bi_giam_chan()` và docx/14 ⚠️ A-1.
    luot_tim_hieu: int = 0
    # Thẻ nội dung đã phát trong phiên này, theo thứ tự. Dùng để XOAY chip TÌM
    # HIỂU: chủ đề có tới 6 chip mà mỗi lượt chỉ hiện được 3, nên chip chưa đọc
    # phải lên trước. Xem pipeline/quick_reply.py.
    the_da_xem: list[str] = Field(default_factory=list)
    # docx/11 §E5 — lượt sớm nhất được phép REFLECT lại sau một "Đúng một phần".
    reflect_locked_until: int = 0
    # docx/11 D7 — dáng câu hỏi của vài lượt gần nhất, để không hỏi lại một kiểu.
    dang_da_dung: list[str] = Field(default_factory=list)
    # docx/11 D10 — node CLARIFY đang nhắm và số lượt đã hỏi mà chưa ra gì.
    target_truoc: str | None = None
    target_hoi_lai: int = 0
    # lịch sử hội thoại tạm (chỉ để dựng prompt — KHÔNG BAO GIỜ ghi log).
    # sống cùng overlay trong Redis, tự hết hạn sau TTL.
    history: list[dict[str, str]] = Field(default_factory=list)

    def push_history(self, role: str, text: str, keep: int = 10) -> None:
        self.history.append({"role": role, "text": text})
        if len(self.history) > keep:
            self.history[:] = self.history[-keep:]

    def recent_turns_text(self, n: int = 5) -> str:
        rows = self.history[-(n * 2):]
        if not rows:
            return ""
        label = {"user": "Học sinh", "assistant": "Bot"}
        return "\n".join(f"{label.get(r['role'], r['role'])}: {r['text']}" for r in rows)

    # ---- helpers -----------------------------------------------------
    def has(self, node_id: str) -> bool:
        return node_id in self.evidence

    def confidence(self, node_id: str) -> float:
        e = self.evidence.get(node_id)
        return e.confidence if e else 0.0

    def is_confirmed(self, node_id: str) -> bool:
        e = self.evidence.get(node_id)
        return bool(e and e.source == EvidenceSource.CONFIRMED)

    def confidences(self) -> dict[str, float]:
        return {nid: e.confidence for nid, e in self.evidence.items()}

    def verbatims(self) -> dict[str, str]:
        return {nid: e.verbatim for nid, e in self.evidence.items() if e.verbatim}

    def speakable_verbatims(self) -> dict[str, str]:
        return {
            nid: e.verbatim
            for nid, e in self.evidence.items()
            if e.verbatim and e.can_be_spoken
        }

    # ---- mutation --------------------------------------------------
    def merge(self, incoming: Evidence) -> None:
        """docx/03 §3 — 3 trường hợp merge."""
        incoming.confidence = min(incoming.confidence, incoming.cap())
        cur = self.evidence.get(incoming.node_id)
        if cur is None:
            self.evidence[incoming.node_id] = incoming
            return

        cur_rank = _SOURCE_RANK[cur.source]
        new_rank = _SOURCE_RANK[incoming.source]
        merged_turns = sorted(set(cur.turn_ids) | set(incoming.turn_ids))

        if new_rank > cur_rank:
            incoming.turn_ids = merged_turns
            if not incoming.verbatim:
                incoming.verbatim = cur.verbatim
            self.evidence[incoming.node_id] = incoming
        elif new_rank == cur_rank:
            cur.confidence = min(max(cur.confidence, incoming.confidence), cur.cap())
            cur.turn_ids = merged_turns
            if incoming.verbatim:
                cur.verbatim = incoming.verbatim
            cur.updated_at = _now()
        else:  # yếu hơn → chỉ nối turn_ids
            cur.turn_ids = merged_turns
            cur.updated_at = _now()

    def promote_confirmed(self, node_ids: list[str], turn_id: int) -> None:
        for nid in node_ids:
            cur = self.evidence.get(nid)
            vb = cur.verbatim if cur else ""
            turns = sorted(set((cur.turn_ids if cur else []) + [turn_id]))
            self.evidence[nid] = Evidence(
                node_id=nid,
                confidence=CONFIRMED_INIT,
                source=EvidenceSource.CONFIRMED,
                turn_ids=turns,
                verbatim=vb,
            )

    def promote_partial(self, node_ids: list[str], turn_id: int) -> None:
        """"Đúng một phần" — nâng vừa phải, KHÔNG đổi source. docx/11 §E5.

        Khác promote_confirmed() ở đúng chỗ quan trọng nhất: source vẫn là
        SELF_REPORT, nên `confirmed_ids` ở decide_gate vẫn rỗng và gate SUPPORT
        không mở. Họ mới nói "gần đúng", chưa nói "đúng".
        """
        for nid in node_ids:
            cur = self.evidence.get(nid)
            if cur is None:
                continue
            cur.confidence = max(cur.confidence, settings.partial_confirm_confidence)
            cur.turn_ids = sorted(set(cur.turn_ids + [turn_id]))
            cur.updated_at = _now()

    def lower_confidence(self, node_ids: list[str], delta: float = 0.3) -> None:
        for nid in node_ids:
            cur = self.evidence.get(nid)
            if cur:
                cur.confidence = max(0.0, cur.confidence - delta)
                cur.updated_at = _now()

    def so_node_noi_duoc(self) -> int:
        """Số node bot THẬT SỰ dùng được để phản chiếu.

        Khác `len(self.evidence)`: node `INFERRED` / `REMEMBERED` đếm vào tổng
        nhưng bot không được nói ra chúng, nên overlay phình lên mà hội thoại
        vẫn đứng yên. Đo giậm chân bằng tổng là đo nhầm — xem docx/11 D8.
        """
        return sum(1 for e in self.evidence.values() if e.can_be_spoken)

    def ghi_dang(self, dang: str, keep: int = 3) -> None:
        self.dang_da_dung.append(dang)
        if len(self.dang_da_dung) > keep:
            self.dang_da_dung[:] = self.dang_da_dung[-keep:]

    def by_source_counts(self) -> dict[str, int]:
        out = {s.value: 0 for s in EvidenceSource}
        for e in self.evidence.values():
            out[e.source.value] += 1
        return out
