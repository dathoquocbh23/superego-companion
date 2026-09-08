# 02 — DOMAIN GRAPH

> **Đây là việc phải làm ĐẦU TIÊN của tuần 1.** Không code — chỉ trích nội dung từ 5 tài liệu vào YAML.
> Toàn bộ ontology đã có sẵn trong corpus của bạn; file này chỉ hệ thống hoá lại.

---

## 1. Hai loại node — phân biệt cho rõ

| Loại | Vai trò | Overlay có theo dõi không? | Bot có nói ra không? |
|---|---|---|---|
| **Evidence node** (24) | Thứ bot *quan sát* được ở người dùng | ✅ Có `confidence` + `source` | ❌ Không bao giờ nói tên node |
| **Content node** (18) | Thứ bot *nói ra* | ❌ Không | ✅ Nội dung duyệt sẵn |

Phân biệt này là cốt lõi: **overlay theo dõi 24 node, corpus phát ngôn qua 18 node.** Không lẫn lộn.

---

## 2. Evidence node (24) — bot theo dõi

### 2.1. Manifestation — Biểu hiện (10 node)

> Nguồn: *NHẬN DIỆN TRONG ĐỜI SỐNG HỌC SINH.docx* — **chính là 10 câu thang Likert**.
> Đây là món quà: bộ đo lường của đề tài đồng thời là ontology của graph. Không phải bịa gì thêm.

| id | Nhãn | Câu Likert gốc |
|---|---|---|
| `m-tu-trach` | Tự trách khi mắc lỗi | "Tôi thường tự trách bản thân khi mắc lỗi." |
| `m-kho-tha-thu` | Khó tha thứ cho bản thân | "Tôi khó tha thứ cho bản thân dù chỉ là sai sót nhỏ." |
| `m-chua-du-tot` | Cảm thấy chưa đủ tốt | "Tôi cảm thấy mình chưa đủ tốt dù đã cố gắng." |
| `m-tieu-chuan-cao` | Đặt tiêu chuẩn rất cao | "Tôi luôn đặt ra tiêu chuẩn rất cao cho bản thân." |
| `m-co-loi-ky-vong` | Có lỗi khi không đáp ứng kỳ vọng | "Tôi cảm thấy có lỗi khi không đáp ứng kỳ vọng của người khác." |
| `m-dang-bi-trach-phat` | Nghĩ mình đáng bị trách phạt | "Tôi thường nghĩ mình đáng bị trách phạt khi thất bại." |
| `m-phai-hoan-hao` | Cảm thấy cần phải hoàn hảo | "Tôi cảm thấy mình cần phải hoàn hảo." |
| `m-xau-ho-khuyet-diem` | Xấu hổ vì khuyết điểm | "Tôi dễ cảm thấy xấu hổ vì những khuyết điểm của bản thân." |
| `m-hiem-hai-long` | Hiếm khi hài lòng với mình | "Tôi hiếm khi hài lòng với chính mình." |
| `m-chi-nho-loi-sai` | Chỉ nhớ lỗi sai | "Tôi thường chỉ nhớ đến những lỗi sai của mình hơn là những điều mình làm tốt." |

### 2.2. Trigger — Bối cảnh kích hoạt (4 node)

> Nguồn: *HIỂU VỀ CÁI SIÊU TÔI TRỪNG PHẠT.docx* §7 + *RỐI LOẠN LO ÂU & TRẦM CẢM.docx* §2

| id | Nhãn |
|---|---|
| `t-diem-so` | Kết quả học tập / điểm số |
| `t-ky-vong-gia-dinh` | Kỳ vọng từ gia đình |
| `t-so-sanh-ban-be` | So sánh với bạn bè |
| `t-thi-cu-tuong-lai` | Thi cử / định hướng tương lai |

### 2.3. Affect — Trạng thái cảm xúc (5 node)

> Nguồn: *RỐI LOẠN LO ÂU & TRẦM CẢM.docx* (triệu chứng WHO) + tài liệu 1

| id | Nhãn | Ghi chú |
|---|---|---|
| `a-toi-loi` | Cảm giác tội lỗi quá mức | Triệu chứng WHO |
| `a-xau-ho` | Xấu hổ | |
| `a-gia-tri-thap` | Cảm nhận bản thân có giá trị thấp | Triệu chứng WHO |
| `a-lo-lang` | Lo lắng / căng thẳng kéo dài | |
| `a-vo-vong` | Cảm giác vô vọng | ⚠️ **Risk-adjacent** — xem §5 |

