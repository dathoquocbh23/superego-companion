# 00 — TỔNG QUAN & QUYẾT ĐỊNH ĐÃ CHỐT

## 1. Định vị sản phẩm

**Tên gọi tạm:** Trợ lý tâm lý giáo dục cho học sinh THPT

**Là gì:**
- Công cụ **tâm lý giáo dục** (psychoeducation) giúp học sinh nhận diện xu hướng tự phê phán quá mức
- Nơi để nói ra điều khó nói mà không bị phán xét
- **Cầu nối** tới người hỗ trợ thật (thầy cô, phòng tư vấn, ba mẹ, chuyên gia)

**KHÔNG phải là gì:**
- ❌ Công cụ chẩn đoán tâm lý
- ❌ Trị liệu / thay thế chuyên gia
- ❌ Dịch vụ cấp cứu tâm lý
- ❌ "Người bạn thân" để học sinh gắn bó thay cho quan hệ thật

> **Ghi nhớ khi viết mọi câu chữ trong sản phẩm:** Punitive Superego là một **khái niệm lý thuyết phân tâm học**, không phải một chẩn đoán. Luôn dùng *"khi có biểu hiện của…"*, không bao giờ dùng *"khi mắc…"*.

---

## 2. Năm quyết định đã chốt

| # | Quyết định | Hệ quả thiết kế |
|---|---|---|
| 1 | **Chưa thuê chuyên gia** ở giai đoạn demo (pass vòng trường mới thuê) | LLM **không được sáng tác nội dung tâm lý**. Mọi lời khuyên/kiến thức là văn bản trích sẵn từ 5 tài liệu. Xem §4. |
| 2 | ~~**Không đăng nhập**~~ → **Đăng nhập TUỲ CHỌN** *(sửa 07/09/2026)* | Mặc định vẫn là phiên ẩn danh, overlay sống trong Redis TTL 24h. Đăng nhập Supabase mở thêm **bộ nhớ dài hạn theo graph** — opt-in, xem [12](12-BO-NHO-DAI-HAN.md). Không đăng nhập thì hành vi y hệt trước. |
| 3 | **Bài test Likert là tuỳ chọn**, không phải cửa ải | Hai lối vào: "Trò chuyện ngay" và "Thử bài tự đánh giá". Kết quả test **luôn nối tiếp sang chat**, không dừng ở màn hình điểm. |
| 4 | **Không làm đồ hoạ vòng lặp** | Thay bằng `INSIGHT_CARD` dạng text — mũi tên nối các câu **nguyên văn người dùng đã nói**. Chi phí gần bằng 0, giữ được điểm nhấn. |
| 5 | **Deadline 30/09/2026** (~24 ngày) | Cắt scope mạnh. Xem [09-TIMELINE.md](09-TIMELINE.md). |

---

## 3. Năm nguyên tắc bất di bất dịch

> Đây là các luật **không được vi phạm dù cháy deadline**. Mượn từ `KG_DEMO_CONTEXT.md §7` của dự án VisualEdu, dịch sang domain tâm lý.

1. **LLM không quyết định an toàn.** Phát hiện khủng hoảng là luật cứng (chuỗi ký tự + ngưỡng), chạy **trước** mọi lời gọi mô hình.

2. **Bot không nói ra nhận định nào về người dùng nếu nhận định đó không có node + bằng chứng trong graph.**

3. **Bằng chứng do LLM suy diễn (`INFERRED`) tuyệt đối không được phát ngôn.** Chỉ dùng để chọn câu hỏi tiếp theo. Muốn nói ra → phải qua `REFLECT` và được người dùng xác nhận.

4. **Mọi lượt ghi log có cấu trúc**: `gate_action`, `target_nodes`, `evidence_delta`, `chip_provenance`, `safety_flags`. Log này vừa để debug, vừa là dataset cho giai đoạn 2.

5. **Mọi thứ hiển thị cho người dùng phải đi qua lớp kiểm hậu kỳ** (chặn ngôn ngữ chẩn đoán, khẳng định y khoa, hứa hẹn).

---

## 4. Quy tắc vàng khi chưa có chuyên gia

**Vấn đề:** không có ai đủ chuyên môn duyệt những gì bot nói ra.

**Giải pháp:** thu hẹp vai trò LLM xuống hai việc nó không thể gây hại — **hỏi** và **nhắc lại lời chính người dùng**.

