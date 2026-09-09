"""
MỘT LƯỢT = MỘT LỜI GỌI LLM. GĐ2, 07/09/2026.

Thay cho 3 lời gọi cũ (extract -> speak -> quickreply), mỗi lời gọi kéo theo
một bản sao CORE_PERSONA:

    trước:  6.591 + 9.542 + 6.099 = 22.232 byte system prompt / lượt (~7.4k token)
    sau:    1 lời gọi, CORE nạp 1 lần, catalog bỏ cue      (~3.1k token)

Việc gì đi đâu:
  - khớp cue hiển nhiên  -> app/evidence/matcher.py, TẤT ĐỊNH, 0 token, chạy TRƯỚC gate
  - nói + sinh chip + suy ra evidence -> lời gọi DUY NHẤT ở đây
  - lọc an toàn chip     -> _chip_an_toan() dưới đây (giữ nguyên luật của
                            app/llm/quickreply.py cũ, file đó đã xoá)

Đánh đổi đã cân nhắc: evidence LLM SUY RA có hiệu lực từ lượt SAU, vì nó về
cùng lúc với câu trả lời chứ không phải trước. Chấp nhận được — cue tất định đã
bắt ngay lượt này mọi thứ học sinh nói thẳng; phần trễ chỉ là suy diễn.
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field

from pydantic import BaseModel, Field, ValidationError

from app.config import settings
from app.gate.decide import BRIDGE, CLARIFY, ORIENT, REFLECT, SUPPORT, GateDecision
from app.gate.directive import build_directive, chon_dang_cau_hoi
from app.graph.likert import likert_text_by_node
from app.graph.loader import GraphService
from app.overlay.model import Evidence, EvidenceSource, Overlay
from app.safety.crisis import check_crisis
from app.safety.normalize import normalize_vi
from app.skills.loader import SkillLoader

logger = logging.getLogger(__name__)

_FENCE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)
_OBJ = re.compile(r"\{.*\}", re.DOTALL)

# Cụm bị chặn trong chip (đã bỏ dấu) — chẩn đoán / tự hại / tuyệt vọng.
# Giữ nguyên từ app/llm/quickreply.py: chip là thứ học sinh BẤM, tức là hệ
# thống đặt chữ vào miệng họ. Mớm triệu chứng ở đây nguy hiểm hơn ở câu trả lời.
_CHIP_CAM = [
    "tram cam", "lo au", "roi loan", "benh", "chan doan",
    "vo dung", "vo vong", "tuyet vong", "vo gia tri", "khong dang song",
    "muon chet", "tu tu", "tu hai", "bo cuoc", "buong xuoi",
    "sieu toi", "cau toan",
    # docx/11 §E7 — bổ sung 08/09/2026. Chip "Mình thấy mình kém cỏi" lọt qua
    # danh sách cũ vì nó chỉ chặn "vo dung"/"vo gia tri". Chip là thứ học sinh
    # BẤM: để nó tự dán một nhãn nặng lên mình còn tệ hơn bot nói câu đó.
    "kem coi", "do te", "te hai", "that bai", "chang ra gi", "vo tich su",
    "khong ra gi", "thua kem", "bat tai",
]


# ---------------------------------------------------------------------------
@dataclass
class TurnPrompt:
    skill: str
    system: str
    user: str
    max_tokens: int
    temperature: float
    che_do_cycle: bool = False


@dataclass
class TurnOutput:
    reply: str = ""
    chips: list[str] = field(default_factory=list)
    evidence: list[Evidence] = field(default_factory=list)
    lines: list[str] = field(default_factory=list)
    closing: str = ""
    flags: list[str] = field(default_factory=list)


class _RawEvidence(BaseModel):
    node_id: str
    confidence: float = Field(ge=0.0, le=1.0)
    verbatim: str = ""
    mapping: str = "inferential"


# ---------------------------------------------------------------------------
def node_catalog(graph: GraphService) -> str:
    """Danh sách `id | label` — CỐ Ý bỏ cue.

    Cue là gợi ý TỪ VỰNG cho regex ở evidence/matcher.py. Nhét chúng vào prompt
    tốn 4.366 byte mỗi lượt để dạy mô hình thứ nó vốn đã hiểu từ nhãn: đọc
    "Chuyện tình cảm" là đủ, không cần liệt kê 10 cách nói về chia tay.
    """
    rows = []
    for nid in graph.evidence_node_ids:
        n = graph.node(nid)
        if n:
            rows.append(f"- {nid} | {n.label}")
    return "\n".join(rows)


def _verbatim_list(overlay: Overlay, node_ids: list[str] | None = None) -> str:
    vbs = overlay.speakable_verbatims()
    if node_ids:
        picked = [vbs[n] for n in node_ids if n in vbs]
        if picked:
            return " · ".join(f'"{v}"' for v in picked)
    return " · ".join(f'"{v}"' for v in vbs.values()) or "(chưa có)"


def _memory_quotes_block(overlay: Overlay, graph: GraphService) -> str:
    from app.memory.service import memory_quotes

    quotes = memory_quotes(overlay, graph)
    if not quotes:
        return "(không có)"
    return "\n".join(f'- Về {label.lower()}: "{vb}"' for label, vb in quotes)


_CHIPS_CLARIFY_MAU = """từ **2 đến {toi_da}** câu trả lời NGẮN mà một học sinh THPT
  có thể bấm để đáp lại chính câu hỏi bạn vừa viết trong `reply` — như thể
  chính họ gõ ra. Mỗi chip <= 8 từ, ngôi thứ nhất ("Mình…"), KHÔNG có dấu chấm
  cuối. Chip là câu TRẢ LỜI, không phải câu hỏi ngược.

  Viết theo VAI, đúng thứ tự này — hệ thống tự thêm chip thoát ở cuối:

  1. **vai A** — trả lời thẳng câu hỏi của bạn.        (luôn có)
  2. **vai B** — cũng trả lời câu đó, nhưng NGƯỢC CHIỀU A.  (luôn có)
  3. **vai C** — CHỈ khi câu `reply` của bạn có một GIẢ ĐỊNH về người dùng
     (bạn viết "nghe như bạn…", "có vẻ bạn…"). Chip này để họ nói giả định đó
     SAI. Ví dụ bot đoán chuyện điểm số thì vai C là "Không phải vì điểm".
  4. **vai D** — CHỈ khi bạn đang không chắc họ muốn nói về chuyện gì: một
     chip kéo sang hướng khác. Ví dụ: "Chuyện ở nhà mới mệt".

  🔴 A và B phải KHÁC HƯỚNG THẬT, không phải khác cường độ. "Mình thấy mình
  kém cỏi" và "Mình nghĩ mình chưa cố gắng" là CÙNG một hướng — cả hai đều bắt
  họ tự nhận mình kém, nên tính là MỘT chip. Đó là lỗi thật ngày 08/09/2026.
  🔴 TUYỆT ĐỐI không đưa vào chip một triệu chứng / cảm xúc tiêu cực mà người
  dùng CHƯA từng nói. Chỉ diễn đạt mức độ hoặc hướng đi của điều họ ĐÃ nói.
  🔴 Vai C và vai D là hai lối thoát — chúng phải SẠCH tuyệt đối, không mang
  bất kỳ chữ nào nói xấu người dùng."""

_CHIPS_KHONG = "để mảng rỗng `[]`. Lượt này hệ thống tự dựng chip, không cần bạn."

_EVIDENCE_CO = """phần bạn SUY RA từ tin nhắn hiện tại, ngoài những cụm hiển
  nhiên hệ thống đã tự khớp. Không có gì để thêm thì trả `[]`."""

_EVIDENCE_KHONG = "để mảng rỗng `[]`. Lượt này không ghi nhận bằng chứng."

_REPLY_CYCLE = """
  ⚠️ Lượt này KHÁC: để `reply` là chuỗi rỗng. Thay vào đó xuất thêm hai khoá —
  `lines` (mảng các câu nguyên văn, GIỮ NGUYÊN thứ tự đã cho, tối đa 5) và
  `closing` (một câu hỏi xác nhận). Hệ thống dựng thẻ từ hai khoá đó."""


def _khoi_bai_test(overlay: Overlay) -> str:
    """Kết quả bài Likert, dạng chữ, để nhét vào 00_CORE_PERSONA.

    Bug 09/09/2026: chỗ này từng chỉ trả "có" / "chưa". Mô hình biết CÓ một bài
    test mà không biết bài đó ra cái gì, nên lượt đầu sau bài test nó hỏi ngược
    "bạn đã đánh giá những gì vậy?" — người vừa trả lời xong 10 câu bị bắt kể
    lại chính 10 câu đó. Đúng nghĩa quên sạch.

    Mọi chữ trả về đều NGUYÊN VĂN assessment.yaml (band label, headline, phát
    biểu Likert) — không có câu nào do mô hình hay do đây tự nghĩ.

    CHỈ liệt kê câu họ chọn "Hoàn toàn đúng" (confidence 0.80). Mức 4 = 0.65,
    dưới ngưỡng 0.70 — xem docx/03 §3.1: "khá đúng" nghĩa là CHƯA CHẮC, đưa vào
    đây là biến một cú tick thành lời tự thú.
    """
    if not overlay.has_taken_assessment:
        return "chưa làm"

    dong = ["RỒI"]
    if overlay.assessment_band_label:
        muc = f'mức "{overlay.assessment_band_label}"'
        if overlay.assessment_average is not None:
            muc += f" (trung bình {overlay.assessment_average}/5)"
        dong.append(muc)
    dau = " — ".join(dong) + "."

    phat_bieu = likert_text_by_node()
    manh = [
        phat_bieu[nid]
        for nid, e in overlay.evidence.items()
        if e.source == EvidenceSource.LIKERT and e.confidence >= 0.80 and nid in phat_bieu
    ]
    if not manh:
        return dau + " Không câu nào họ chọn ở mức cao nhất."

    return dau + ' Những câu họ chọn "Hoàn toàn đúng":\n' + "\n".join(
        f"  • {c}" for c in manh
    )


def build_turn_prompt(
    *,
    skills: SkillLoader,
    graph: GraphService,
    overlay: Overlay,
    decision: GateDecision,
    user_message: str,
    recent_turns: str,
    cycle_ordered_verbatims: list[str] | None = None,
    refusal_situation: str | None = None,
    thu_evidence: bool = True,
    chip_toi_da: int = 3,
) -> TurnPrompt:
    """Dựng system prompt cho lời gọi DUY NHẤT của lượt này."""
    che_do_cycle = bool(
        decision.gate == REFLECT
        and decision.mode == "cycle"
        and cycle_ordered_verbatims
    )
    xin_chips = decision.gate == CLARIFY and refusal_situation is None

    chung = dict(
        TURN_COUNT=overlay.turn_count,
        HAS_TAKEN_ASSESSMENT=_khoi_bai_test(overlay),
        MEMORY_QUOTES=_memory_quotes_block(overlay, graph),
        NODE_CATALOG=node_catalog(graph),
        CHIPS_SPEC=(
            _CHIPS_CLARIFY_MAU.format(toi_da=chip_toi_da) if xin_chips else _CHIPS_KHONG
        ),
        EVIDENCE_SPEC=_EVIDENCE_CO if thu_evidence else _EVIDENCE_KHONG,
        REPLY_NOTE=_REPLY_CYCLE if che_do_cycle else "",
        # Chỉ dẫn "lượt này phải đạt được gì" — xem app/gate/directive.py.
        GATE_DIRECTIVE=build_directive(
            graph, overlay, decision,
            refusal_situation=refusal_situation,
            user_message=user_message,
        ),
        # Lý thuyết nền, lấy theo node đang nhắm. Xem GraphService.theory_steer().
        THEORY_STEER=graph.theory_steer(
            decision.target_nodes[0] if decision.target_nodes else None
        ),
    )
    recent = recent_turns or "(chưa có)"

    if refusal_situation is not None:
        system = skills.build(
            "99_REFUSAL", SITUATION=refusal_situation, USER_MESSAGE=user_message, **chung
        )
        return TurnPrompt("99_REFUSAL", system, user_message, 500, 0.4)

    if decision.gate == CLARIFY:
        label = ""
        if decision.target_nodes:
            n = graph.node(decision.target_nodes[0])
            label = n.label if n else ""
        # Dáng vừa chọn được ghi lại để lượt sau không hỏi lại đúng kiểu câu đó.
        # build_directive() là hàm thuần nên việc ghi nằm ở đây.
        khoa, _ = chon_dang_cau_hoi(
            graph, overlay, user_message,
            decision.target_nodes[0] if decision.target_nodes else None,
        )
        overlay.ghi_dang(khoa)
        system = skills.build(
            "11_CLARIFY",
            TARGET_NODE_LABEL=label or "điều người dùng vừa nói",
            KNOWN_VERBATIMS=_verbatim_list(overlay),
            RECENT_TURNS=recent,
            USER_MESSAGE=user_message,
            **chung,
        )
        return TurnPrompt("11_CLARIFY", system, user_message, 700, 0.7)

    if decision.gate == ORIENT:
        # Chip chủ đề là TẤT ĐỊNH (pipeline/quick_reply.py) — mô hình chỉ viết
        # hai câu dẫn. Để nó tự sinh chip ở đây là mời nó liệt kê lại đúng thứ
        # đang hiện ngay bên dưới.
        system = skills.build(
            "13_ORIENT", RECENT_TURNS=recent, USER_MESSAGE=user_message, **chung
        )
        return TurnPrompt("13_ORIENT", system, user_message, 300, 0.5)

    if decision.gate == REFLECT:
        mode = decision.mode or "single"
        if che_do_cycle:
            vbs = " · ".join(f'"{v}"' for v in cycle_ordered_verbatims or [])
            pattern = "một vòng lặp: kỳ vọng cao -> không đạt -> tự phê phán -> lại cố hơn"
        else:
            vbs = _verbatim_list(overlay, decision.target_nodes)
            pattern = "cách người dùng nói về mình đang khá nặng nề"
        system = skills.build(
            "12_REFLECT",
            VERBATIMS=vbs, PATTERN_DESCRIPTION=pattern, MODE=mode,
            RECENT_TURNS=recent, **chung,
        )
        return TurnPrompt("12_REFLECT", system, user_message, 700, 0.7, che_do_cycle)

    if decision.gate == BRIDGE:
        res_node = graph.node(decision.resource_node) if decision.resource_node else None
        rtype = "ba mẹ" if (res_node and res_node.resource_kind == "gia-dinh") else (
            res_node.label if res_node else "người thật"
        )
        system = skills.build(
            "15_BRIDGE",
            RESOURCE_TYPE=rtype, TRIGGER_REASON=decision.reason,
            VERBATIMS=_verbatim_list(overlay), RECENT_TURNS=recent, **chung,
        )
        return TurnPrompt("15_BRIDGE", system, user_message, 500, 0.3)

    if decision.gate == SUPPORT:
        # Chế độ chủ đề phát thẻ KHÁI NIỆM (không có coping_node), nên lấy tiêu
        # đề từ concept — nếu không mô hình được bảo là sắp giới thiệu "một gợi
        # ý nhỏ" trong khi thứ sắp hiện ra là một thẻ lý thuyết.
        node_id = decision.coping_node or decision.concept_node
        node = graph.node(node_id) if node_id else None
        body = graph.content_body(node_id) if node_id else None
        system = skills.build(
            "14_SUPPORT",
            VERBATIMS=_verbatim_list(overlay),
            COPING_TITLE=(body or {}).get("title") or (node.label if node else "một gợi ý nhỏ"),
            RECENT_TURNS=recent, **chung,
        )
        return TurnPrompt("14_SUPPORT", system, user_message, 400, 0.6)

    raise ValueError(f"gate không diễn đạt được: {decision.gate}")


# ---------------------------------------------------------------------------
def _parse_json(text: str) -> dict | None:
    for cand in (text, *_FENCE.findall(text or "")):
        cand = (cand or "").strip()
        if not cand:
            continue
        try:
            data = json.loads(cand)
        except json.JSONDecodeError:
            m = _OBJ.search(cand)
            if not m:
                continue
            try:
                data = json.loads(m.group(0))
            except json.JSONDecodeError:
                continue
        if isinstance(data, dict):
            return data
    return None


def _chuan_hoa_substring(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").lower()).strip()


def _risk_cues(graph: GraphService) -> list[str]:
    out: list[str] = []
    for nid in graph.evidence_node_ids:
        n = graph.node(nid)
        if n and n.risk_adjacent:
            out.extend(normalize_vi(c) for c in n.cues)
    return out


def _chip_an_toan(chip: str, risk_cues: list[str]) -> bool:
    if not chip or len(chip) > 44 or len(chip.split()) > 9:
        return False
    if check_crisis(chip).tier is not None:
        return False
    norm = normalize_vi(chip)
    if any(b in norm for b in _CHIP_CAM):
        return False
    return not any(rc and rc in norm for rc in risk_cues)


def parse_turn_output(
    raw: str,
    *,
    graph: GraphService,
    user_message: str,
    turn_id: int,
    lay_chips: bool,
    cycle_verbatims: list[str] | None = None,
    chip_toi_da: int = 3,
) -> TurnOutput:
    """JSON của mô hình -> TurnOutput đã kiểm. Không bao giờ raise.

    Chốt chặn chống bịa giữ nguyên từ app/llm/extract.py cũ: node_id không có
    trong graph thì loại, verbatim không phải chuỗi con của tin nhắn thì loại,
    confidence vượt trần theo `mapping` thì kẹp lại.
    """
    out = TurnOutput()
    data = _parse_json(raw)
    if data is None:
        # Không parse được -> coi TOÀN BỘ raw là câu trả lời. Thà bot nói được
        # một câu hơi thô còn hơn im lặng vì mô hình quên dấu ngoặc nhọn.
        out.reply = (raw or "").strip()
        out.flags.append("turn_parse_failed")
        return out

    out.reply = str(data.get("reply") or "").strip()

    if cycle_verbatims is not None:
        cho_phep = list(cycle_verbatims)
        giu = [l for l in (data.get("lines") or []) if l in cho_phep]
        out.lines = giu[:5] if len(giu) >= 3 else cho_phep[:5]
        out.closing = str(data.get("closing") or "").strip()

    if lay_chips:
        risk = _risk_cues(graph)
        seen: set[str] = set()
        for c in data.get("chips") or []:
            # §E7 — dấu chấm biến chip thành lời tuyên bố dứt khoát ("Mình thấy
            # mình kém cỏi."); bỏ đi thì nó đọc như một câu nói dở dang, đúng
            # bản chất của một gợi ý.
            c = str(c).strip().rstrip(".").strip()
            if _chip_an_toan(c, risk) and c.lower() not in seen:
                seen.add(c.lower())
                out.chips.append(c)
            if len(out.chips) >= max(chip_toi_da, 2):
                break
        if len(out.chips) < 2:
            out.chips = []          # thiếu -> caller dùng chip tất định
            out.flags.append("chips_khong_du_sau_loc")

    valid = set(graph.evidence_node_ids)
    haystack = _chuan_hoa_substring(user_message)
    for item in data.get("evidence") or []:
        try:
            r = _RawEvidence(**item)
        except (ValidationError, TypeError):
            out.flags.append("extract_bad_item")
            continue
        if r.node_id not in valid:
            out.flags.append("extract_hallucinated_node")
            continue
        vb = (r.verbatim or "").strip()
        if vb and _chuan_hoa_substring(vb) not in haystack:
            out.flags.append("extract_verbatim_not_substring")
            continue
        literal = r.mapping.strip().lower() == "literal"
        cap = (
            settings.self_report_confidence_cap if literal
            else settings.extract_confidence_cap
        )
        out.evidence.append(
            Evidence(
                node_id=r.node_id,
                confidence=min(max(r.confidence, 0.0), cap),
                source=EvidenceSource.SELF_REPORT if literal else EvidenceSource.INFERRED,
                turn_ids=[turn_id],
                verbatim=vb,
            )
        )
    return out