### 2.4. Impact — Ảnh hưởng chức năng (5 node)

> Nguồn: *KHI NÀO CẦN TÌM HỖ TRỢ.docx* §2

| id | Nhãn |
|---|---|
| `i-kho-tap-trung` | Khó tập trung |
| `i-roi-loan-giac-ngu` | Khó ngủ / rối loạn giấc ngủ |
| `i-ne-tranh` | Né tránh bài tập, kiểm tra, cơ hội mới |
| `i-mat-dong-luc` | Mất động lực học tập |
| `i-thu-minh` | Thu mình, cô lập |

---

## 3. Content node (18) — bot phát ngôn

### 3.1. Concept — Khái niệm (4 node)

> Nguồn: *HIỂU VỀ CÁI SIÊU TÔI TRỪNG PHẠT.docx*

| id | Nội dung lấy từ |
|---|---|
| `c-id-ego-superego` | §2 — ba thành tố, ví dụ "ngày mai kiểm tra nhưng muốn chơi game" |
| `c-lanh-manh-vs-trung-phat` | §5 — **bảng phân biệt 8 dòng**. Đây là nội dung mạnh nhất của corpus. |
| `c-vong-lap-tu-phe-phan` | *KHI NÀO CẦN TÌM HỖ TRỢ.docx* §5 — chuỗi vòng lặp |
| `c-khong-phai-chan-doan` | §7 + lưu ý cuối tài liệu 4a — "không dán nhãn, không phải bệnh" |

### 3.2. Coping — Kỹ năng ứng phó (6 node)

> Nguồn: *CÁC CÁCH KHẮC PHỤC TẠI NHÀ.docx*

| id | Nhãn | Lấy từ mục |
|---|---|---|
| `k-nhan-dien-tu-phe-phan` | Nhận diện hành vi tự cản trở | Self-sabotage §1 |
| `k-tu-tran-an` | Thực hành lòng trắc ẩn với bản thân | Self-sabotage §3 |
| `k-growth-mindset` | Thay đổi tư duy về thất bại | Self-sabotage §4 |
| `k-chia-nho-muc-tieu` | Xây tự tin từ những bước nhỏ | Self-sabotage §5 |
| `k-chanh-niem` | Chánh niệm / hít thở sâu | Self-sabotage §6 + Xả stress §6.3 |
| `k-ghi-nhan-tich-cuc` | Ghi nhận điều tích cực (3 điều mỗi ngày) | Xả stress §1 |

> ⚠️ Tài liệu có 18 cách xả stress. **Chỉ đưa 6 vào graph.** Bot không bao giờ dump danh sách — mỗi lượt đúng **một** kỹ năng, chọn theo policy edge.

### 3.3. RiskFlag — Cờ cảnh báo (3 node)

> Nguồn: *KHI NÀO CẦN TÌM HỖ TRỢ.docx* §2–4

| id | Điều kiện kích hoạt |
|---|---|
| `r-keo-dai` | Người dùng nhắc tới mốc thời gian ≥ 2 tuần |
| `r-suy-giam-chuc-nang` | ≥ 2 node Impact có evidence |
| `r-y-nghi-tu-hai` | 🔴 Lớp an toàn tất định bắt được — xem [04](04-SAFETY-LAYER.md) |

### 3.4. Resource — Nguồn hỗ trợ (5 node)

> Nguồn: *KHI NÀO CẦN TÌM HỖ TRỢ.docx* §6 + danh bạ cuối tài liệu

| id | Nội dung |
|---|---|
| `s-gvcn` | Giáo viên chủ nhiệm — kèm câu mở lời mẫu |
| `s-tu-van-hoc-duong` | Phòng tư vấn tâm lý học đường |
| `s-ba-me` | Ba mẹ — **kèm nguyên văn kịch bản lời thoại** trong tài liệu |
| `s-hotline` | 🔴 Hotline sơ cứu tâm lý **0832000202** |
| `s-phong-kham` | Danh bạ phòng khám / bệnh viện TP.HCM |

---

## 4. Cạnh (edges)

### 4.1. Các loại cạnh

```
Trigger  --triggers-->    Manifestation
Manifestation --produces--> Affect
Affect   --impairs-->     Impact
Impact   --reinforces-->  Manifestation          ← ĐÓNG VÒNG LẶP

Manifestation --explained_by--> Concept
Manifestation --addressed_by[priority, condition]--> Coping    ← POLICY EDGE
Impact + RiskFlag --escalates_to--> Resource
```

