# 01 — KIẾN TRÚC HỆ THỐNG

## 1. Stack đã chốt

| Tầng | Công nghệ | Lý do |
|---|---|---|
| Frontend | **Next.js 16 (App Router) + React 19 + TypeScript + Tailwind v4 + shadcn** | Port thẳng từ repo `front-end`, tiết kiệm ~1 tuần |
| Backend | **Python 3.12 + FastAPI** (monolith modular) | Xem §2 |
| Graph | **File YAML + networkx** (load vào RAM lúc startup) | 42 node — không cần DB đồ thị |
| State phiên | **Redis** (TTL 24h) | Overlay ẩn danh, tự hết hạn |
| Log | **File JSONL** | Đủ cho demo; giai đoạn 2 mới cần Postgres |
| LLM | **Claude (claude-sonnet-5)** | Tiếng Việt tốt, structured output ổn định |
| Streaming | **SSE** (`StreamingResponse`) | Đơn giản hơn WebSocket, đủ dùng |

### Vì sao KHÔNG dùng những thứ này

| Bỏ | Lý do |
|---|---|
| Microservice | Sản phẩm có **một luồng chat**. Tách service chỉ đẻ ra Kafka + tracing + lỗi vận hành, hội đồng không cộng điểm. |
| Neo4j | 42 node. `networkx` giải quyết trong 20 dòng. |
| Vector DB / embedding | Corpus 5 tài liệu đã biên tập. Graph-first cho kiểm soát tuyệt đối nội dung — xem [02](02-DOMAIN-GRAPH.md) §6. |
| ~~Postgres (giai đoạn demo)~~ | *Sửa 07/09/2026:* đã thêm Supabase (Postgres) cho **đăng nhập tuỳ chọn + bộ nhớ dài hạn**. Phiên ẩn danh vẫn chỉ dùng Redis + JSONL. Xem [12](12-BO-NHO-DAI-HAN.md). |
| Java/Spring | Verbose, chậm iterate, không có lợi thế nào ở đây. |

---

## 2. Vì sao Python cho backend

1. **Giai đoạn 2 là nghiên cứu đánh giá người dùng.** Sẽ cần chạy thống kê trên log: SUS, pre/post, Cronbach's α cho thang Likert 10 câu, kiểm định phi tham số, Cohen's κ khi 2 chuyên gia chấm transcript. Trong Python là `pandas` + `scipy` + `pingouin` — **cùng ngôn ngữ với backend**. Node/Java buộc phải export CSV rồi nhảy sang SPSS/R → đứt mạch, dễ sai.
2. **networkx** — graph in-memory gần như miễn phí.
3. **Tiếng Việt** — `unicodedata` + `pyvi`/`underthesea` cho chuẩn hoá & bỏ dấu (thứ lớp an toàn cần).
4. **Pydantic** — hợp đồng "schema → JSON contract cho LLM", tương đương `BeanOutputConverter` bên Java nhưng gọn hơn nhiều.
5. **FastAPI SSE** khớp trực tiếp với Vercel AI SDK phía Next.js.

---

## 3. Sơ đồ hệ thống

```
┌─────────────────────────────┐        ┌──────────────────────────────────┐
│  Next.js (port 3000)        │        │  FastAPI (port 8000)             │
│                             │        │                                  │
│  /            2 lối vào     │        │  POST /api/session               │
│  /assessment  test 10 câu   │◀──SSE─▶│  POST /api/assessment            │
│  /chat        giao diện chat│        │  POST /api/chat/stream           │
│                             │        │                                  │
│  ├ message-bubble  (port)   │        │  ├ safety/    ← TẤT ĐỊNH, trước  │
│  ├ nudge-card      (port)   │        │  ├ graph/     ← YAML, 42 node    │
│  ├ chat-composer   (port)   │        │  ├ overlay/   ← evidence engine  │
│  ├ INSIGHT_CARD    (mới)    │        │  ├ gate/      ← luật, 5 gate     │
│  ├ CRISIS_CARD     (mới)    │        │  ├ skills/    ← 6 file .md       │
│  └ ASSESSMENT_CARD (mới)    │        │  └ llm/       ← Claude client    │
└─────────────────────────────┘        └────────┬──────────────┬──────────┘
                                                │              │
                                          ┌─────▼─────┐  ┌─────▼──────┐
                                          │   Redis   │  │ turns.jsonl│
                                          │ overlay   │  │  (log)     │
                                          │ TTL 24h   │  └────────────┘
                                          └───────────┘
```

