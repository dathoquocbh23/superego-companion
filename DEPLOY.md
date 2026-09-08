# DEPLOY — Frontend lên Vercel · Backend lên Render (free tier)

> Hướng dẫn triển khai bản demo của "Chatbot đồng hành — Cái siêu tôi trừng phạt".
> Đọc code đã xác nhận: backend = **FastAPI / Python** (`app.main:app`), frontend =
> **Next.js 16 App Router** (client gọi thẳng backend qua `NEXT_PUBLIC_API_BASE`).

---

## 0. Bức tranh tổng thể

```
                 trình duyệt học sinh
                        │
        ┌───────────────┴────────────────┐
        │ HTML/JS tĩnh                    │ fetch() + SSE  (CORS)
        ▼                                ▼
  Vercel (frontend)  ───────────►  Render (backend FastAPI)
  Next.js 16                        uvicorn app.main:app
                                         │
                                         ├── Google AI Studio (Gemini)  — LLM
                                         └── Supabase (Postgres + Auth) — overlay,
                                             transcript, đăng nhập, bộ nhớ dài hạn
```

Điểm cần nhớ:

- **Frontend gọi backend từ trình duyệt**, không phải server-to-server → **CORS bắt buộc
  đúng**. `CORS_ORIGINS` trên Render phải chứa đúng domain Vercel.