### 4.2. Vòng lặp cốt lõi

> Tài liệu *KHI NÀO CẦN TÌM HỖ TRỢ.docx* §5 đã viết sẵn nguyên văn:
> *"Tiêu chuẩn quá khắt khe → Không đạt tiêu chuẩn → Tự phê phán → Tội lỗi/xấu hổ → Cảm thấy bản thân kém giá trị → Căng thẳng → Càng cố gắng hoàn hảo → Lại tự phê phán"*

Ánh xạ sang node:

```
m-tieu-chuan-cao
      ↓ triggers
   t-diem-so  (không đạt)
      ↓ triggers
   m-tu-trach
      ↓ produces
   a-toi-loi ／ a-xau-ho
      ↓ produces
   a-gia-tri-thap
      ↓ produces
   a-lo-lang
      ↓ reinforces
   m-phai-hoan-hao
      ↓ ──────────── quay về m-tu-trach
```

**Đây là tài sản lớn nhất của sản phẩm.** Khi overlay thắp sáng ≥ 4 node trên chu trình này, bot dựng được `INSIGHT_CARD` — vẽ đúng vòng lặp của em ấy **bằng chính lời em ấy đã nói**. Đó là khoảnh khắc demo.

### 4.3. Policy edge (11 cạnh) — thứ giết "sáo rỗng"

Cấu trúc: `từ_node --addressed_by[priority, condition κ]--> coping_node`

| # | Biểu hiện | Điều kiện κ | Kỹ năng ưu tiên | Vì sao |
|---|---|---|---|---|
| 1 | `i-ne-tranh` | có `m-dang-bi-trach-phat` hoặc `a-xau-ho` | `k-chia-nho-muc-tieu` | Né tránh do sợ thất bại → cần chiến thắng nhỏ, không cần thiền |
| 2 | `m-tieu-chuan-cao` | — | `k-growth-mindset` | Đổi cách nhìn thất bại là gốc |
| 3 | `m-phai-hoan-hao` | — | `k-growth-mindset` | Cùng cơ chế |
| 4 | `m-tu-trach` | — | `k-tu-tran-an` | Lòng trắc ẩn đối trọng trực tiếp với tự trách |
| 5 | `m-kho-tha-thu` | — | `k-tu-tran-an` | Cùng cơ chế |
| 6 | `m-chi-nho-loi-sai` | — | `k-ghi-nhan-tich-cuc` | Bài tập 3 điều tốt/ngày nhắm đúng thiên lệch chú ý |
| 7 | `m-hiem-hai-long` | — | `k-ghi-nhan-tich-cuc` | Cùng cơ chế |
| 8 | `a-lo-lang` | có `i-roi-loan-giac-ngu` | `k-chanh-niem` | Lo âu + mất ngủ → hít thở sâu là can thiệp phù hợp nhất |

**Luật chọn:** khi nhiều cạnh cùng khớp → chọn cạnh có `priority` cao nhất; hoà → chọn cạnh xuất phát từ node có `confidence` cao nhất.

---

## 5. Node risk-adjacent — xử lý riêng

`a-vo-vong` (cảm giác vô vọng) là **triệu chứng trầm cảm theo WHO**, và là hàng xóm của ý nghĩ tự hại.

**Luật:**
- Khi `a-vo-vong` đạt `CONFIRMED` → **ép gate = `BRIDGE`**, bất kể trạng thái khác
- **Không bao giờ** sinh quick reply chạm vào node này
- Không đưa `COPING` như câu trả lời chính cho `a-vo-vong` — bắc cầu tới người thật trước

---

## 6. Truy xuất tri thức: graph-first, KHÔNG vector

**Quyết định:** mỗi content node **mang sẵn đoạn văn đã trích từ corpus**. Truy xuất = duyệt graph, không tính cosine similarity.

| | Vector RAG | Graph-first (chọn cái này) |
|---|---|---|
| Biết trước bot sẽ nói gì | ❌ Không | ✅ Có, theo từng node |
| Chuyên gia duyệt được | 🟡 Phải duyệt cả corpus | ✅ Duyệt đúng 18 đoạn |
| Truy vết nguồn | 🟡 Xấp xỉ | ✅ Chính xác đến dòng |
| Nguy cơ lôi ra đoạn lạ | 🔴 Có | ✅ Không thể |
| Công sức | Cao (chunk, embed, index) | Thấp (chép vào YAML) |

Câu hỏi tự do ngoài graph → **từ chối lịch sự** (`99_REFUSAL.md`), không cố trả lời.

