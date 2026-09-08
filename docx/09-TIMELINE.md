# 09 — KẾ HOẠCH 24 NGÀY

> Hôm nay: **CN 06/09/2026** · Deadline: **T4 30/09/2026**
> Bám file này hằng ngày. Tick checkbox khi xong.

---

## Tổng quan

| Tuần | Ngày | Trọng tâm | Sản phẩm cuối tuần |
|---|---|---|---|
| **T1** | T2 07/09 → CN 13/09 | **Nội dung** — không code | Graph + skill + phrase list hoàn chỉnh |
| **T2** | T2 14/09 → CN 20/09 | **Backend** | API chạy được, curl ra câu trả lời |
| **T3** | T2 21/09 → CN 27/09 | **Frontend** | Sản phẩm bấm được đầu-cuối |
| **T4** | T2 28/09 → T4 30/09 | **Red-team + tập demo** | Sẵn sàng bảo vệ |

> ⚠️ Tuần 4 chỉ có **3 ngày**. Nghĩa là **mọi thứ phải xong hết ngày 27/09**. Đừng lên kế hoạch làm tính năng ở tuần 4.

---

## TUẦN 1 — NỘI DUNG (07/09 → 13/09)

> **Đây là đường găng.** Không có chuyên gia, nên nội dung *chính là* lớp an toàn.
> Tuần này **không viết code sản phẩm**. Ai ngứa tay muốn code, cứ dựng scaffold rỗng.

### T2 07/09 — Trích node

- [ ] Đọc lại cả 5 tài liệu `.docx` một lượt, đánh dấu đoạn sẽ dùng
- [ ] Tạo `data/domain_graph.yaml`
- [ ] Nhập **10 node Manifestation** (copy từ 10 câu Likert)
- [ ] Nhập **4 Trigger**, **5 Affect**, **5 Impact**

### T3 08/09 — Cues + cạnh

- [ ] Viết `cues` cho **cả 24 evidence node** (3–6 cụm tiếng Việt mỗi node)
  - Nghĩ như học sinh gõ, không như sách giáo khoa: *"mình dở quá"*, *"tại mình hết"*
- [ ] Khai báo cạnh `triggers` / `produces` / `impairs` / `reinforces`
- [ ] Khai báo `cycle-tu-phe-phan` (7 node, `min_nodes_to_activate: 4`)

### T4 09/09 — Content node

- [ ] `data/content/concepts.yaml` — 4 mục, **trích nguyên văn**
- [ ] `data/content/coping.yaml` — 6 mục, **trích nguyên văn**
- [ ] `data/content/resources.yaml` — 5 mục (hotline + danh bạ TP.HCM)
- [ ] Khai báo **11 policy edge** + `priority` + `condition`

### T5 10/09 — Lớp an toàn ⚠️ ưu tiên cao nhất

- [ ] Viết `EXACT_ACCENTED` (4 cụm — xử lý bẫy "tự tử"/"từ từ")
- [ ] Viết `NORMALIZED` tầng 1 (~20 cụm)
- [ ] Viết tầng 2 (~12 cụm)
- [ ] Viết tầng 3 (~10 cụm)
- [ ] `data/crisis_card.md` — trích nguyên văn tài liệu
- [ ] Viết 4 nhóm chặn post-check

### T6 11/09 — Skill files (1)

- [ ] `00_CORE_PERSONA.md`
- [ ] `01_EXTRACT_EVIDENCE.md`
- [ ] `11_CLARIFY.md`

### T7 12/09 — Skill files (2)

- [ ] `12_REFLECT.md` (gồm chế độ `cycle`)
- [ ] `15_BRIDGE.md`
- [ ] `99_REFUSAL.md`
- [ ] `data/assessment.yaml` — 10 câu + 4 band + nguyên văn diễn giải

### CN 13/09 — Rà soát 🚧 CỔNG KIỂM SOÁT

