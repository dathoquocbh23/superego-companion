# 03 — OVERLAY & GATE

> Overlay = thứ bot *biết* về người dùng. Gate = quyết định bot *làm gì* với hiểu biết đó.
> Đây là nơi trả lời câu hỏi "làm sao bot thực sự hiểu người dùng đang gặp gì".

---

## 1. Mô hình bằng chứng (Evidence)

```python
class EvidenceSource(str, Enum):
    REMEMBERED  = "REMEMBERED"   # nạp từ bộ nhớ dài hạn (phiên TRƯỚC) — xem docx/12
    LIKERT      = "LIKERT"       # từ bài tự đánh giá
    SELF_REPORT = "SELF_REPORT"  # người dùng tự nói ra
    INFERRED    = "INFERRED"     # LLM suy diễn
    CONFIRMED   = "CONFIRMED"    # bot hỏi lại, người dùng xác nhận

# Hạng mạnh dần khi merge: REMEMBERED(-1) < INFERRED(0) < LIKERT(1)
#                          < SELF_REPORT(2) < CONFIRMED(3)
# REMEMBERED yếu nhất là CỐ Ý: lời hôm nay luôn đè lời tháng trước.

class Evidence(BaseModel):
    node_id:    str
    confidence: float            # 0.0 – 1.0
    source:     EvidenceSource
    turn_ids:   list[int]
    verbatim:   str              # ⚠️ BẮT BUỘC — nguyên văn người dùng nói
    updated_at: datetime

class Overlay(BaseModel):
    session_id:      str
    user_id:         str | None              # None = ẩn danh (mặc định)
    memory_seeded:   bool                    # đã nạp bộ nhớ dài hạn chưa
    evidence:        dict[str, Evidence]     # node_id → Evidence
    active_cycles:   list[str]
    turn_count:      int
    gates_used:      list[str]               # lịch sử gate, chống lặp
    bridge_offered:  bool                    # đã bắc cầu chưa
```

### `verbatim` là bắt buộc

Không có `verbatim` thì:
- Bot không thể phản chiếu bằng lời người dùng → quay về "sáo rỗng"
- `INSIGHT_CARD` không dựng được
- Chuyên gia (giai đoạn 2) không audit được suy diễn của bot

---

## 2. `source` — cơ chế an toàn quan trọng nhất

| source | Bot được phép làm gì | Bot **KHÔNG** được làm gì |
|---|---|---|
| `INFERRED` | Chọn câu hỏi tiếp theo (gate `CLARIFY`) | ❌ **Nói ra**. Không phản chiếu, không đặt tên, không đưa kỹ năng dựa trên nó. |
| `SELF_REPORT` | Phản chiếu lại **bằng chính chữ của người dùng** | ❌ Diễn giải thành khái niệm tâm lý |
| `CONFIRMED` | Đặt tên mẫu hình, psychoeducate, đưa kỹ năng | ❌ Gọi là chẩn đoán / bệnh |
| `LIKERT` | Dùng làm ngữ cảnh, mở lời có trọng tâm | ❌ Coi là kết luận về người dùng |

> **Đây là câu trả lời cho "hiểu người dùng nhưng không được phép sai".**
> Bot hiểu — nhưng hiểu một cách **kiểm chứng được và bác bỏ được**.

### Đường nâng cấp source

```
INFERRED  ──(bot hỏi ở gate CLARIFY, user trả lời khẳng định)──▶ SELF_REPORT
SELF_REPORT ──(bot REFLECT, user bấm "Đúng" / gõ xác nhận)────▶ CONFIRMED
LIKERT    ──(user nhắc lại trong hội thoại)───────────────────▶ SELF_REPORT
```

**Không có đường nào đi thẳng từ `INFERRED` sang `CONFIRMED`.**

---

## 3. Quy tắc tính confidence

| Nguồn | Confidence khởi tạo |
|---|---|
| Likert mức 5 | 0.80 |
| Likert mức 4 | 0.65 |
| Likert mức 3 | 0.40 |
| Likert mức 1–2 | 0.15 (ghi nhận nhưng coi như không có) |
| LLM trích, `INFERRED` | theo mô hình trả về, **trần 0.60** |
| Người dùng tự nói rõ, `SELF_REPORT` | 0.75 |
| Người dùng xác nhận, `CONFIRMED` | 0.95 |

