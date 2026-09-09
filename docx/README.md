# KẾ HOẠCH TRIỂN KHAI — Chatbot đồng hành "Cái siêu tôi trừng phạt"

> Bộ tài liệu kế hoạch cho sản phẩm demo NCKH. Đọc theo thứ tự số.
> Ngày lập: 06/09/2026 · Deadline demo vòng trường: **30/09/2026** (~24 ngày)

---

## Đọc theo thứ tự nào

| File | Nội dung | Khi nào đọc |
|---|---|---|
| [00-TONG-QUAN.md](00-TONG-QUAN.md) | Định vị sản phẩm, quyết định đã chốt, nguyên tắc bất di bất dịch, phạm vi | **Đọc đầu tiên** |
| [01-KIEN-TRUC.md](01-KIEN-TRUC.md) | Stack, sơ đồ hệ thống, cấu trúc thư mục, luồng 1 lượt chat | Trước khi code |
| [02-DOMAIN-GRAPH.md](02-DOMAIN-GRAPH.md) | Đặc tả 42 node + cạnh + policy edge + schema YAML | **Tuần 1 — làm trước tiên** |
| [03-OVERLAY-VA-GATE.md](03-OVERLAY-VA-GATE.md) | Mô hình bằng chứng, 5 gate, thuật toán quyết định | Tuần 1–2 |
| [04-SAFETY-LAYER.md](04-SAFETY-LAYER.md) | Phát hiện khủng hoảng tiếng Việt, chặn hậu kỳ, nội dung CRISIS_CARD | **Tuần 1 — ưu tiên ngang graph** |
| [05-SKILL-FILES.md](05-SKILL-FILES.md) | Đặc tả 6 file skill .md | Tuần 1 |
| [06-BACKEND.md](06-BACKEND.md) | FastAPI: module, endpoint, hợp đồng LLM, SSE | Tuần 2 |
| [07-FRONTEND.md](07-FRONTEND.md) | Next.js: trang, component port từ repo cũ, card mới | Tuần 3 |
| [08-LOGGING.md](08-LOGGING.md) | Schema log — dataset cho giai đoạn 2 | Tuần 2 |
| [09-TIMELINE.md](09-TIMELINE.md) | Kế hoạch 24 ngày, checklist, đường găng, danh sách cắt | **Bám hằng ngày** |
| [10-DEMO-VA-RUI-RO.md](10-DEMO-VA-RUI-RO.md) | Kịch bản demo, bảng rủi ro, chuẩn bị giai đoạn 2 | Tuần 4 |
| [11-KICH-BAN-CHAT-MAU.md](11-KICH-BAN-CHAT-MAU.md) | **Kịch bản chat đầy đủ để duyệt** — lời thoại + trạng thái nội bộ + checklist duyệt | **Đọc & duyệt TRƯỚC khi code** |
| [12-BO-NHO-DAI-HAN.md](12-BO-NHO-DAI-HAN.md) | Đăng nhập Supabase + bộ nhớ dài hạn theo graph, schema SQL, ràng buộc an toàn & pháp lý | Sau khi `03` đã chạy |
| [13-MENU-4-CHU-DE.md](13-MENU-4-CHU-DE.md) | **Menu 4 chủ đề** theo 4 folder tài liệu — hồ sơ chủ đề, 2 loại chip, bảng vật liệu, kế hoạch sửa từng file | **Trước khi code màn chào mới** |
| [14-KICH-BAN-4-CHU-DE.md](14-KICH-BAN-4-CHU-DE.md) | **Kịch bản 4 chủ đề để duyệt** — lời thoại + trạng thái nội bộ + kịch bản an toàn + checklist | **Đọc & duyệt cùng `13`** |

> ⚠️ File `11` chứa **4 điều chỉnh spec** (mục D) phát hiện khi viết kịch bản — cần áp vào file `03` và `05` trước khi implement.
>
> ⚠️ File `13` chứa **5 điều chỉnh spec** nữa (mục 6) phát hiện khi đối chiếu yêu cầu khách 08/09 với tài liệu nghiên cứu — cần áp vào `03`, `05`, `07`. Nặng nhất là **D2**: cách khách phát biểu mục tiêu ("để học sinh hiểu mình đang bị gì") đụng thẳng luật cấm chẩn đoán của chính docx nguồn.

---

## Tóm tắt 60 giây

Xây một **trợ lý tâm lý giáo dục** cho học sinh THPT, giúp nhận diện xu hướng **tự phê phán quá mức** (Punitive Superego) và bắc cầu tới hỗ trợ từ người thật.

Điểm khác biệt so với một chatbot bọc ChatGPT:

1. **Graph tri thức + overlay bằng chứng** — bot tích luỹ hiểu biết về người dùng qua từng lượt, có thể truy vết và **có thể sai được** (falsifiable), thay vì "cảm nhận" của LLM.
2. **Gate quyết định bằng luật**, không bằng cảm tính mô hình — LLM chỉ *diễn đạt* quyết định đã có.
3. **Lớp an toàn tất định chạy trước LLM** — phát hiện khủng hoảng không bao giờ phụ thuộc mô hình.
4. **Mọi nội dung tâm lý là văn bản đã duyệt sẵn** từ 5 tài liệu nghiên cứu (nguồn WHO/NIMH/APA) — LLM không sáng tác lời khuyên.

---

## Nguồn tham chiếu

| Nguồn | Đường dẫn |
|---|---|
| Corpus nghiên cứu (5 tài liệu .docx) | `E:\app-nckh\TÀI LIỆU NGHIÊN CỨU KHOA HỌC\` |
| Frontend tham chiếu (port UI chat) | `E:\fpt_university\Semester9\source-code\front-end` |
| Backend tham chiếu (pattern skill/gate/chip) | `E:\fpt_university\Semester9\source-code\visual-edu-backend-final` |

---

## Trạng thái

- [ ] Tuần 1 — Nội dung (graph + skill + safety)
- [ ] Tuần 2 — Backend
- [ ] Tuần 3 — Frontend
- [ ] Tuần 4 — Red-team + tập demo