- [ ] Đọc to **toàn bộ** content node — có câu nào nghe như chẩn đoán không?
- [ ] Đọc lại 6 skill — có chỗ nào cho phép bot khẳng định về người dùng không?
- [ ] Thử tay 10 câu học sinh thật hay nói → tự hỏi bot *nên* trả lời gì
- [ ] **Quyết định:** nếu chưa xong → cắt gate `BRIDGE`, còn 4 gate

> **Điều kiện qua cổng:** graph validate được, 6 skill xong, phrase list 3 tầng xong.
> Chưa đạt → cắt scope, **không lùi lịch**.

---

## TUẦN 2 — BACKEND (14/09 → 20/09)

### T2 14/09 — Nền

- [ ] Scaffold FastAPI, `config.py`, CORS, health check
- [ ] `graph/loader.py` + `_validate()` chặn startup
- [ ] `skills/loader` — load 1 lần, báo lỗi khi thiếu placeholder

### T3 15/09 — An toàn + overlay

- [ ] `safety/normalize.py`, `safety/crisis.py` (3 tầng)
- [ ] `safety/chips.py` (4 tiền tố)
- [ ] `overlay/model.py`, `overlay/store.py` (Redis + TTL)
- [ ] **Test ngay:** 20 câu khủng hoảng → đúng tier chưa?

### T4 16/09 — LLM lượt 1

- [ ] `llm/client.py` — Claude, retry
- [ ] `llm/extract.py` — JSON schema, trần 0.60
- [ ] Kiểm `verbatim` là substring của input (chốt chặn chống bịa)
- [ ] Loại `node_id` không có trong graph

### T5 17/09 — Gate

- [ ] `graph/cycles.py` — dò cycle hoạt hoá
- [ ] `gate/decide.py` — 5 gate + ưu tiên cứng
- [ ] `resolve_policy_edge` — 11 cạnh + điều kiện κ
- [ ] `highest_information_gain_node`
- [ ] **Test:** không vào `SUPPORT` khi chưa qua `REFLECT`

### T6 18/09 — LLM lượt 2 + SSE

- [ ] `llm/speak.py` — stream
- [ ] `POST /api/chat/stream` — 5 loại event
- [ ] `postcheck.py`
- [ ] `quick_reply.py` — 7 luật

### T7 19/09 — API còn lại

- [ ] `POST /api/session`
- [ ] `GET` + `POST /api/assessment` + seed overlay
- [ ] `telemetry/log.py`
- [ ] Bảng xử lý lỗi ([06](06-BACKEND.md) §9)

### CN 20/09 — Rà soát 🚧 CỔNG KIỂM SOÁT

- [ ] Chạy `curl` một hội thoại 8 lượt đầu-cuối
- [ ] Kiểm log: gate có chuyển hợp lý không?
- [ ] **Test:** `ESCALATE` có phát sinh lời gọi LLM nào không? (phải là **không**)

> **Điều kiện qua cổng:** backend trả lời được qua curl, log ghi đủ trường.

---

## TUẦN 3 — FRONTEND (21/09 → 27/09)

### T2 21/09 — Scaffold + port

- [ ] Next.js + Tailwind v4 + shadcn
- [ ] Port `message-list`, `message-bubble`, `chat-composer`, `nudge-card`
- [ ] `DisclaimerBanner`

### T3 22/09 — Chat chạy

- [ ] `use-chat-session` → SSE
- [ ] Zod schema + discriminated union
- [ ] `ReflectBubble` + quick replies chạy được

### T4 23/09 — Card

- [ ] `CrisisCard` (🔴 `tel:` link, không đóng được)
- [ ] `InsightCard` (⭐ điểm nhấn demo)
- [ ] `CopingCard`, `BridgeCard`, `KnowledgeCard`

### T5 24/09 — Assessment

