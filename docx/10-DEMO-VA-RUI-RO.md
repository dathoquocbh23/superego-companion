# 10 — KỊCH BẢN DEMO, RỦI RO & GIAI ĐOẠN 2

---

## 1. Bốn kịch bản demo

> Mỗi kịch bản chứng minh **đúng một điều**. Không gộp, không lan man.
> Tập trước, quay video dự phòng.

### Kịch bản 1 — Phát hiện vòng lặp ⭐ (kịch bản chính)

**Chứng minh:** bot tích luỹ hiểu biết qua các lượt và nhận ra mẫu hình.

```
HS:  hôm nay thi được 6.5, chán quá
BOT: [CLARIFY] Bạn kỳ vọng mình được bao nhiêu?

HS:  ít nhất phải 8 phẩy chứ
BOT: [CLARIFY] Nếu không đạt được con số đó thì bạn thường nghĩ gì về mình?

HS:  thì mình tệ thật chứ sao, học mãi mà vẫn vậy
BOT: [CLARIFY] Lúc đó cảm giác nặng nhất là gì?

HS:  thấy có lỗi với ba mẹ, tốn tiền học thêm mà có được gì đâu
BOT: [REFLECT — INSIGHT_CARD]
     ┌─ ĐIỀU MÌNH ĐỂ Ý THẤY ────────────────┐
     │  "ít nhất phải 8 phẩy"               │
     │            ↓                          │
     │  "mình tệ thật chứ sao"              │
     │            ↓                          │
     │  "thấy có lỗi với ba mẹ"             │
     │            ↓                          │
     │  "học mãi mà vẫn vậy"                │
     │            ↓                          │
     │  ... rồi lại quay về đầu             │
     │                                       │
     │  Mình hiểu đúng ý bạn chứ?           │
     │  [Đúng vậy] [Không hẳn]              │
     └───────────────────────────────────────┘

HS:  [bấm Đúng vậy]
BOT: [SUPPORT] + COPING_CARD (k-growth-mindset theo policy edge)
```

**Câu chốt khi thuyết trình:**
> *"Không câu nào trong thẻ này do AI viết ra. Cả 4 dòng đều là nguyên văn học sinh vừa nói — hệ thống chỉ nối chúng lại theo đúng vòng lặp đã mô tả trong tài liệu nghiên cứu."*

---

### Kịch bản 2 — Cá nhân hoá

**Chứng minh:** cùng một câu hỏi, hai câu trả lời khác nhau — hết sáo rỗng.

Chuẩn bị sẵn **2 phiên** với overlay khác nhau (làm test Likert khác nhau):

| | Học sinh A | Học sinh B |
|---|---|---|
| Overlay nổi bật | `m-dang-bi-trach-phat`, `i-ne-tranh` | `m-tieu-chuan-cao`, `m-phai-hoan-hao` |
| Cùng gõ | *"em không làm nổi bài tập"* | *"em không làm nổi bài tập"* |
| Policy edge khớp | #1 → `k-chia-nho-muc-tieu` | #2 → `k-growth-mindset` |
| Bot trả lời | Chia nhỏ mục tiêu, chiến thắng nhỏ | Nhìn lại cách định nghĩa "làm được" |

**Câu chốt:**
> *"Cùng một câu, hai câu trả lời. Không phải do mô hình ngẫu nhiên — mà do policy edge trong graph chọn đúng kỹ năng cho đúng biểu hiện."*

---

### Kịch bản 3 — Bắc cầu tự động

**Chứng minh:** bot chủ động đẩy về phía người thật, không giữ người dùng lại.

```
HS:  mấy tuần nay em không ngủ được, sáng dậy chẳng muốn đi học
     bài vở thì bỏ đó không đụng tới
     → khớp i-roi-loan-giac-ngu + i-mat-dong-luc + i-ne-tranh (3 Impact)
     → "mấy tuần nay" → r-keo-dai

BOT: [BRIDGE — ép gate, không đợi được hỏi]
     1–2 câu dẫn + BRIDGE_CARD (kịch bản nói với ba mẹ, nguyên văn tài liệu)
```

**Câu chốt:**
> *"Ngưỡng này do luật quyết định, không do mô hình cảm thấy. Hai dấu hiệu ảnh hưởng chức năng cộng với yếu tố kéo dài là hệ thống bắc cầu — dù học sinh không hỏi."*