---

## 7. Schema YAML

```yaml
# data/domain_graph.yaml
version: "1.0"
reviewed_by: null          # giai đoạn 2: tên chuyên gia + ngày duyệt

nodes:
  - id: m-tu-trach
    type: manifestation
    label: "Tự trách khi mắc lỗi"
    likert_item: 1
    source_doc: "NHẬN DIỆN TRONG ĐỜI SỐNG HỌC SINH.docx"
    # gợi ý cho bước TRÍCH bằng chứng — KHÔNG hiển thị cho người dùng
    cues:
      - "tự trách"
      - "tại mình"
      - "lỗi của mình"
      - "mình dở quá"

  - id: a-vo-vong
    type: affect
    label: "Cảm giác vô vọng"
    risk_adjacent: true          # ⚠️ ép BRIDGE khi CONFIRMED
    source_doc: "RỐI LOẠN LO ÂU & TRẦM CẢM.docx"
    cues: ["vô vọng", "chẳng còn hy vọng", "mãi mãi vậy thôi"]

  - id: c-lanh-manh-vs-trung-phat
    type: concept
    label: "Siêu tôi lành mạnh vs trừng phạt"
    content_ref: "content/concepts.yaml#lanh-manh-vs-trung-phat"

  - id: k-tu-tran-an
    type: coping
    label: "Lòng trắc ẩn với bản thân"
    content_ref: "content/coping.yaml#tu-tran-an"

edges:
  - from: t-diem-so
    to: m-tu-trach
    type: triggers

  - from: m-tu-trach
    to: a-toi-loi
    type: produces

  - from: a-lo-lang
    to: m-phai-hoan-hao
    type: reinforces           # cạnh đóng vòng lặp

  - from: m-tu-trach
    to: k-tu-tran-an
    type: addressed_by
    priority: 10
    condition: null

  - from: i-ne-tranh
    to: k-chia-nho-muc-tieu
    type: addressed_by
    priority: 20
    condition:                 # κ — chỉ áp dụng khi thoả
      any_of: [m-dang-bi-trach-phat, a-xau-ho]

cycles:                        # khai báo tường minh để cycles.py không phải tự dò
  - id: cycle-tu-phe-phan
    label: "Vòng lặp tự phê phán"
    nodes:
      - m-tieu-chuan-cao
      - t-diem-so
      - m-tu-trach
      - a-toi-loi
      - a-gia-tri-thap
      - a-lo-lang
      - m-phai-hoan-hao
    min_nodes_to_activate: 4   # ≥4 node có evidence → đủ dựng INSIGHT_CARD
```

## 8. Schema nội dung

```yaml
# data/content/coping.yaml
tu-tran-an:
  title: "Thử đối xử với mình như với một người bạn"
  body: |
    Sự tự trách móc chỉ làm trầm trọng thêm tình trạng tự hủy hoại.
    Thay vì trừng phạt bản thân vì đã làm hỏng việc, hãy đối xử với chính
    mình như cách bạn đối xử với một người bạn thân.
  action: "Lần tới khi bạn định tự trách, thử hỏi: nếu bạn mình gặp chuyện này, mình sẽ nói gì với bạn ấy?"
  source: "CÁC CÁCH KHẮC PHỤC TẠI NHÀ.docx — mục 3"
```

> **Luật:** trường `body` là **nguyên văn hoặc gần nguyên văn** tài liệu. Không diễn giải lại. Đây là điều giữ cho sản phẩm an toàn khi chưa có chuyên gia.

---

## 9. Checklist tuần 1 — Graph

- [ ] Tạo `data/domain_graph.yaml` với đủ **24 evidence node**
- [ ] Thêm `cues` cho từng evidence node (3–6 cụm từ tiếng Việt mỗi node)
- [ ] Thêm **18 content node** + `content_ref`
- [ ] Viết `data/content/concepts.yaml` (4 mục, trích nguyên văn)
- [ ] Viết `data/content/coping.yaml` (6 mục, trích nguyên văn)
- [ ] Viết `data/content/resources.yaml` (5 mục, gồm hotline + danh bạ)
- [ ] Khai báo cạnh: `triggers`, `produces`, `impairs`, `reinforces`
- [ ] Khai báo **11 policy edge** với `priority` + `condition`
- [ ] Khai báo `cycle-tu-phe-phan`
- [ ] Đọc lại toàn bộ: **có câu nào nghe như chẩn đoán không?** Có → sửa.