- **Render free tier KHÔNG có Redis.** Overlay (bằng chứng + lịch sử 1 phiên) mặc định
  sống trên Redis. Không cấu hình gì thì code *âm thầm* rơi về RAM và **quên sạch mọi
  phiên mỗi lần container ngủ/thức hoặc deploy lại**. Xử lý ở [§3.4](#34-overlay-không-có-redis-trên-render).
- **Render free tier ngủ sau ~15 phút không có request.** Lần gọi đầu sau khi ngủ mất
  ~50 giây (cold start). Xem [§6](#6-giữ-cho-backend-không-ngủ-tuỳ-chọn).
- Đĩa Render free là **tạm thời** — `data/turns.jsonl` sẽ mất khi restart. Chấp nhận
  được (số liệu nghiên cứu nên đẩy lên Supabase qua `TURNLOG_SUPABASE_ENABLED`).

---

## 1. Chuẩn bị chung

### 1.1. Đưa code lên GitHub

Cả Vercel lẫn Render đều deploy từ một repo Git. Thư mục `e:\app-nckh` hiện **chưa phải
git repo**.

```bash
cd /e/app-nckh

# .gitignore ở gốc — chặn rác và secret
cat > .gitignore <<'EOF'
# secrets
backend/.env
frontend/.env.local

# python
**/__pycache__/
**/.venv/
**/.pytest_cache/

# node / next
frontend/node_modules/
frontend/.next/
frontend/out/
*.tsbuildinfo

# logs
backend/data/*.jsonl
EOF

git init
git add .
git commit -m "Chuẩn bị deploy: frontend Vercel + backend Render"
git branch -M main
git remote add origin https://github.com/<user>/app-nckh.git
git push -u origin main
```

> `backend/.gitignore` và `frontend/.gitignore` đã chặn `.env` / `.env.local` sẵn — kiểm
> tra lại `git status` **không thấy** hai file đó trước khi push.

### 1.2. ⚠️ Xoay lại secret

File `backend/.env` và `frontend/.env.local` trên máy đang chứa **key thật**
(Supabase, có thể cả Gemini). Nếu chúng từng bị commit / chia sẻ:

- **Supabase** → Project Settings → API → *rotate* `service_role` key (và cả `anon` nếu
  nghi ngờ). `service_role` bypass RLS — lộ là đọc được bộ nhớ mọi học sinh.
- **Gemini** → https://aistudio.google.com/apikey → xoá key cũ, tạo key mới.

Từ giờ key chỉ sống trong **dashboard Vercel/Render**, không nằm trong repo.

### 1.3. Dựng schema Supabase

Nếu chưa chạy: mở Supabase → **SQL Editor** → chạy lần lượt các file trong
`backend/db/migrations/` theo thứ tự:

| File | Bắt buộc khi |
|---|---|
| `001_init.sql` | luôn (nền tảng: conversations, messages, turn_logs, hàm `touch_updated_at`) |
| `002_memory.sql` | dùng bộ nhớ dài hạn |
| `003_consent.sql` | dùng bộ nhớ dài hạn |
| `004_verbatim.sql` | lưu transcript nguyên văn |
| `005_anon_auth.sql` | dùng đăng nhập ẩn danh / bộ nhớ |
| `006_overlay_state.sql` | **`OVERLAY_BACKEND=supabase`** (khuyến nghị cho Render free — xem §3.4) |

Cho demo tối thiểu (không đăng nhập, không bộ nhớ) mà vẫn giữ được phiên qua cold start:
chạy `001` + `006`.

---

## 2. Các file thêm vào repo cho Render

Render suy luận được app Python, nhưng khai báo tường minh sẽ đỡ đau. Tạo **ở gốc repo**:

### 2.1. `render.yaml` (Blueprint — tuỳ chọn nhưng nên có)

```yaml
services:
  - type: web
    name: nckh-backend
    runtime: python
    plan: free
    rootDir: backend
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    healthCheckPath: /health
    envVars:
      - key: PYTHON_VERSION
        value: 3.12.7
      # các biến còn lại nhập ở dashboard (xem §3.3) hoặc thêm sync:false ở đây
```

### 2.2. Chốt phiên bản Python

Code dùng cú pháp `list[str]`, `str | None`, `from __future__ import annotations` → cần
**Python ≥ 3.10**, khuyến nghị **3.12**. Chọn 1 trong 2:

- Đặt env var `PYTHON_VERSION=3.12.7` trên Render, **hoặc**
- Tạo `backend/runtime.txt`:
  ```
  python-3.12.7
  ```

---

## 3. Deploy BACKEND lên Render

### 3.1. Tạo service

1. https://dashboard.render.com → **New → Web Service** → *Build and deploy from a Git
   repository* → chọn repo `app-nckh`.
2. Cấu hình:

   | Trường | Giá trị |
   |---|---|
   | **Name** | `nckh-backend` |
   | **Region** | Singapore (gần VN nhất) |
   | **Branch** | `main` |
   | **Root Directory** | `backend` |
   | **Runtime** | Python 3 |
   | **Build Command** | `pip install -r requirements.txt` |
   | **Start Command** | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
   | **Instance Type** | Free |

3. **Health Check Path**: `/health` (Advanced).

> `--port $PORT` bắt buộc: Render cấp cổng động qua biến `$PORT`. Bind cứng `8000` sẽ bị
> báo "no open ports detected" và deploy fail.

### 3.2. pydantic-settings đọc env như thế nào

`app/config.py` trỏ `env_file` vào `backend/.env`. Trên Render **không có file đó** —
không sao: pydantic-settings đọc **biến môi trường thật** trước. Mọi biến khai ở
dashboard Render đều vào thẳng `Settings`. Tên biến **không phân biệt hoa thường**
(`GEMINI_API_KEY` = `gemini_api_key`).

### 3.3. Biến môi trường cần đặt trên Render

**Nhóm tối thiểu để bot trả lời thật:**

| Biến | Giá trị | Ghi chú |
|---|---|---|
| `LLM_PROVIDER` | `gemini` | hoặc `anthropic` |
| `GEMINI_API_KEY` | *(key AI Studio)* | bỏ trống + `LLM_OFFLINE=true` → bot trả câu tĩnh, đủ để test luồng |
| `GEMINI_MODEL` | `gemini-2.5-flash` | free tier RPM thấp; client tự retry khi 429/503 |
| `LLM_OFFLINE` | `false` | |
| `CORS_ORIGINS` | `https://<app>.vercel.app` | **điền sau khi có domain Vercel** (§5). Nhiều origin: ngăn cách bằng dấu phẩy, không khoảng trắng thừa. Không hỗ trợ `*` (do `allow_credentials=True`). |

**Nhóm giữ phiên qua cold start (rất nên có — xem §3.4):**

| Biến | Giá trị |
|---|---|
| `OVERLAY_BACKEND` | `supabase` |
| `SUPABASE_URL` | `https://<ref>.supabase.co` |
| `SUPABASE_SERVICE_ROLE_KEY` | *(service_role key — CHỈ ở backend)* |
| `OVERLAY_TTL_SECONDS` | `86400` |

**Nhóm nghiên cứu / tính năng (tuỳ chọn):**

| Biến | Mặc định | Ý nghĩa |
|---|---|---|
| `TRANSCRIPT_ENABLED` | `true` | ghi hội thoại nguyên văn vào Supabase; thiếu `SUPABASE_*` → tự no-op |
| `TURNLOG_SUPABASE_ENABLED` | `true` | đẩy số liệu turn_logs (không PII) lên Supabase — bù cho `turns.jsonl` bị mất khi restart |
| `MEMORY_ENABLED` | `false` | bộ nhớ dài hạn; bật cần `SUPABASE_*` + migration 002/003/005 |

> Không dùng Supabase chút nào? Đặt `OVERLAY_BACKEND=memory` và bỏ hết `SUPABASE_*`.
> Bot vẫn chạy, nhưng **mất toàn bộ phiên đang nói dở mỗi lần container ngủ/deploy**.

### 3.4. Overlay: không có Redis trên Render

Mặc định `OVERLAY_BACKEND=redis` + `REDIS_URL=redis://localhost:6379/0`. Trên Render free
không có Redis nào ở địa chỉ đó → `OverlayStore` **âm thầm** chạy bằng RAM. Hậu quả: mỗi
cold start / deploy, mọi phiên mất `evidence`, `gate history`, `stall streak` — hội thoại
đang sống bị hỏng logic, không chỉ mất số liệu.

Ba lựa chọn, theo thứ tự khuyến nghị:

1. **`OVERLAY_BACKEND=supabase`** *(khuyến nghị)* — dùng luôn Supabase đã có, không thêm
   dịch vụ thứ ba. Phải chạy `006_overlay_state.sql` trước. Đánh đổi: mỗi lần `save()`
   overlay là một HTTP round-trip (~vài chục–trăm ms) thay vì Redis TCP — nhỏ so với
   ~1.5–2s mỗi lượt gọi LLM. Đọc cache trong RAM nên chỉ `save()` chạm mạng.
2. **Redis ngoài** — tạo free Redis ở [Upstash](https://upstash.com), đặt
   `REDIS_URL=rediss://...`, giữ `OVERLAY_BACKEND=redis`.
3. **`OVERLAY_BACKEND=memory`** — chỉ khi demo ngắn, chấp nhận reset. Không cần Supabase.

### 3.5. Deploy & kiểm tra

Bấm **Create Web Service**. Xong khi log hiện:

```
Graph vX: N evidence + M content node, ... Skills: ...
LLM: gemini:gemini-2.5-flash          (hoặc "OFFLINE (câu tĩnh)")
Uvicorn running on http://0.0.0.0:10000
```

Ghi lại URL, ví dụ `https://nckh-backend.onrender.com`. Kiểm tra:

```bash
curl https://nckh-backend.onrender.com/health
# {"status":"ok","graph_version":"...","llm_offline":false,...}
```

> Nếu deploy **fail ở startup**: `app/main.py` cố ý **không khởi động** khi
> `domain_graph.yaml` không hợp lệ hoặc thiếu placeholder trong file skill. Đọc log để
> biết dòng nào — đây là hành vi có chủ đích, không phải lỗi hạ tầng.

---

## 4. Deploy FRONTEND lên Vercel

### 4.1. Import project

1. https://vercel.com/new → import repo `app-nckh`.
2. Cấu hình:

   | Trường | Giá trị |
   |---|---|
   | **Framework Preset** | Next.js (tự nhận) |
   | **Root Directory** | `frontend` |
   | **Build Command** | *(mặc định)* `next build` |
   | **Output Directory** | *(mặc định)* `.next` |
   | **Install Command** | *(mặc định)* `npm ci` |
   | **Node.js Version** | 20 hoặc 22 |

> Next.js `16.3.0` + React `19.2` — Vercel hỗ trợ sẵn, không cần chỉnh gì thêm.

### 4.2. Biến môi trường (Environment Variables)

| Biến | Giá trị | Scope |
|---|---|---|
| `NEXT_PUBLIC_API_BASE` | `https://nckh-backend.onrender.com` | Production (+ Preview) |
| `NEXT_PUBLIC_SUPABASE_URL` | `https://<ref>.supabase.co` | *(chỉ khi dùng đăng nhập/bộ nhớ)* |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | *(anon key — KHÔNG BAO GIỜ service_role)* | *(như trên)* |

- **Không** dấu `/` ở cuối `NEXT_PUBLIC_API_BASE` (`api.ts` tự nối `/api/...`).
- Thiếu 2 biến `SUPABASE_*` → app chạy hoàn toàn ẩn danh, trang `/login` báo "chưa cấu
  hình". Đó là hành vi hợp lệ cho demo.
- `NEXT_PUBLIC_*` được **nhúng vào bundle lúc build** → đổi giá trị phải **redeploy**.

### 4.3. Deploy

**Deploy** → chờ build. Xong sẽ có domain kiểu `https://app-nckh.vercel.app`.

---

## 5. Nối hai đầu (bắt buộc, làm sau cùng)

Vòng lặp con gà — quả trứng: mỗi bên cần URL của bên kia.

1. **Có domain Vercel** → về Render, set
   `CORS_ORIGINS=https://app-nckh.vercel.app` → **Manual Deploy / Save** (Render tự
   restart). Nhiều domain (kèm domain tuỳ chỉnh):
   `CORS_ORIGINS=https://app-nckh.vercel.app,https://chatbot.truong.edu.vn`
2. **Có domain Render** → đảm bảo `NEXT_PUBLIC_API_BASE` trên Vercel trỏ đúng → nếu vừa
   sửa thì **Redeploy** frontend.
3. Preview deployment của Vercel có domain đổi liên tục (`app-nckh-git-*.vercel.app`).
   `CORS_ORIGINS` không nhận wildcard → để test preview thì thêm từng domain preview
   thủ công, hoặc chỉ test trên domain Production.

---

## 6. Giữ cho backend không ngủ (tuỳ chọn)

Render free ngủ sau ~15 phút. Trước buổi demo **30/09**:

- Cách đơn giản: [cron-job.org](https://cron-job.org) (miễn phí) ping
  `https://nckh-backend.onrender.com/health` mỗi **10 phút**.
- 1 service chạy liên tục ≈ 730 giờ/tháng, nằm trong hạn 750 giờ free.
- Vẫn nên **mở app trước giờ demo 5–10 phút** để chắc chắn đã "nóng máy".
- Backup: video demo dự phòng (đã có trong kế hoạch `docx/09`).

---

## 7. Checklist nghiệm thu sau deploy

- [ ] `GET /health` trả `status: ok`, `llm_offline` đúng như mong đợi.
- [ ] Mở domain Vercel → trang chủ hiện 2 lối vào + hotline.
- [ ] `/assessment` → làm 10 câu → màn kết quả có nút vào chat (gọi `POST /api/assessment`
      200, không lỗi CORS trong Console).
- [ ] `/chat` → gửi 1 tin → thấy **token stream dần** (SSE chạy), không phải hiện 1 cục.
- [ ] Thử câu khủng hoảng (theo `tests/test_safety_crisis.py`) → hiện **CRISIS_CARD** với
      link `tel:`, **không** có token nào stream, **không** quick reply.
- [ ] DevTools → Network → request tới `onrender.com` có header
      `access-control-allow-origin` = domain Vercel.
- [ ] (Nếu `OVERLAY_BACKEND=supabase`) chat vài lượt → vào Supabase xem bảng
      `overlay_state` có dòng; Manual Deploy lại backend → chat tiếp trong cùng phiên vẫn
      nhớ ngữ cảnh.
- [ ] (Nếu bật transcript) bảng `messages` / `conversations` có dữ liệu.

---

## 8. Sự cố thường gặp

| Triệu chứng | Nguyên nhân & cách xử lý |
|---|---|
| Console: `blocked by CORS policy` | `CORS_ORIGINS` trên Render không khớp **chính xác** domain Vercel (thừa `/` cuối, nhầm `http`/`https`, hay chưa restart sau khi sửa). Sửa → Manual Deploy. |
| Request đầu tiên treo ~50s rồi mới chạy | Cold start Render free. Bình thường. Xem §6. |
| `502 Bad Gateway` / "no open ports detected" | Start Command thiếu `--host 0.0.0.0 --port $PORT`. |
| Deploy fail ngay lúc khởi động, log nhắc `domain_graph` hoặc `skill` | Có chủ đích: graph/skill không hợp lệ thì app từ chối chạy. Sửa file dữ liệu. |
| Chat trả nguyên 1 cục thay vì stream dần | Hiếm trên Render (app đã gửi `X-Accel-Buffering: no`). Kiểm tra không có proxy/CDN nào chen giữa; đừng bọc `/api/chat/stream` sau Vercel rewrite. |
| Bot luôn trả câu chung chung, `/health` báo `llm_offline: true` | Thiếu `GEMINI_API_KEY` hoặc `LLM_OFFLINE=true`. |
| Bot hay lỗi "Mình đang hơi chậm, bạn nhắn lại giúp" | Gemini free tier 429 RESOURCE_EXHAUSTED. Giãn nhịp test, hoặc nâng quota, hoặc đổi `GEMINI_MODEL`. |
| Sau mỗi lần Render restart, hội thoại "quên" hết | `OVERLAY_BACKEND` vẫn là `redis`/`memory`. Chuyển sang `supabase` + chạy migration 006 (§3.4). |
| Vercel build fail ở `next build` | Chạy `npm run build` ở `frontend/` trên máy để tái hiện. Kiểm tra Node version ≥ 20 trong Project Settings. |
| `/login` báo chưa cấu hình | Thiếu `NEXT_PUBLIC_SUPABASE_URL` / `NEXT_PUBLIC_SUPABASE_ANON_KEY`. Hợp lệ nếu demo ẩn danh. |
| Đổi `NEXT_PUBLIC_API_BASE` nhưng frontend vẫn gọi URL cũ | Biến `NEXT_PUBLIC_*` nhúng lúc build — phải **Redeploy** Vercel. |

---

## 9. Tóm tắt giới hạn free tier

| | Render free (backend) | Vercel Hobby (frontend) |
|---|---|---|
| Ngủ khi rảnh | Có, sau ~15 phút (cold start ~50s) | Không (static/serverless) |
| Giờ chạy | 750 giờ instance/tháng | — |
| Đĩa | Tạm thời — mất khi restart | — (build artifact) |
| Bandwidth | Đủ cho demo | 100 GB/tháng |
| Ràng buộc dùng | — | Chỉ **phi thương mại** với gói Hobby |

Với buổi demo 30/09: cấu hình đề xuất là **`LLM_PROVIDER=gemini` + `OVERLAY_BACKEND=supabase`
+ cron ping /health**, và luôn có video dự phòng.