**Merge:** khi node đã có evidence và nhận thêm bằng chứng mới:
- `source` mới **mạnh hơn** → thay thế, cộng `turn_ids`, cập nhật `verbatim`
- `source` bằng nhau → `confidence = max(cũ, mới)`, nối `turn_ids`
- `source` yếu hơn → chỉ nối `turn_ids`, giữ nguyên phần còn lại

**Ngưỡng:** `CONFIDENCE_THRESHOLD = 0.70`
> Mượn từ `TurnClassifierServiceImpl.CONFIDENCE_THRESHOLD = 0.75f` của repo VisualEdu — dưới ngưỡng thì **không đoán**, mà đi hỏi.

---

## 4. Năm gate

### 4.1. Bảng gate

| Gate | Điều kiện kích hoạt | Bot làm gì | Nội dung từ đâu |
|---|---|---|---|
| 🔴 `ESCALATE` | Lớp an toàn tất định bắt tầng 1 hoặc 2 | Trả `CRISIS_CARD` | 🔒 Văn bản cứng, **không gọi LLM** |
| `BRIDGE` | `r-suy-giam-chuc-nang` (≥2 Impact) **hoặc** `r-keo-dai` **hoặc** `a-vo-vong` CONFIRMED | Khuyến khích tìm người thật + kịch bản mở lời | 🔒 `resources.yaml` + LLM viết 1 câu dẫn |
| `CLARIFY` | Tổng confidence thấp, hoặc node cao nhất < ngưỡng, hoặc lượt đầu | Hỏi **một** câu mở, nhắm node giá trị thông tin cao nhất | ✅ LLM sinh, trong khuôn skill |
| `REFLECT` | ≥1 node đạt ngưỡng ở `SELF_REPORT`, hoặc cycle hoạt hoá | Nêu thử mẫu hình + **xin xác nhận** | ✅ LLM diễn đạt, bắt buộc dùng `verbatim` |
| `SUPPORT` | ≥1 node `CONFIRMED` **và** đã đi qua `REFLECT` | Kiến thức + **đúng 1** kỹ năng theo policy edge | 🔒 `concepts.yaml` / `coping.yaml` + LLM 1 câu dẫn |

### 4.2. Ưu tiên (cứng, không đổi)

```
ESCALATE  >  BRIDGE  >  CLARIFY  >  REFLECT  >  SUPPORT
```

### 4.3. Luật chống "bot khuyên nhảm"

> **Không được vào `SUPPORT` nếu chưa từng đi qua `REFLECT` được xác nhận.**

Đây là bản dịch của nguyên tắc `"GOAL slot rỗng → không được kết thúc lời giải"` trong `KG_DEMO_CONTEXT.md §7`.

Lý do: đưa lời khuyên cho một vấn đề mà người dùng chưa xác nhận là mình có = **áp đặt**. Đó chính là cơ chế sinh ra câu trả lời sáo rỗng.

---

## 5. Thuật toán quyết định gate

```
def decide_gate(overlay, safety_result, turn_input) -> GateDecision:

    # ── 1. AN TOÀN (đã chạy trước, ở lớp tất định) ──────────────────
    if safety_result.tier in (1, 2):
        return ESCALATE

    # ── 2. BẮC CẦU ─────────────────────────────────────────────────
    impacts = count(evidence where type == impact and confidence >= 0.70)
    if impacts >= 2 or overlay.has("r-keo-dai") or overlay.confirmed("a-vo-vong"):
        if not overlay.bridge_offered:
            return BRIDGE(target = pick_resource(overlay))

    # ── 3. HỖ TRỢ (chỉ khi đã REFLECT + CONFIRMED) ─────────────────
    confirmed = [e for e in evidence if e.source == CONFIRMED]
    if confirmed and "REFLECT" in overlay.gates_used:
        coping = resolve_policy_edge(confirmed)       # 11 policy edge
        return SUPPORT(target = coping, concept = explain_of(confirmed))

    # ── 4. PHẢN CHIẾU ──────────────────────────────────────────────
    if overlay.active_cycles:
        return REFLECT(target = overlay.active_cycles[0], mode = "cycle")

    strong = [e for e in evidence
              if e.confidence >= 0.70 and e.source in (SELF_REPORT, LIKERT)]
    if strong:
        return REFLECT(target = strong[0], mode = "single")

    # ── 5. MẶC ĐỊNH: LÀM RÕ ────────────────────────────────────────
    return CLARIFY(target = highest_information_gain_node(overlay))
```