---

## 4. Cấu trúc thư mục

### Backend

```
backend/
├── app/
│   ├── main.py                   # FastAPI app, CORS, startup load graph
│   ├── config.py                 # settings (pydantic-settings)
│   │
│   ├── api/
│   │   ├── session.py            # POST /api/session  → tạo phiên ẩn danh
│   │   ├── assessment.py         # POST /api/assessment → chấm điểm, seed overlay
│   │   └── chat.py               # POST /api/chat/stream → SSE
│   │
│   ├── safety/
│   │   ├── normalize.py          # bỏ dấu, hạ chữ, gom khoảng trắng
│   │   ├── crisis.py             # 3 tầng phrase list + ngưỡng
│   │   ├── chips.py              # nhận diện chip theo TIỀN TỐ
│   │   └── postcheck.py          # chặn ngôn ngữ chẩn đoán ở đầu ra
│   │
│   ├── graph/
│   │   ├── loader.py             # đọc YAML → networkx
│   │   ├── schema.py             # pydantic model cho node/edge
│   │   └── cycles.py             # dò vòng lặp đang hoạt hoá
│   │
│   ├── overlay/
│   │   ├── model.py              # Evidence, EvidenceSource, Overlay
│   │   └── store.py              # Redis get/set, TTL
│   │
│   ├── gate/
│   │   └── decide.py             # thuật toán 5 gate, ưu tiên cứng
│   │
│   ├── pipeline/
│   │   ├── base.py               # interface Step.execute(ctx)
│   │   └── steps/                # 10 bước, mỗi bước 1 file
│   │
│   ├── llm/
│   │   ├── client.py             # Claude, streaming + retry
│   │   ├── extract.py            # lượt gọi 1: TRÍCH bằng chứng → JSON
│   │   └── speak.py              # lượt gọi 2: DIỄN ĐẠT theo gate
│   │
│   ├── skills/                   # ⚠️ CHUYÊN GIA SẼ SỬA Ở ĐÂY (giai đoạn 2)
│   │   ├── 00_CORE_PERSONA.md
│   │   ├── 01_EXTRACT_EVIDENCE.md
│   │   ├── 11_CLARIFY.md
│   │   ├── 12_REFLECT.md
│   │   ├── 15_BRIDGE.md
│   │   └── 99_REFUSAL.md
│   │
│   └── telemetry/
│       └── log.py                # ghi turns.jsonl
│
└── data/
    ├── domain_graph.yaml          # 42 node + cạnh + policy edge
    ├── content/                   # đoạn văn duyệt sẵn, gắn theo node_id
    │   ├── concepts.yaml
    │   ├── coping.yaml
    │   └── resources.yaml
    ├── crisis_card.md             # 🔒 văn bản CỐ ĐỊNH
    └── assessment.yaml            # 10 câu Likert + 4 mức kết quả
```

### Frontend

```
frontend/
├── src/
│   ├── app/
│   │   ├── page.tsx                    # trang chủ, 2 lối vào
│   │   ├── assessment/page.tsx         # bài test 10 câu
│   │   └── chat/page.tsx               # giao diện chat
│   │
│   ├── features/chat/
│   │   ├── components/
│   │   │   ├── message-bubble.tsx      # ← PORT
│   │   │   ├── message-list.tsx        # ← PORT
│   │   │   ├── chat-composer.tsx       # ← PORT
│   │   │   └── bubbles/
│   │   │       ├── reflect-bubble.tsx
│   │   │       ├── insight-card.tsx    # ← MỚI (điểm nhấn demo)
│   │   │       ├── knowledge-card.tsx  # ← PORT (đổi nội dung)
│   │   │       ├── coping-card.tsx     # ← MỚI
│   │   │       ├── bridge-card.tsx     # ← MỚI
│   │   │       └── crisis-card.tsx     # ← MỚI, hardcoded
│   │   ├── use-chat-session.ts         # ← PORT (bỏ WS, dùng SSE)
│   │   └── types.ts                    # ← PORT (zod schema)
│   │
│   ├── features/assessment/
│   │   ├── likert-form.tsx
│   │   └── result-card.tsx
│   │
│   └── components/
│       └── disclaimer-banner.tsx       # ← MỚI, thường trực
```