| Gate | Nội dung đến từ đâu | LLM được làm gì |
|---|---|---|
| `ESCALATE` | 🔒 Nguyên văn tài liệu *KHI NÀO CẦN TÌM HỖ TRỢ* | **Không gọi LLM** |
| `SUPPORT` (kiến thức + kỹ năng) | 🔒 Nguyên văn tài liệu *HIỂU VỀ CÁI SIÊU TÔI TRỪNG PHẠT*, *RỐI LOẠN LO ÂU & TRẦM CẢM*, *CÁC CÁCH KHẮC PHỤC TẠI NHÀ* | Chỉ viết **1 câu dẫn** vào card |
| `BRIDGE` | 🔒 Nguyên văn tài liệu *KHI NÀO CẦN TÌM HỖ TRỢ* §6 | Chỉ viết **1 câu dẫn** |
| `CLARIFY` | LLM sinh câu hỏi | ✅ Tự do trong khuôn: 1 câu, mở, không mớm triệu chứng |
| `REFLECT` | LLM diễn đạt, **bắt buộc dùng lại verbatim của user** | ✅ Trong khuôn |

**Ba biện pháp bù trừ:**

1. **Banner thường trực** trên mọi màn hình:
   > *"Sản phẩm demo học thuật — nội dung tổng hợp từ WHO/NIMH/APA, chưa qua thẩm định chuyên môn độc lập. Không thay thế tư vấn tâm lý."*

2. **Không mời học sinh thật dùng thử trước khi pass vòng trường.** Demo bằng chính thành viên nhóm đóng vai. Cho bạn cùng lớp thử = đã là phơi nhiễm người thật, hội đồng có quyền chất vấn về đạo đức.

3. **Quay video kịch bản demo dự phòng** — không phụ thuộc bot ứng biến trực tiếp trên sân khấu.

---

## 5. Phạm vi demo

### LÀM

| Hạng mục | Quy mô |
|---|---|
| Trang chủ 2 lối vào | 1 trang |
| Bài tự đánh giá Likert 10 câu + 4 mức kết quả | 1 trang |
| Giao diện chat | Port từ repo `front-end` |
| Domain graph | **42 node** (24 evidence + 18 content) |
| Policy edge | 11 cạnh *(8 gốc + 3 nhánh xấu hổ / giá trị bản thân thấp, sửa 07/09/2026)* |
| Gate | **5** — `ESCALATE` / `CLARIFY` / `REFLECT` / `SUPPORT` / `BRIDGE` |
| Skill file | 7 file `.md` *(thêm `14_SUPPORT.md` 07/09/2026)* |
| Loại bubble | 6 loại |
| Quick replies | 2–3 chip mỗi lượt, có chip thoát |
| Lớp an toàn tất định | Danh sách cụm từ tiếng Việt 3 tầng |
| Log có cấu trúc | JSONL |

### KHÔNG LÀM

- ❌ Đăng nhập / tài khoản / hồ sơ dài hạn
- ❌ Vector search / RAG embedding (graph-first thuần — xem [02](02-DOMAIN-GRAPH.md) §6)
- ❌ Neo4j, Kafka, Mongo, microservice
- ❌ Đồ hoạ SVG vòng lặp
- ❌ Voice / mobile app
- ❌ Đa ngôn ngữ
- ❌ Dashboard quản trị
- ❌ Ghi nhớ người dùng giữa các phiên

---

## 6. Vì sao cần graph (câu trả lời cho hội đồng)

Nếu bị hỏi *"khác gì gọi thẳng ChatGPT?"*:

| Chatbot RAG thường | Sản phẩm này |
|---|---|
| Mỗi lượt độc lập, truy xuất tài liệu rồi trả lời | Tích luỹ bằng chứng qua các lượt vào overlay |
| Ai hỏi cũng nhận lời khuyên giống nhau → **sáo rỗng** | Chọn kỹ năng theo **policy edge** khớp đúng biểu hiện của người này |
| Không ai biết trước mô hình sẽ nói gì | Mỗi câu truy vết được về node → tài liệu nguồn |
| "Hiểu" người dùng theo cách không kiểm chứng được | Overlay có `verbatim` + `source` → chuyên gia mở ra audit được, và **bác bỏ được** |
| Không có ranh giới an toàn cứng | Khủng hoảng chặn ở lớp tất định, trước LLM |

---

## 7. Đối tượng & bối cảnh

- **Người dùng:** học sinh THPT 16–18 tuổi tại TP.HCM
- **Ngôn ngữ:** tiếng Việt toàn bộ
- **Giọng:** ấm, ngang hàng, không giảng đạo, không dùng "thầy/cô", xưng "mình" – gọi "bạn"
- **Độ dài trả lời:** 2–5 câu. Dài hơn là sai thiết kế.