### `highest_information_gain_node` — chọn hỏi gì

Ưu tiên node thoả cả 3:
1. Là **hàng xóm** của node đã có evidence (không nhảy sang vùng graph trống)
2. Confidence hiện tại **thấp hoặc chưa có**
3. Nằm trên một `cycle` mà các node khác đã sáng ≥ 2

Nếu overlay hoàn toàn rỗng (lượt đầu, không làm test) → hỏi câu mở chung, không nhắm node nào.

---

## 6. Kích hoạt cycle → `INSIGHT_CARD`

```
cycle được coi là HOẠT HOÁ khi:
    số node của cycle có evidence (confidence >= 0.60)  >=  min_nodes_to_activate (4)
```

Khi hoạt hoá, gate `REFLECT` chuyển sang `mode = "cycle"` và dựng `INSIGHT_CARD`:

```
┌─ ĐIỀU MÌNH ĐỂ Ý THẤY ─────────────────────────────┐
│                                                   │
│   "phải được 8 phẩy"            ← verbatim        │
│            ↓                                      │
│   được 6.5 → "mình tệ thật"     ← verbatim        │
│            ↓                                      │
│   thấy có lỗi với ba mẹ         ← verbatim        │
│            ↓                                      │
│   "phải cố hơn nữa"             ← verbatim        │
│            ↓                                      │
│   ... rồi lại quay về đầu                         │
│                                                   │
│   Mình hiểu đúng ý bạn chứ?                       │
│   [ Đúng vậy ]  [ Không hẳn ]                     │
└───────────────────────────────────────────────────┘
```

**Luật dựng card:**
- Mỗi dòng **phải** là `verbatim` từ overlay — không được LLM viết lại
- Nếu một node trên cycle không có `verbatim` → **bỏ dòng đó**, không bịa
- Tối đa 5 dòng
- Luôn kết bằng câu xin xác nhận + 2 chip
- Bấm "Đúng vậy" → toàn bộ node trên cycle nâng lên `CONFIRMED`
- Bấm "Không hẳn" → hạ confidence 0.3, quay lại `CLARIFY`

---

## 7. Luật sinh quick replies (3–5 chip)