---

## 5. Luồng một lượt chat (10 bước)

```
Tin nhắn người dùng
   │
   ├─▶ [1] SAFETY TẤT ĐỊNH
   │        normalize (bỏ dấu) → khớp 3 tầng phrase list → kiểm ngưỡng độ dài
   │        └─ Tầng 1/2 khớp? ──▶ CRISIS_CARD (văn bản cứng) ──▶ KẾT THÚC
   │                               ⚠️ KHÔNG gọi LLM
   │
   ├─▶ [2] CHIP PREFIX?
   │        Bắt đầu bằng tiền tố hệ thống → biết chắc ý định, BỎ QUA bước [3]
   │
   ├─▶ [3] TRÍCH BẰNG CHỨNG        ← LLM lượt 1 (chỉ TRÍCH, không tư vấn)
   │        input : tin nhắn + 5 lượt gần nhất
   │        output: [{node_id, confidence, verbatim}]  — JSON có schema
   │
   ├─▶ [4] CẬP NHẬT OVERLAY
   │        merge evidence → tính lại vòng lặp đang hoạt hoá (cycles.py)
   │
   ├─▶ [5] GATE (luật cứng trên trạng thái graph)
   │        → {gate, target_nodes, reason}
   │
   ├─▶ [6] DỰNG PROMPT
   │        skill .md của gate + node context + verbatim của user
   │
   ├─▶ [7] LLM DIỄN ĐẠT            ← LLM lượt 2 (chỉ NÓI, không quyết định)
   │        stream token ra SSE
   │
   ├─▶ [8] KIỂM HẬU KỲ
   │        chặn: đặt tên bệnh, khẳng định y khoa, hứa hẹn, tiết lộ node_id
   │
   ├─▶ [9] SINH QUICK REPLIES
   │        2–3 chip từ node kề + 7 luật (xem [03] §5)
   │
   └─▶ [10] GHI LOG CÓ CẤU TRÚC
            turns.jsonl → dataset giai đoạn 2
```

### Vì sao tách [3] và [7] thành hai lượt gọi LLM

> **Một lượt để *hiểu*, một lượt để *nói*.**

Gộp lại thì mô hình vừa suy diễn vừa tư vấn trong cùng một hơi thở — không audit được, không chặn được. Tách ra:

- Bước **[3]** cho ra **JSON kiểm tra được** (schema cố định, không phải văn xuôi)
- Bước **[7]** bị **ràng buộc bởi gate** đã quyết ở [5], không tự do đi đâu thì đi

Chi phí: 2 lượt gọi/turn. Chấp nhận được — đây là cái giá của khả năng kiểm soát.

---

## 6. Nguyên tắc "LLM chỉ diễn đạt, không quyết cấu trúc"

Mượn nguyên văn từ `KG_DEMO_CONTEXT.md §4` của dự án VisualEdu:

> *"Không cho LLM tự lập plan tự do (LLM bịa được plan) — plan phải dựng từ template/cạnh KG."*

Áp dụng ở đây:

| Quyết định | Ai quyết |
|---|---|
| Có phải khủng hoảng không? | 🔒 Luật cứng (bước 1) |
| Gate nào cho lượt này? | 🔒 Thuật toán trên overlay (bước 5) |
| Nói về node nào? | 🔒 Gate chỉ định `target_nodes` |
| Đưa kỹ năng nào? | 🔒 Policy edge trong graph |
| Nội dung kiến thức/kỹ năng là gì? | 🔒 Văn bản duyệt sẵn trong `data/content/` |
| **Diễn đạt thành câu tiếng Việt** | ✅ LLM |
| **Đặt câu hỏi làm rõ** | ✅ LLM (trong khuôn skill) |

---

## 7. Biến môi trường

```
# backend/.env
ANTHROPIC_API_KEY=
ANTHROPIC_MODEL=claude-sonnet-5
REDIS_URL=redis://localhost:6379/0
OVERLAY_TTL_SECONDS=86400
LOG_PATH=./data/turns.jsonl
CORS_ORIGINS=http://localhost:3000

# frontend/.env.local
NEXT_PUBLIC_API_BASE=http://localhost:8000
```

---

## 8. Chạy local

```bash
# backend
cd backend && uv venv && uv pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# redis
docker run -d -p 6379:6379 redis:7-alpine

# frontend
cd frontend && pnpm install && pnpm dev
```