---

### Kịch bản 4 — Test an toàn (làm TRỰC TIẾP trên sân khấu)

**Chứng minh:** ranh giới an toàn là cứng, không phụ thuộc AI.

```
Gõ một câu có tín hiệu tầng 1
   → CRISIS_CARD bật NGAY LẬP TỨC (không có độ trễ streaming)
   → hotline 0832000202, bấm gọi được
```

**Câu chốt:**
> *"Chú ý độ trễ — bằng không. Vì câu này không đi qua mô hình ngôn ngữ. Nó khớp một danh sách cụm từ và trả về văn bản cố định đã soạn sẵn. Chúng em không đánh cược tính mạng vào một lời gọi API."*

> 💡 Đây thường là khoảnh khắc thuyết phục nhất với hội đồng. Đừng bỏ.

---

## 2. Chuẩn bị demo

- [ ] Kiểm môi trường trước **2 tiếng**: Redis chạy? API key còn hạn? mạng phòng hội đồng?
- [ ] **Video dự phòng 4 kịch bản** mở sẵn ở tab bên cạnh
- [ ] 2 phiên đã seed sẵn cho kịch bản 2
- [ ] Điện thoại thật để demo `tel:` link
- [ ] Bảng kết quả red-team in ra giấy

---

## 3. Câu hỏi khó & cách trả lời

| Câu hỏi | Trả lời |
|---|---|
| *"Khác gì gọi ChatGPT?"* | Ba điểm: (1) LLM không quyết định an toàn — khủng hoảng chặn ở lớp luật cứng; (2) mọi nội dung tâm lý là văn bản trích từ WHO/NIMH/APA, mô hình không sáng tác lời khuyên; (3) hệ thống tích luỹ bằng chứng có `verbatim` và truy vết được — sai chỗ nào chỉ ra được chỗ đó. |
| *"Ai duyệt nội dung?"* | Thẳng thắn: **chưa có chuyên gia** ở giai đoạn này. Vì vậy đã thu hẹp vai trò LLM xuống còn hỏi và phản chiếu; mọi nội dung tâm lý là trích nguyên văn từ tài liệu có nguồn. Thuê chuyên gia là bước đầu tiên của giai đoạn 2. |
| *"Nếu AI nói sai thì sao?"* | Ba lớp chặn: gate ràng buộc nội dung, post-check chặn ngôn ngữ chẩn đoán, và bằng chứng `INFERRED` không bao giờ được phát ngôn. Cho xem bảng red-team 40 prompt. |
| *"Học sinh lệ thuộc vào bot thì sao?"* | Gate `BRIDGE` tự kích hoạt theo ngưỡng khách quan, không đợi được hỏi. Bot không nhớ người dùng giữa các phiên — chủ ý để không hình thành quan hệ gắn bó. |
| *"Có thu thập dữ liệu học sinh không?"* | Không đăng nhập, không PII. Overlay chỉ sống 24h trong Redis. Log **không chứa nội dung hội thoại** — chỉ metadata và định danh node. |
| *"Đã thử với học sinh thật chưa?"* | Chưa — và đó là **chủ ý**. Thử nghiệm trên trẻ vị thành niên cần hội đồng đạo đức duyệt + đồng thuận phụ huynh. Đó là nội dung giai đoạn 2. |
| *"Sao chỉ 24 node?"* | Đây là demo slice có chủ đích. 24 node đến trực tiếp từ thang đo 10 câu và các triệu chứng WHO trong tài liệu — không bịa ontology. Mở rộng cần chuyên gia. |

---

## 4. Bảng rủi ro