> ⚠️ **Số lượng chip đã đổi 08/09/2026.** Luật cũ chốt cứng 2–3 chip mỗi lượt.
> Luật hiện hành là **3–5 chip tuỳ tình huống** — công thức, 5 vai chip, và
> bảng số chip theo từng gate nằm ở [11 Phần E](11-KICH-BAN-CHAT-MAU.md#phần-e--luật-số-lượng-quick-reply-35-chip).
> 7 luật an toàn dưới đây **vẫn giữ nguyên** và áp cho mọi chip, kèm 4 luật bổ
> sung ở §E7. Code: `app/pipeline/quick_reply.py`.

### Vì sao cần

Học sinh 16–18 thường **không gọi tên được cảm xúc của mình**. Chip hạ rào cản diễn đạt và giữ hội thoại trong phạm vi an toàn.

### Cạm bẫy phải tránh

**Gợi ý mang tính mớm (iatrogenic suggestion):** đưa chip *"Mình thấy vô vọng"* cho một người chưa hề nói gì tương tự = **gieo** trạng thái đó vào đầu một đứa trẻ. Hội đồng phản biện tinh ý sẽ hỏi đúng chỗ này.

### 7 luật (bắt buộc)

| # | Luật |
|---|---|
| 1 | Chip sinh từ **node kề với node ĐÃ có evidence**. Không nhảy sang vùng graph chưa có dấu vết. |
| 2 | Chip diễn đạt **mức độ / hướng đi**, không giới thiệu triệu chứng mới. |
| 3 | 🔴 **Không bao giờ** chip nội dung khủng hoảng, tự hại, hay khẳng định bệnh lý. Không chip node có `risk_adjacent: true`. |
| 4 | Luôn có **1 chip thoát**: *"Mình chưa muốn nói về chuyện này"* / *"Không hẳn vậy"*. |
| 5 | Ô nhập text tự do **luôn mở**. Chip là phím tắt, không phải menu ép chọn. |
| 6 | Chip mang **tiền tố hệ thống** để nhận diện tất định khi quay lại (xem [04](04-SAFETY-LAYER.md) §5). |
| 7 | Mỗi chip log kèm `chip_provenance = {gate, source_node, target_node}`. |
| 8 | *(08/09/2026)* Hai chip **cùng một hướng** tính là **một** chip. Đếm chip không bằng đếm lựa chọn — xem [11 §E2](11-KICH-BAN-CHAT-MAU.md#e2-chip-có-5-vai--không-phải-5-câu-chữ-khác-nhau). |
| 9 | *(08/09/2026)* Lượt nào bot **giả định** điều gì thì phải có **chip bác bỏ tiền đề**. |
| 10 | *(08/09/2026)* Chip **không kết thúc bằng dấu chấm**, và không được bắt người dùng tự dán nhãn nặng lên mình. |

### Ví dụ

**ĐÚNG** — gate `CLARIFY`, evidence hiện có: `m-tu-trach` (SELF_REPORT):

```
"Chuyện đó có hay xảy ra không?"        → target: tần suất
"Lúc đó bạn nghĩ gì về bản thân?"       → target: a-gia-tri-thap (node kề)
"Mình chưa muốn nói sâu hơn"            → chip thoát (luật 4)
```

**SAI** — vi phạm luật 2 và 3:

```
❌ "Mình thấy mình vô dụng"              → gieo a-gia-tri-thap
❌ "Mình không muốn sống nữa"            → nội dung khủng hoảng
❌ "Có lẽ mình bị trầm cảm"              → khẳng định bệnh lý
```

---

## 8. Vòng đời overlay

```
POST /api/session
   └─▶ tạo session_id (uuid4), overlay rỗng, Redis SET TTL=86400

POST /api/assessment  (tuỳ chọn)
   └─▶ 10 câu → seed evidence source=LIKERT cho 10 node manifestation

POST /api/chat/stream  (mỗi lượt)
   └─▶ merge evidence → tính cycle → gate → trả lời → ghi log

Sau 24h không hoạt động
   └─▶ Redis tự xoá. Không có bản sao nào khác.
```

> ⚠️ **Phiên ẩn danh: không lưu overlay ra file/DB.** Đây là hồ sơ cảm xúc của trẻ vị thành niên — dữ liệu nhạy cảm theo Nghị định 13/2023/NĐ-CP. Chỉ log lượt chat đã **ẩn danh hoá** (xem [08](08-LOGGING.md)).
>
> **Sửa 07/09/2026 — ngoại lệ có kiểm soát:** người dùng ĐĂNG NHẬP và tự BẬT bộ nhớ thì trọng số node được lưu vào Supabase. Vẫn **không lưu nguyên văn**, không lưu `verbatim`, không lưu lịch sử hội thoại. Xem [12-BO-NHO-DAI-HAN.md](12-BO-NHO-DAI-HAN.md) §2 và §7 (nghĩa vụ theo NĐ 13/2023).

---

## 9. Checklist

- [ ] `overlay/model.py` — Evidence, EvidenceSource, Overlay
- [ ] Bảng confidence khởi tạo theo nguồn
- [ ] Logic merge evidence (3 trường hợp)
- [ ] `overlay/store.py` — Redis get/set với TTL
- [ ] `graph/cycles.py` — dò cycle hoạt hoá
- [ ] `gate/decide.py` — 5 gate + ưu tiên cứng
- [ ] `highest_information_gain_node`
- [ ] `resolve_policy_edge` — 11 cạnh + điều kiện κ
- [ ] Bộ sinh quick replies + 7 luật
- [ ] Test: `INFERRED` không bao giờ lọt vào output
- [ ] Test: không vào `SUPPORT` khi chưa qua `REFLECT`
