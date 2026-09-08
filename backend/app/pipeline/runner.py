"""
Orchestrator một lượt chat. GĐ2 (07/09/2026): MỘT lượt = MỘT lời gọi LLM.

Trả về async generator các sự kiện SSE dạng (event_name, data_dict):
    meta → (token* | card) → footer → done

Khác kiến trúc cũ ở đúng hai chỗ:

  [3] TRÍCH giờ TẤT ĐỊNH (app/evidence/matcher.py) — chạy TRƯỚC gate, 0 token,
      ~0ms thay cho ~1.300ms. Cái LLM còn làm là SUY DIỄN, và nó về cùng lượt
      nói ở bước [7], nên có hiệu lực từ lượt SAU.

  [7] Một lời gọi duy nhất trả JSON {reply, chips, evidence} thay cho ba lời
      gọi nối tiếp (extract → speak → quickreply). Mất khả năng stream token
      thật, nhưng tổng thời gian GIẢM: 3 lượt round-trip nối tiếp (~3.5s theo
      turns.jsonl) xuống còn 1 (~1.5s). Token phát ra là cắt khúc chuỗi đã có.

ESCALATE: chỉ meta → card(CRISIS_CARD) → done. KHÔNG có token nào (không gọi LLM).

GĐ6 (07/09/2026): sau khi yield "done", lượt được ghi nguyên văn vào Supabase
(_ghi_transcript). Chạy sau cùng nên không chen vào đường phản hồi.
"""
from __future__ import annotations

import logging
import time
from collections.abc import AsyncIterator

from app.config import settings
from app.evidence.matcher import match_evidence
from app.gate.decide import (
    BRIDGE, CLARIFY, ESCALATE, ORIENT, REFLECT, SUPPORT,
    TARGET_HOI_LAI_TOI_DA, TARGET_NE_TRONG, decide_gate,
)
from app.graph.cycles import active_cycles, cycle_verbatim_lines
from app.graph.loader import get_graph
from app.llm.client import get_llm
from app.llm.turn import build_turn_prompt, parse_turn_output
from app.memory.service import memory_quotes
from app.memory.service import record_turn as memory_record_turn
from app.memory.service import seed_overlay as memory_seed_overlay
from app.overlay.model import Overlay
from app.overlay.store import get_store
from app.pipeline.context import PipelineContext
from app.persistence.transcript import get_transcript_store, title_from
from app.persistence.turnlog import get_turnlog_store
from app.pipeline.quick_reply import ESCAPE_CLARIFY as QR_ESCAPE_CLARIFY
from app.pipeline.quick_reply import build_quick_replies, ngan_sach_chip_noi_dung
from app.pipeline.riskflags import infer_riskflags
from app.safety.chips import detect_chip
from app.safety.crisis import check_crisis
from app.safety.postcheck import is_near_duplicate, post_check
from app.safety.refusal import classify_refusal
from app.telemetry.log import log_turn, session_hash

logger = logging.getLogger(__name__)

MESSAGE_TYPE_BY_GATE = {
    ESCALATE: "CRISIS_CARD",
    BRIDGE: "BRIDGE_CARD",
    SUPPORT: "COPING_CARD",
    CLARIFY: "REFLECT",
    REFLECT: "REFLECT",
    ORIENT: "REFLECT",
}

SUPPORT_LEAD_FALLBACK = "Vậy mình đưa bạn xem cái này nhé:"
LOI_CHUNG = "Mình đang hơi chậm, bạn nhắn lại giúp mình nhé."

# D6 — nhãn node đưa vào post-check. CHỈ node PHÁN QUYẾT: nhãn trigger là chữ
# thường ngày ("kết quả học tập", "chuyện tình cảm") mà bot nói ra hoàn toàn
# bình thường — đưa vào đây là tự chặn mình.
_TYPE_PHAN_QUYET = {"manifestation", "affect", "impact"}


def _nhan_phan_quyet(graph) -> list[str]:
    return [
        n.label
        for nid in graph.evidence_node_ids
        if (n := graph.node(nid)) and n.type in _TYPE_PHAN_QUYET
    ]


def _last_assistant_text(overlay: Overlay) -> str:
    for row in reversed(overlay.history):
        if row.get("role") == "assistant":
            return row.get("text", "")
    return ""