| Rủi ro | Mức | Cách chặn |
|---|---|---|
| Bot nói câu mang tính chẩn đoán | 🔴 Cao | Post-check chặn cứng + skill cấm tuyệt đối + LLM không sáng tác nội dung |
| Bỏ sót tín hiệu khủng hoảng | 🔴 Cao | 3 tầng phrase list, ưu tiên recall, không xử lý phủ định, red-team 40 prompt |
| Chip mớm triệu chứng | 🟠 TB | 7 luật sinh chip, cấm node `risk_adjacent`, luôn có chip thoát |
| Kết quả test gây sốc (band CAO) | 🟠 TB | Luôn có nút vào chat, không bao giờ là màn hình cuối |
| Học sinh lệ thuộc | 🟠 TB | Không nhớ giữa phiên, gate `BRIDGE` tự kích hoạt |
| Trễ deadline | 🟠 TB | Danh sách cắt theo thứ tự ([09](09-TIMELINE.md)) |
| LLM lỗi/timeout lúc demo | 🟡 Thấp | Video dự phòng + câu tĩnh khi lỗi |
| Graph phình to | 🟡 Thấp | Khoá cứng 24 evidence node |
| Rò rỉ dữ liệu nhạy cảm | 🟡 Thấp | Không PII, không log nội dung, TTL 24h |

---

## 5. Giai đoạn 2 — chuẩn bị từ bây giờ

### 5.1. Việc phải làm sau khi pass vòng trường

| Thứ tự | Việc | Ghi chú |
|---|---|---|
| 1 | **Thuê chuyên gia tâm lý** | Duyệt: 18 content node, 6 skill, phrase list, kịch bản `BRIDGE` |
| 2 | **Hội đồng đạo đức của trường/khoa** | Bắt buộc — đối tượng là trẻ vị thành niên |
| 3 | **Đồng thuận phụ huynh + đồng thuận học sinh** | Hai văn bản riêng |
| 4 | **Xin phép qua nhà trường** | Trường làm trung gian, không tiếp cận trực tiếp |
| 5 | **Mã tham gia ẩn danh** | Xem §5.2 |
| 6 | Pilot 30–50 học sinh | |
| 7 | Phân tích + viết báo cáo | |

### 5.2. ⚠️ Mã tham gia ẩn danh — thiết kế trước

Không đăng nhập thì **không ghép được pre/post của cùng một người**.

Giải pháp cho giai đoạn 2 (**không** phải tài khoản):
```
Hệ thống sinh mã: HS-4821
Học sinh ghi lại / chụp màn hình
Nhập lại mã đó ở lần đo sau  →  ghép được pre/post
Mã KHÔNG liên kết với tên, lớp, hay bất kỳ PII nào
```

Ghi nhớ để không phải đập lại schema.

### 5.3. Bộ chỉ số đo

| Khía cạnh | Công cụ | Ghi chú |
|---|---|---|
| Tính khả dụng | **SUS** (10 câu) | Chuẩn quốc tế, dễ biện luận |
| Mức chấp nhận | **TAM** hoặc UTAUT rút gọn | Perceived usefulness / ease of use |
| Chất lượng nội dung | Rubric tự xây, **2 chuyên gia** chấm transcript | Báo cáo Cohen's κ |
| An toàn khủng hoảng | Bộ test đối kháng mở rộng (~100 prompt) | Recall là chỉ số chính |
| Nhận thức người dùng | Bảng hỏi tự xây, pre/post | ⚠️ **Không** dùng thang lâm sàng |
| Hiệu quả graph | Số lượt tới `CONFIRMED` đầu tiên | Từ log ([08](08-LOGGING.md) §3) |

> ⚠️ **Tuyệt đối không hứa đo "hiệu quả lâm sàng"** (giảm trầm cảm/lo âu). Quá tầm và nặng về đạo đức. Chỉ đo nhận thức, khả dụng, chấp nhận, chất lượng nội dung, an toàn.

### 5.4. Hướng phát triển sau đó

- Mở rộng graph với chuyên gia (24 → 60+ node)
- Overlay dài hạn **có đồng thuận** → theo dõi tiến triển
- Dashboard cho phòng tư vấn học đường (tổng hợp ẩn danh, **không** hồ sơ cá nhân)
- Đo chất lượng gate: chuyên gia gán nhãn gate "đúng" → so với gate hệ thống chọn

---

## 6. Nhắc cuối

Sản phẩm này chạm vào cảm xúc của trẻ vị thành niên. Khi phân vân giữa **"làm thêm tính năng"** và **"làm an toàn hơn"** — luôn chọn vế sau.

Một chatbot đơn giản mà an toàn thì bảo vệ được. Một chatbot thông minh mà nói sai một câu với một đứa trẻ thì không.
