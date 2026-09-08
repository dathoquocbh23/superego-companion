# 08 — LOG CÓ CẤU TRÚC

> Mượn nguyên tắc từ `KG_DEMO_CONTEXT.md §7.4`:
> *"Output của gate/policy phải GHI LOG có cấu trúc — vừa để debug demo, vừa là dữ liệu đo cho paper sau này."*
>
> **Thiết kế log NGAY BÂY GIỜ**, không để tới giai đoạn 2. Log thiếu trường = mất dữ liệu vĩnh viễn.

---

## 1. Schema một lượt

Ghi vào `data/turns.jsonl`, mỗi dòng một JSON.

```jsonc
{
  "turn_id": 7,
  "session_hash": "a3f9c2",           // hash 6 ký tự, KHÔNG phải session_id
  "ts": "2026-09-24T14:32:11Z",

  // ── An toàn ──────────────────────────────────────────
  "safety_tier": null,                // null | 1 | 2 | 3
  "safety_matched": [],               // cụm từ đã khớp (để tinh chỉnh phrase list)

  // ── Đầu vào ──────────────────────────────────────────
  "input_len": 47,
  "input_is_chip": false,
  "chip_type": null,                  // CONFIRM_YES | CONFIRM_NO | ASK | DECLINE

  // ── Trích bằng chứng ─────────────────────────────────
  "extracted": [
    { "node_id": "m-tu-trach", "confidence": 0.55 }
  ],
  "extract_failed": false,
  "extract_hallucinated": [],         // node_id bịa bị loại

  // ── Trạng thái overlay SAU lượt này ──────────────────
  "overlay_size": 6,
  "overlay_by_source": { "LIKERT": 4, "SELF_REPORT": 2, "INFERRED": 0, "CONFIRMED": 0 },
  "active_cycles": ["cycle-tu-phe-phan"],

  // ── Quyết định ───────────────────────────────────────
  "gate": "REFLECT",
  "gate_reason": "cycle_activated",
  "target_nodes": ["cycle-tu-phe-phan"],
  "policy_edge_used": null,           // khi gate = SUPPORT

  // ── Đầu ra ───────────────────────────────────────────
  "message_type": "INSIGHT_CARD",
  "response_len": 132,
  "response_sentences": 3,
  "postcheck_flags": [],              // vd ["postcheck_diagnosis_blocked"]

  // ── Quick replies ────────────────────────────────────
  "chip_provenance": [
    { "text_hash": "9d2f", "gate": "REFLECT", "source_node": "cycle-tu-phe-phan", "target_node": null, "is_escape": false },
    { "text_hash": "1a7b", "gate": "REFLECT", "source_node": "cycle-tu-phe-phan", "target_node": null, "is_escape": true }
  ],

  // ── Hiệu năng ────────────────────────────────────────
  "latency_ms": { "safety": 2, "extract": 810, "speak": 1640, "total": 2510 },
  "tokens": { "extract_in": 1420, "extract_out": 86, "speak_in": 980, "speak_out": 118 }
}
```

---

## 2. ⚠️ KHÔNG bao giờ ghi vào log

| Trường | Vì sao |
|---|---|
| `user_message` (nguyên văn) | Lời tâm sự của trẻ vị thành niên = dữ liệu nhạy cảm (Nghị định 13/2023/NĐ-CP) |
| `verbatim` | Cùng lý do |
| `response_text` (nguyên văn) | Có thể chứa lại verbatim của người dùng |
| `session_id` gốc | Dùng `session_hash` — hash một chiều, không truy ngược |
| Bất kỳ PII nào | Tên, trường, lớp, số điện thoại |

> **Chỉ ghi metadata và định danh node.** Đủ để phân tích hành vi hệ thống, không đủ để tái dựng nội dung riêng tư.

### Ngoại lệ có kiểm soát (giai đoạn 2)

Khi có **hội đồng đạo đức duyệt + đồng thuận phụ huynh + đồng thuận học sinh**, mới bật thêm log nội dung để chuyên gia chấm transcript. Lúc đó ghi ra file **riêng, mã hoá**, không lẫn vào `turns.jsonl`.

---

## 3. Log này trả lời được câu hỏi gì

### Cho demo (tuần 4 — debug)

| Câu hỏi | Trường dùng |
|---|---|
| Bot có bị kẹt ở `CLARIFY` mãi không? | `gate` theo `turn_id` |
| Trích xuất có bịa node không? | `extract_hallucinated` |
| Post-check có bắt được gì không? | `postcheck_flags` |
| Chậm ở đâu? | `latency_ms` |
| Cụm từ khủng hoảng nào hay khớp nhầm? | `safety_matched` khi `safety_tier = 3` |

### Cho giai đoạn 2 (nghiên cứu)

| Chỉ số | Cách tính |
|---|---|
| **Số lượt trung bình để đạt `CONFIRMED` đầu tiên** | Đo tốc độ "hiểu người dùng" của graph |
| **Tỉ lệ phân bố gate** | `CLARIFY` quá cao = bot mù; `SUPPORT` quá sớm = nguy hiểm |
| **Tỉ lệ kích hoạt cycle** | Đo hiệu quả của thiết kế graph |
| **Tỉ lệ chip thoát được bấm** | Đo mức độ chip có ép buộc không |
| **Độ chính xác phát hiện khủng hoảng** | Đối chiếu `safety_tier` với nhãn của chuyên gia |
| **Tỉ lệ post-check chặn** | Đo độ an toàn của prompt |
| **So sánh có/không làm test** | Nhóm có `LIKERT` trong `overlay_by_source` vs không |

> Chỉ số **"số lượt để đạt CONFIRMED đầu tiên"** là bằng chứng định lượng mạnh nhất cho luận điểm *"graph giúp hiểu người dùng nhanh hơn"*. Nhớ đo nó.

---

## 4. Ghi log

```python
def log_turn(ctx: PipelineContext) -> None:
    """KHÔNG BAO GIỜ để lỗi log làm hỏng lượt chat của người dùng."""
    try:
        record = build_record(ctx)
        with open(settings.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception:
        logger.exception("log_turn failed")   # nuốt lỗi, không raise
```

```python
def session_hash(session_id: str) -> str:
    return hashlib.sha256(session_id.encode()).hexdigest()[:6]
```

---

## 5. Kiểm tra nhanh log (tuần 4)

```python
import pandas as pd
df = pd.read_json("data/turns.jsonl", lines=True)

df["gate"].value_counts(normalize=True)          # phân bố gate
df["postcheck_flags"].explode().value_counts()   # post-check bắt gì
df["latency_ms"].apply(lambda d: d["total"]).describe()
df[df["extract_hallucinated"].str.len() > 0]     # trích bịa node
```

---

## 6. Checklist

- [ ] `telemetry/log.py` — schema đầy đủ §1
- [ ] `session_hash` — sha256 cắt 6 ký tự
- [ ] Kiểm lại: **không có trường nào chứa nội dung người dùng**
- [ ] Nuốt lỗi khi ghi log thất bại
- [ ] `data/turns.jsonl` nằm trong `.gitignore`
- [ ] Script phân tích nhanh (§5) để dùng ở tuần 4