- [ ] Trang `/assessment` — 10 câu Likert
- [ ] Màn hình kết quả + **nút vào chat**
- [ ] Nối kết quả → seed overlay → chat

### T6 25/09 — Trang chủ + hoàn thiện

- [ ] Trang `/` — 2 lối vào + hotline hiện sẵn
- [ ] Microcopy theo bảng ([07](07-FRONTEND.md) §7)
- [ ] Test trên điện thoại thật

### T7 26/09 — Đi hết luồng

- [ ] Chạy đủ 4 kịch bản demo ([10](10-DEMO-VA-RUI-RO.md))
- [ ] Sửa lỗi phát hiện được
- [ ] ⚠️ **Từ đây KHÔNG thêm tính năng mới**

### CN 27/09 — Đóng băng 🚧 CỔNG KIỂM SOÁT

- [ ] **Feature freeze.** Chỉ sửa lỗi từ đây.
- [ ] Chạy lại cả 4 kịch bản, quay màn hình

> **Điều kiện qua cổng:** sản phẩm bấm được đầu-cuối, 4 kịch bản chạy trơn.

---

## TUẦN 4 — RED-TEAM & DEMO (28/09 → 30/09)

### T2 28/09 — Red-team an toàn

- [ ] Chạy đủ **40 prompt** đối kháng ([04](04-SAFETY-LAYER.md) §9)
- [ ] Ghi kết quả vào bảng → đưa vào báo cáo
- [ ] Sửa phrase list nếu có ca bỏ sót
- [ ] Chạy lại toàn bộ sau khi sửa

### T3 29/09 — Tài liệu + tập demo

- [ ] Slide / poster
- [ ] **Quay video 4 kịch bản** (dự phòng nếu demo trực tiếp trục trặc)
- [ ] Tập nói 2 lượt
- [ ] Chuẩn bị trả lời câu hỏi khó ([10](10-DEMO-VA-RUI-RO.md) §3)

### T4 30/09 — 🎯 DEMO

- [ ] Kiểm tra môi trường trước 2 tiếng (Redis chạy? API key còn hạn? mạng?)
- [ ] Mở sẵn video dự phòng ở tab bên cạnh

---

## Đường găng & danh sách cắt

### Đường găng
```
Graph + Skill (T1)  →  Gate (T2)  →  Card (T3)  →  Red-team (T4)
```
Chậm ở tuần 1 là chậm toàn bộ. **Bảo vệ tuần 1 bằng mọi giá.**

### Cắt theo thứ tự này khi trễ

| Ưu tiên cắt | Hạng mục | Mất gì |
|---|---|---|
| 1 | Gate `BRIDGE` → gộp vào `SUPPORT` | Mất một kịch bản demo |
| 2 | `KnowledgeCard` → gộp vào `CopingCard` | Ít card hơn |
| 3 | Policy edge: 8 → 4 | Cá nhân hoá thô hơn |
| 4 | Evidence node: 24 → 14 (bỏ Trigger + 5 Affect) | Cycle yếu đi |
| 5 | Trang `/assessment` → chỉ còn chat | **Mất cơ chế mồi overlay** — cắt cuối cùng |

### 🔒 KHÔNG CẮT — dù có chuyện gì

1. Lớp phát hiện khủng hoảng tất định + `CRISIS_CARD` hardcoded
2. Banner disclaimer thường trực
3. Luật `INFERRED` không được phát ngôn
4. Post-check chặn ngôn ngữ chẩn đoán
5. Hai lượt gọi LLM tách biệt (hiểu / nói)

---

## Ghi chú làm việc

- **Commit mỗi ngày**, message tiếng Việt, ghi rõ đang ở mục nào của kế hoạch
- **Không refactor** trong tuần 3–4
- Gặp bug lạ tuần 4 → **dùng video dự phòng**, đừng sửa nóng trước giờ demo
- Có thời gian thừa? Viết thêm test đối kháng, đừng thêm tính năng
