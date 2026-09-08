# Backend — Chatbot đồng hành "Cái siêu tôi trừng phạt"

Triển khai **Tuần 1 (nội dung)** + **Tuần 2 (backend)** theo bộ kế hoạch trong `../docx/`.

## Chạy nhanh

```bash
cd backend
python -m venv .venv
./.venv/Scripts/python.exe -m pip install -r requirements.txt   # Windows
# source .venv/bin/activate && pip install -r requirements.txt  # *nix

cp .env.example .env         # điền GEMINI_API_KEY (hoặc để LLM_OFFLINE=true)
docker run -d -p 6379:6379 redis:7-alpine   # tuỳ chọn — thiếu Redis vẫn chạy (RAM)

./.venv/Scripts/python.exe -m uvicorn app.main:app --reload --port 8000
#   …hoặc trên PowerShell:  .\run-dev.ps1
```

## LLM

Mặc định **Gemini (Google AI Studio)** — `LLM_PROVIDER=gemini`, `GEMINI_MODEL=gemini-flash-latest`.
Lấy key ở https://aistudio.google.com/apikey. Đổi sang Claude: `LLM_PROVIDER=anthropic` + `ANTHROPIC_API_KEY`.

- Lượt "trích bằng chứng" gọi Gemini ở chế độ `response_mime_type=application/json`.
- Client tự retry với backoff luỹ thừa khi gặp `429 RESOURCE_EXHAUSTED` / `503` (free tier RPM thấp).
- `LLM_OFFLINE=true` hoặc thiếu API key → bot chạy **chế độ offline**: lượt "diễn đạt" trả câu
  tĩnh, lượt "trích bằng chứng" khớp `cues` theo luật. Đủ để demo toàn bộ luồng mà không tốn token.
- Thiếu Redis → overlay sống trong RAM, tự mất khi restart (chấp nhận được ở demo).

> ⚠️ `.env` chứa API key — đã nằm trong `.gitignore`, KHÔNG commit.

## Test

```bash
./.venv/Scripts/python.exe -m pytest -q
```

81 test: lớp an toàn đối kháng (docx/04 §9), gate + ưu tiên cứng, chốt chặn
`verbatim`-là-substring, `ESCALATE` không phát sinh lời gọi LLM, chấm điểm assessment…

## API (docx/06 §2)

| Method | Path | Việc |
|---|---|---|
| POST | `/api/session` | Tạo phiên ẩn danh (uuid4, Redis TTL 24h) |
| GET | `/api/assessment` | 10 câu Likert + thang 5 mức |
| POST | `/api/assessment` | Chấm điểm 4 band + **seed overlay** `source=LIKERT` |
| POST | `/api/chat/stream` | SSE: `meta` → (`token*` \| `card`) → `footer` → `done` |
| GET | `/health` | Trạng thái graph / LLM |

`ESCALATE`: chỉ `meta` → `card` (CRISIS_CARD) → `done`. **Không token nào** (không gọi LLM).

## Cấu trúc

```
data/
  domain_graph.yaml       24 evidence + 18 content node · 8 policy edge · cycle-tu-phe-phan
  content/                đoạn văn duyệt sẵn, trích nguyên văn 5 tài liệu
  crisis_card.md          🔒 văn bản CỐ ĐỊNH — không đi qua LLM
  assessment.yaml         10 câu + 4 band (nguyên văn diễn giải)
app/
  safety/    normalize · crisis (3 tầng + EXACT_ACCENTED) · chips · postcheck · refusal
  graph/     loader (+ _validate chặn startup) · schema · cycles
  overlay/   model (Evidence/Overlay, merge 3 ca) · store (Redis + RAM fallback)
  gate/      decide — 5 gate, ưu tiên ESCALATE > BRIDGE > SUPPORT > REFLECT > CLARIFY
  skills/    6 file .md + loader (báo lỗi khi thiếu placeholder)
  llm/       client (stream + offline) · extract (lượt 1, JSON) · speak (lượt 2)
  pipeline/  runner — 10 giai đoạn · quick_reply (7 luật, fallback tất định) · riskflags
  llm/       … · quickreply.py — sinh 2 chip CLARIFY theo ngữ cảnh + lọc an toàn (skill 13)
  telemetry/ log.py → data/turns.jsonl (metadata, KHÔNG nội dung người dùng)
  api/       session · assessment · chat
scripts/analyze_log.py    kiểm tra nhanh log (docx/08 §5)
```

## 4 điều chỉnh spec đã áp (docx/11 phần D)

- **D1** — ưu tiên gate: `ESCALATE > BRIDGE > SUPPORT > REFLECT > CLARIFY` (CLARIFY là mặc định).
- **D2** — lượt trích trả thêm `mapping`: `literal` → `SELF_REPORT` (trần 0.75), `inferential` → `INFERRED` (trần 0.60).
- **D3** — `MIN_NODES_FOR_REFLECT = 3` cho REFLECT chế độ đơn; chế độ `cycle` giữ ngưỡng ≥ 4 node ≥ 0.60.
- **D4** — `INSIGHT_CARD` khử trùng lặp theo `verbatim`; còn < 3 dòng → không dựng thẻ, quay về REFLECT văn xuôi.

## Nguyên tắc bất di bất dịch (đã kiểm bằng test)

1. LLM không quyết định an toàn — `check_crisis` chạy trước, tất định.
2. `INFERRED` không bao giờ lọt vào output (`Evidence.can_be_spoken`, `speakable_verbatims`).
3. Không vào `SUPPORT` khi chưa qua `REFLECT` được xác nhận.
4. Mọi lượt ghi log có cấu trúc — không chứa `user_message` / `verbatim` / `response_text`.
5. Mọi output đi qua `post_check` (chặn chẩn đoán / hứa hẹn / rò rỉ nội bộ / cắt > 5 câu).

## Chưa làm ở pass này

- Tuần 3 (frontend Next.js) — chưa.
- Bộ đối kháng 40 prompt của Tuần 4 mới có ~35 ca trong `tests/test_safety_crisis.py`; mở rộng khi red-team.
- `_offline_extract` là baseline luật cho demo không API key — không thay cho LLM lượt 1 thật.