async def _ghi_so_lieu(record: dict | None) -> None:
    """Đẩy bản ghi turn_logs lên Supabase. File jsonl đã ghi xong trước đó.

    Tách khỏi _ghi_transcript() có chủ đích: đây là số liệu KHÔNG PII, kho
    riêng, bảng riêng. Xem docstring app/persistence/turnlog.py.
    """
    if record:
        await get_turnlog_store().push([record])


async def _ghi_transcript(ctx: PipelineContext, user_message: str) -> None:
    """Lưu 2 message của lượt này vào Supabase. GĐ6.

    Gọi SAU khi đã yield "done" — người dùng đã đọc xong câu trả lời, nên chậm
    hay hỏng ở đây đều không ai thấy. Nuốt lỗi tuyệt đối: mất transcript còn
    hơn mất phiên tư vấn.
    """
    store = get_transcript_store()
    if not store.available:
        return
    overlay = ctx.overlay
    try:
        # Overlay Redis hết TTL, hoặc Supabase chết đúng lúc mở phiên → chưa có
        # id. Dựng lại ở đây thay vì bỏ luôn cả phiên.
        if not overlay.conversation_id:
            overlay.conversation_id = await store.ensure_conversation(
                ctx.session_id, overlay.user_id
            )
        if not overlay.conversation_id:
            return

        if ctx.turn_id == 1:
            await store.set_title(overlay.conversation_id, title_from(user_message))

        await store.record_messages(overlay.conversation_id, [
            {
                "turn_id": ctx.turn_id, "role": "user", "message_type": "USER",
                "content": user_message,
            },
            {
                "turn_id": ctx.turn_id, "role": "assistant",
                "message_type": ctx.message_type,
                # Thẻ (INSIGHT/COPING/BRIDGE/CRISIS) không có `content` — nội
                # dung nằm ở `card`. Giữ chuỗi rỗng chứ không nhồi mô tả thẻ
                # vào content: đọc lại lúc phân tích sẽ tưởng bot đã nói câu đó.
                "content": ctx.response_text or "",
                "card": ctx.card,
                "quick_replies": ctx.quick_replies or None,
            },
        ])
    except Exception:  # pragma: no cover — đã nuốt ở tầng store, đây là lưới cuối
        logger.exception("ghi transcript lỗi")


def _crisis_card_payload() -> dict:
    try:
        text = settings.crisis_card_path.read_text(encoding="utf-8")
    except Exception:  # pragma: no cover
        text = "Hotline sơ cứu tâm lý: 0832000202"
    return {"type": "CRISIS_CARD", "markdown": text, "phone": "0832000202"}


async def run_chat_turn(session_id: str, message: str) -> AsyncIterator[tuple[str, dict]]:
    graph = get_graph()
    store = get_store()
    llm = get_llm()
    t0 = time.perf_counter()

    overlay: Overlay = await store.get(session_id)

    # Bộ nhớ dài hạn — nạp MỘT LẦN ở đầu phiên, trước khi trích bất cứ gì.
    # Node nạp vào mang source=REMEMBERED: không phát ngôn được, không đủ mạnh
    # để kích REFLECT, chỉ giúp CLARIFY hỏi trúng chỗ hơn. Xem docx/12 §5.
    await memory_seed_overlay(overlay, overlay.user_id, graph)

    overlay.turn_count += 1
    turn_id = overlay.turn_count

    ctx = PipelineContext(
        session_id=session_id,
        session_hash=session_hash(session_id),
        user_message=message,
        overlay=overlay,
        turn_id=turn_id,
        input_len=len(message or ""),
    )

    # ── [1] SAFETY TẤT ĐỊNH ─────────────────────────────────────────
    s_start = time.perf_counter()
    ctx.safety = check_crisis(message)
    ctx.latency_ms["safety"] = int((time.perf_counter() - s_start) * 1000)

    if ctx.safety.stops_pipeline:
        ctx.gate = decide_gate(graph, overlay, ctx.safety, None)  # → ESCALATE
        ctx.message_type = "CRISIS_CARD"
        ctx.card = _crisis_card_payload()
        overlay.crisis_shown = True
        overlay.gates_used.append(ESCALATE)
        overlay.push_history("user", message)
        await store.save(overlay)

        yield "meta", {"gate": ESCALATE, "message_type": "CRISIS_CARD"}
        yield "card", ctx.card
        yield "footer", {"quickReplies": [], "turn_id": turn_id, "crisis": True}
        yield "done", {}
        ctx.latency_ms["total"] = int((time.perf_counter() - t0) * 1000)
        await _ghi_so_lieu(log_turn(ctx))
        # Lượt khủng hoảng là lượt ĐÁNG lưu nhất cho nghiên cứu — đừng để nó
        # rơi mất chỉ vì nhánh này return sớm.
        await _ghi_transcript(ctx, message)
        await store.save(overlay)
        return

    # ── [2] CHIP PREFIX? ────────────────────────────────────────────
    ctx.chip = detect_chip(message)
    ctx.input_is_chip = ctx.chip is not None
    clean_message = ctx.chip.clean_text if ctx.chip else message

    # ── [2b] TỪ CHỐI NGOÀI PHẠM VI / JAILBREAK ─────────────────────
    refusal = None if ctx.chip else classify_refusal(message)

    # ── [3] TRÍCH BẰNG CHỨNG — TẤT ĐỊNH, 0 TOKEN ───────────────────
    #     Chạy TRƯỚC gate nên vẫn có hiệu lực NGAY LƯỢT NÀY, đúng như kiến
    #     trúc cũ. Phần LLM suy ra thêm được gộp vào ở cuối, cho lượt sau.
    if ctx.chip is None and refusal is None:
        e_start = time.perf_counter()
        ctx.extracted = match_evidence(graph, message, turn_id)
        ctx.latency_ms["extract"] = int((time.perf_counter() - e_start) * 1000)
        ctx.flags.append("extract_cue_matcher")

    # ── [4] CẬP NHẬT OVERLAY ──────────────────────────────────────
    if ctx.chip and ctx.chip.chip_type == "CONFIRM_YES":
        targets = list(overlay.active_cycles)
        cyc_nodes: list[str] = []
        for cid in targets:
            c = next((c for c in graph.cycles if c.id == cid), None)
            if c:
                cyc_nodes.extend(n for n in c.nodes if overlay.has(n))
        if not cyc_nodes:
            cyc_nodes = [
                nid for nid, e in overlay.evidence.items()
                if e.confidence >= settings.confidence_threshold
                and graph.node(nid) and graph.node(nid).is_evidence
            ]
        overlay.promote_confirmed(cyc_nodes, turn_id)
    elif ctx.chip and ctx.chip.chip_type == "CONFIRM_PARTIAL":
        # docx/11 §E5 — nâng vừa phải, KHÔNG promote CONFIRMED, rồi khoá REFLECT
        # vài lượt để bot không dựng lại đúng cái thẻ họ vừa nói là chưa khớp.
        nang = [
            n for c in overlay.active_cycles for cc in graph.cycles if cc.id == c
            for n in cc.nodes if overlay.has(n)
        ]
        overlay.promote_partial(nang or list(overlay.evidence), turn_id)
        overlay.reflect_locked_until = overlay.turn_count + settings.reflect_cooldown_turns
    elif ctx.chip and ctx.chip.chip_type == "CONFIRM_NO":
        lower = [n for c in overlay.active_cycles for cc in graph.cycles if cc.id == c for n in cc.nodes]
        overlay.lower_confidence(lower or list(overlay.evidence), 0.3)
    elif ctx.chip and ctx.chip.chip_type == "DECLINE":
        # không hỏi lại node đang nhắm trong 3 lượt
        for cid in overlay.active_cycles:
            pass
    else:
        for ev in ctx.extracted:
            overlay.merge(ev)

    infer_riskflags(graph, overlay, message, turn_id)
    overlay.active_cycles = active_cycles(graph, overlay.confidences())

    # ── [4b] ĐO GIẬM CHÂN ──────────────────────────────────────────
    #     Phải chạy TRƯỚC decide_gate: gate ORIENT đọc chính hai con số này.
    # Đếm node NÓI ĐƯỢC, không đếm tổng: bằng chứng LLM suy ra (INFERRED) làm
    # overlay phình lên mà bot vẫn chưa nắm được gì để phản chiếu. Xem
    # Overlay.so_node_noi_duoc() và docx/11 D8.
    kich_thuoc = overlay.so_node_noi_duoc()
    overlay.stall_streak = (
        0 if kich_thuoc > overlay.evidence_size_prev else overlay.stall_streak + 1
    )
    overlay.evidence_size_prev = kich_thuoc

    # ── [4c] BỎ CUỘC VỚI NODE HỎI MÃI KHÔNG RA (D10) ──────────────
    #     Chạy TRƯỚC decide_gate để lượt này đã nhắm sang chỗ khác.
    truoc = overlay.target_truoc
    if truoc and not overlay.has(truoc):
        overlay.target_hoi_lai += 1
        if overlay.target_hoi_lai >= TARGET_HOI_LAI_TOI_DA:
            overlay.suppressed_nodes[truoc] = overlay.turn_count + TARGET_NE_TRONG
            overlay.target_hoi_lai = 0
            ctx.flags.append("target_bo_cuoc")
    else:
        overlay.target_hoi_lai = 0

    # ── [5] GATE ─────────────────────────────────────────────────
    ctx.gate = decide_gate(graph, overlay, ctx.safety, ctx.chip)
    decision = ctx.gate
    overlay.target_truoc = (
        decision.target_nodes[0]
        if decision.gate == CLARIFY and decision.target_nodes
        else None
    )

    # ── [6] DỰNG NGỮ CẢNH CYCLE ─────────────────────────────────
    cycle_lines: list[str] = []
    if decision.gate == REFLECT and decision.mode == "cycle" and decision.target_nodes:
        cycle_lines = cycle_verbatim_lines(
            graph, decision.target_nodes[0], overlay.verbatims(), overlay.confidences()
        )
        # D4 — < 3 dòng sau khử trùng lặp → không dựng thẻ, quay về REFLECT đơn
        if len(cycle_lines) < 3:
            decision.mode = "single"
            cycle_lines = []

    # docx/11 §E3 — TRẦN chip nội dung cho lượt này. Phải tính TRƯỚC lời gọi:
    # chính prompt là chỗ nói cho mô hình biết nó được viết mấy chip.
    chip_toi_da = ngan_sach_chip_noi_dung(graph, overlay, clean_message)

    prompt = build_turn_prompt(
        skills=_skills(), graph=graph, overlay=overlay, decision=decision,
        user_message=clean_message,
        recent_turns=overlay.recent_turns_text(),
        cycle_ordered_verbatims=cycle_lines or None,
        refusal_situation=refusal,
        thu_evidence=(ctx.chip is None and refusal is None),
        chip_toi_da=chip_toi_da,
    )

    ctx.message_type = "REFLECT" if refusal else MESSAGE_TYPE_BY_GATE.get(decision.gate, "REFLECT")
    if decision.gate == REFLECT and decision.mode == "cycle":
        ctx.message_type = "INSIGHT_CARD"
    if decision.gate == SUPPORT:
        ctx.message_type = "KNOWLEDGE_CARD" if decision.concept_node and not decision.coping_node else "COPING_CARD"

    yield "meta", {"gate": ("REFUSAL" if refusal else decision.gate), "message_type": ctx.message_type}

    # ── [7] LỜI GỌI LLM DUY NHẤT CỦA LƯỢT ───────────────────────
    sp_start = time.perf_counter()
    raw_text = ""
    try:
        raw_text = await llm.complete(
            system=prompt.system, user=prompt.user,
            max_tokens=prompt.max_tokens, temperature=prompt.temperature,
            json_mode=True,
        )
    except Exception:
        logger.exception("lượt: LLM lỗi")
        ctx.flags.append("turn_llm_error")
    ctx.latency_ms["speak"] = int((time.perf_counter() - sp_start) * 1000)

    out = parse_turn_output(
        raw_text,
        graph=graph,
        user_message=clean_message,
        turn_id=turn_id,
        lay_chips=(decision.gate == CLARIFY and refusal is None),
        cycle_verbatims=cycle_lines if prompt.che_do_cycle else None,
        chip_toi_da=chip_toi_da,
    )
    ctx.flags.extend(out.flags)
    ctx.extract_failed = "turn_parse_failed" in out.flags
    ctx.extract_hallucinated = [f for f in out.flags if f == "extract_hallucinated_node"]

    # ── [8] KIỂM HẬU KỲ ─────────────────────────────────────────
    # refusal dùng prompt riêng, không phải CLARIFY thật => không áp luật 6.5
    nhan_node = _nhan_phan_quyet(graph)
    cau_truoc = _last_assistant_text(overlay)

    def _kiem(text: str):
        return post_check(
            text or LOI_CHUNG,
            gate=None if refusal else decision.gate,
            co_tri_nho=bool(memory_quotes(overlay, graph)),
            node_labels=nhan_node,
            cau_truoc="" if refusal else cau_truoc,
        )

    checked = _kiem(out.reply)

    # THỬ LẠI ĐÚNG MỘT LẦN cho hai lỗi mà prompt không tự chặn được:
    #   D6  câu có nhãn nội bộ của node
    #   D9  câu hỏi gần trùng câu lượt trước
    # `checked.text` lúc này đã là câu thay thế an toàn, nên thử lại thất bại
    # cũng không sinh ra đầu ra xấu — chỉ mất một lượt nói kém hay hơn.
    if (checked.label_leak or checked.lap_cau_hoi) and not prompt.che_do_cycle:
        if checked.label_leak:
            ctx.flags.append("label_leak_retry")
            cam = (
                f"\n\n⛔ LẦN TRƯỚC BẠN VIẾT HỎNG: câu của bạn có cụm «{checked.label_leak}»"
                " — đó là NHÃN NỘI BỘ của hệ thống, không phải chữ để nói với người"
                " dùng. Viết lại toàn bộ, tuyệt đối không dùng cụm đó và không dùng"
                " cách nói khác cùng nghĩa. Chỉ hỏi, đừng khẳng định gì về họ."
            )
        else:
            ctx.flags.append("lap_cau_hoi_retry")
            cam = (
                f"\n\n⛔ LẦN TRƯỚC BẠN VIẾT HỎNG: câu bạn vừa viết gần như trùng"
                f" câu bạn đã hỏi ở lượt trước —\n\n    «{cau_truoc}»\n\n"
                "Người dùng đang nhìn thấy cả hai câu trên cùng một màn hình. Hỏi"
                " lại cùng một thứ là dấu hiệu rõ nhất cho họ thấy bot không nghe."
                " Viết một câu hỏi HỎI VÀO CHUYỆN KHÁC HẲN, và đừng mở đầu bằng"
                " cùng một khuôn chữ."
            )
        try:
            raw_lai = await llm.complete(
                system=prompt.system + cam, user=prompt.user,
                max_tokens=prompt.max_tokens, temperature=prompt.temperature,
                json_mode=True,
            )
        except Exception:
            logger.exception("lượt: LLM lỗi khi thử lại sau lỗi hậu kỳ")
            raw_lai = ""
        if raw_lai:
            out_lai = parse_turn_output(
                raw_lai, graph=graph, user_message=clean_message, turn_id=turn_id,
                lay_chips=(decision.gate == CLARIFY and refusal is None),
                chip_toi_da=chip_toi_da,
            )
            lai = _kiem(out_lai.reply)
            if out_lai.reply and not lai.label_leak and not lai.lap_cau_hoi:
                checked = lai
                out.chips = out_lai.chips or out.chips
                out.evidence = out_lai.evidence or out.evidence
            else:
                ctx.flags.append("postcheck_retry_that_bai")

    ctx.flags.extend(checked.flags)
    ctx.response_text = checked.text

    # ── dựng card + phát token ─────────────────────────────────
    if prompt.che_do_cycle and cycle_lines:
        lines = out.lines or cycle_lines[:5]
        closing = out.closing or "Mình xâu chuỗi lại từ chính lời bạn nói. Mình hiểu đúng ý bạn chứ?"
        ctx.card = {"type": "INSIGHT_CARD", "lines": lines[:5], "closing": closing}
        ctx.response_text = ""
        yield "card", ctx.card
    elif decision.gate == SUPPORT:
        lead = checked.text or SUPPORT_LEAD_FALLBACK
        # Câu dẫn nằm ngay dưới câu REFLECT của lượt trước, cùng một màn hình.
        # Nhại lại là hỏng hẳn — xem is_near_duplicate().
        truoc = _last_assistant_text(overlay)
        if truoc and is_near_duplicate(lead, truoc):
            lead = SUPPORT_LEAD_FALLBACK
            ctx.flags.append("support_lead_duplicate_replaced")
        card: dict = {"type": ctx.message_type, "lead": lead}
        if decision.coping_node:
            body = graph.content_body(decision.coping_node) or {}
            card.update(
                title=body.get("title", ""),
                body=(body.get("body", "") or "").strip(),
                action=body.get("action", ""),
                source=body.get("source", ""),
            )
        if decision.concept_node and not decision.coping_node:
            body = graph.content_body(decision.concept_node) or {}
            card.update(
                title=body.get("title", ""),
                body=(body.get("body", "") or "").strip(),
                source=body.get("source", ""),
            )
        ctx.card = card
        yield "token", {"t": lead}
        yield "card", card
    elif decision.gate == BRIDGE:
        lead = checked.text or "Nói với người thật không phải là làm quá đâu."
        body = graph.content_body(decision.resource_node) if decision.resource_node else None
        card = {"type": "BRIDGE_CARD", "lead": lead}
        if body:
            card.update(
                title=body.get("title", ""),
                body=(body.get("body", "") or "").strip(),
                source=body.get("source", ""),
            )
        ctx.card = card
        yield "token", {"t": lead}
        yield "card", card
    else:
        # CLARIFY / REFLECT đơn / REFUSAL → text thuần.
        # Cắt khúc chỉ để giữ nguyên giao diện SSE của frontend; đây KHÔNG còn
        # là stream thật (xem docstring đầu file).
        for piece in _chunk_text(ctx.response_text):
            yield "token", {"t": piece}

    # ── [9] QUICK REPLIES ─────────────────────────────────────
    if decision.gate == ESCALATE:
        ctx.quick_replies, ctx.chip_provenance = [], []
    elif refusal is not None:
        # Lượt từ chối KHÔNG kèm chip: `decision` ở đây là gate cũ (trích bị bỏ
        # qua), nên chip sinh ra sẽ thuộc về lượt trước — bấm "Đúng vậy" sẽ
        # promote evidence cho một mẫu hình bot vừa KHÔNG hề nêu.
        ctx.quick_replies, ctx.chip_provenance = [], []
    else:
        ctx.quick_replies, ctx.chip_provenance = build_quick_replies(
            graph, overlay, decision, so_dong_the=len(cycle_lines),
        )
        # CLARIFY: thay chip tĩnh bằng chip mô hình vừa sinh trong CÙNG lời gọi
        # (giữ chip thoát). Rỗng = đã bị lọc an toàn → giữ chip tất định.
        # Số chip là 2..chip_toi_da, do mô hình quyết trong khoảng đó — xem
        # docx/11 §E3: chỉ nó mới biết câu nó vừa viết có giả định hay không.
        if decision.gate == CLARIFY and len(out.chips) >= 2:
            tgt = decision.target_nodes[0] if decision.target_nodes else None
            escape = QR_ESCAPE_CLARIFY
            noi_dung = out.chips[:chip_toi_da]
            ctx.quick_replies = [*noi_dung, escape]
            ctx.chip_provenance = [
                {"text": c, "gate": CLARIFY, "source_node": tgt,
                 "target_node": None, "is_escape": False}
                for c in noi_dung
            ]
            ctx.chip_provenance.append(
                {"text": escape, "gate": CLARIFY, "source_node": tgt,
                 "target_node": None, "is_escape": True}
            )

    # ── [10] BẰNG CHỨNG LLM SUY RA → có hiệu lực từ lượt SAU ────
    #     Gộp SAU khi gate đã quyết, đúng theo đánh đổi đã ghi ở đầu file.
    for ev in out.evidence:
        overlay.merge(ev)
        ctx.extracted.append(ev)

    # ── cập nhật overlay lịch sử + gate ─────────────────────
    overlay.gates_used.append("REFUSAL" if refusal else decision.gate)
    overlay.gates_used[:] = overlay.gates_used[-20:]
    if decision.gate == BRIDGE:
        overlay.bridge_offered = True
    overlay.push_history("user", message)
    display = ctx.response_text or (ctx.card.get("lead") if ctx.card else "") or "[thẻ]"
    overlay.push_history("assistant", display)
    await store.save(overlay)

    # Ghi vào bộ nhớ dài hạn. Nuốt lỗi — bộ nhớ hỏng không được làm hỏng lượt chat.
    await memory_record_turn(
        overlay, overlay.user_id, ctx.session_hash, turn_id, ctx.extracted
    )

    yield "footer", {"quickReplies": ctx.quick_replies, "turn_id": turn_id}
    yield "done", {}

    ctx.latency_ms["total"] = int((time.perf_counter() - t0) * 1000)
    await _ghi_so_lieu(log_turn(ctx))
    await _ghi_transcript(ctx, message)
    if overlay.conversation_id:
        await store.save(overlay)   # giữ lại id vừa dựng lại, khỏi hỏi lần nữa


# --------------------------------------------------------------------------
def _chunk_text(text: str, size: int = 24):
    text = text or ""
    for i in range(0, len(text), size):
        yield text[i:i + size]


def _skills():
    from app.skills.loader import get_skills
    return get_skills()
