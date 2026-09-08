# 06 — BACKEND (FastAPI)

> Tuần 2. Đọc [01](01-KIEN-TRUC.md) §4 để biết cấu trúc thư mục trước.

---

## 1. Dependencies

```txt
# requirements.txt
fastapi>=0.115
uvicorn[standard]>=0.32
pydantic>=2.9
pydantic-settings>=2.6
anthropic>=0.40
redis>=5.2
networkx>=3.4
pyyaml>=6.0
python-dotenv>=1.0

# giai đoạn 2 (phân tích)
# pandas, scipy, pingouin
```

---

## 2. API endpoints

### 2.1. `POST /api/session`

Tạo phiên. Mặc định ẩn danh, không PII.

Có header `Authorization: Bearer <supabase_access_token>` hợp lệ thì phiên gắn
với tài khoản và mở bộ nhớ dài hạn (nếu người dùng đã bật). Token sai/thiếu
**không phải lỗi** — rơi về phiên ẩn danh như cũ.

```jsonc
// Request: {}                     Header (tuỳ chọn): Authorization: Bearer ...
// Response
{
  "session_id": "8f3a2c1e-...",
  "expires_in": 86400,
  "signed_in": false
}
```

---

### 2.2. `GET /api/assessment`

Trả 10 câu Likert + thang 5 mức (đọc từ `data/assessment.yaml`).

```jsonc
{
  "scale": [
    { "value": 1, "label": "Hoàn toàn không" },
    { "value": 2, "label": "Không đúng lắm" },
    { "value": 3, "label": "Khó xác định" },
    { "value": 4, "label": "Khá đúng" },
    { "value": 5, "label": "Hoàn toàn đúng" }
  ],
  "items": [
    { "id": 1, "node_id": "m-tu-trach",
      "text": "Tôi thường tự trách bản thân khi mắc lỗi." }
    // … 10 câu
  ],
  "disclaimer": "Bài đánh giá này giúp bạn nhận diện… không phải công cụ chẩn đoán tâm lý."
}
```

---

### 2.3. `POST /api/assessment`

Chấm điểm + **seed overlay**.

```jsonc
// Request
{ "session_id": "...", "answers": { "1": 4, "2": 5, "3": 3, "...": 0 } }

// Response
{
  "total": 34,
  "average": 3.4,
  "band": "DANG_CHU_Y",             // THAP | NHE | DANG_CHU_Y | CAO
  "band_label": "Mức đáng chú ý",
  "result_text": "...",             // nguyên văn từ tài liệu, theo band
  "next_actions": [
    { "label": "Nói chuyện về kết quả này", "href": "/chat?from=assessment" }
  ],
  "disclaimer": "..."
}
```

**Ánh xạ band** (nguyên văn tài liệu *NHẬN DIỆN TRONG ĐỜI SỐNG HỌC SINH.docx*):

| Điểm TB | band | Nhãn |
|---|---|---|
| 1,00 – 2,00 | `THAP` | Mức thấp |
| 2,01 – 3,00 | `NHE` | Mức nhẹ |
| 3,01 – 4,00 | `DANG_CHU_Y` | Mức đáng chú ý |
| 4,01 – 5,00 | `CAO` | Mức cao |

**Seed overlay:** mỗi câu → evidence cho `node_id` tương ứng, `source=LIKERT`, confidence theo bảng ở [03](03-OVERLAY-VA-GATE.md) §3.

> ⚠️ Màn hình kết quả **luôn có nút đi tiếp vào chat**. Không bao giờ là màn hình cuối.

---

### 2.4. `POST /api/chat/stream` — SSE

```jsonc
// Request
{ "session_id": "...", "message": "hôm nay em thi được 6.5, em thấy mình tệ thật" }
```

**Định dạng sự kiện SSE:**

```
event: meta
data: {"gate":"REFLECT","message_type":"REFLECT"}

event: token
data: {"t":"Mình "}

event: token
data: {"t":"để ý "}

event: card
data: {"type":"INSIGHT_CARD","lines":["phải được 8 phẩy","..."],"closing":"Mình hiểu đúng chứ?"}

event: footer
data: {"quickReplies":["✓ Đúng vậy","✗ Không hẳn","— Mình chưa muốn nói"],"turn_id":7}

event: done
data: {}
```

| Event | Khi nào |
|---|---|
| `meta` | Ngay sau khi gate quyết định — frontend biết render loại bubble nào |
| `token` | Từng token văn bản (gate `CLARIFY` / `REFLECT` / `BRIDGE`) |
| `card` | Nội dung có cấu trúc (`INSIGHT_CARD`, `KNOWLEDGE_CARD`, `COPING_CARD`, `BRIDGE_CARD`, `CRISIS_CARD`) |
| `footer` | Cuối stream — mang `quickReplies` (giống pattern `ws-messages.ts` của repo cũ) |
| `done` | Kết thúc |

> **Trường hợp `ESCALATE`:** chỉ có `meta` → `card` (CRISIS_CARD) → `done`. **Không có token nào**, vì không gọi LLM.

---

## 3. Interface pipeline step

```python
class PipelineContext(BaseModel):
    session_id:     str
    user_message:   str
    overlay:        Overlay
    safety:         SafetyResult   | None = None
    chip:           ChipSignal     | None = None
    extracted:      list[Evidence] = []
    gate:           GateDecision   | None = None
    response_text:  str            = ""
    card:           dict           | None = None
    quick_replies:  list[str]      = []
    flags:          list[str]      = []

class Step(Protocol):
    name: str
    async def execute(self, ctx: PipelineContext) -> None: ...
```

### Danh sách step (theo thứ tự)

| # | Step | File | Ghi chú |
|---|---|---|---|
| 1 | `SafetyGuardStep` | `steps/safety_guard.py` | Có thể **dừng pipeline** |
| 2 | `ChipDetectStep` | `steps/chip_detect.py` | Bỏ qua step 3 nếu khớp |
| 3 | `ExtractEvidenceStep` | `steps/extract_evidence.py` | LLM lượt 1 |
| 4 | `UpdateOverlayStep` | `steps/update_overlay.py` | Merge + dò cycle |
| 5 | `GateDecideStep` | `steps/gate_decide.py` | Luật cứng |
| 6 | `BuildPromptStep` | `steps/build_prompt.py` | SkillLoader |
| 7 | `SpeakStep` | `steps/speak.py` | LLM lượt 2, stream |
| 8 | `PostCheckStep` | `steps/post_check.py` | Chặn đầu ra |
| 9 | `QuickReplyStep` | `steps/quick_reply.py` | 7 luật |
| 10 | `LogTurnStep` | `steps/log_turn.py` | JSONL |

**Luật dừng sớm:** step 1 khớp tầng 1/2 → set `ctx.card = CRISIS_CARD`, nhảy thẳng tới step 10.

---

## 4. Hợp đồng LLM lượt 1 — Trích bằng chứng

```python
class ExtractedEvidence(BaseModel):
    node_id:    str
    confidence: float = Field(ge=0.0, le=0.60)   # trần cứng
    verbatim:   str   = Field(max_length=120)

class ExtractionResult(BaseModel):
    evidence: list[ExtractedEvidence] = []
```

**Gọi model:**

| Tham số | Giá trị |
|---|---|
| model | `claude-sonnet-5` |
| max_tokens | 800 |
| temperature | **0.0** (trích xuất phải ổn định) |
| system | `01_EXTRACT_EVIDENCE.md` đã điền placeholder |
| stream | ❌ không |

**Xử lý lỗi:**
- Parse JSON hỏng → thử bóc code fence → vẫn hỏng → trả `evidence: []`, log `flags: ["extract_parse_failed"]`. **Không crash.**
- `node_id` không có trong graph → **loại bỏ**, log `flags: ["extract_hallucinated_node"]`
- `verbatim` không phải substring của `user_message` → **loại bỏ**. Đây là chốt chặn chống bịa quan trọng.

---

## 5. Hợp đồng LLM lượt 2 — Diễn đạt

| Tham số | Giá trị |
|---|---|
| model | `claude-sonnet-5` |
| max_tokens | 400 (ngắn — ép bot không giảng đạo) |
| temperature | 0.7 (`CLARIFY`, `REFLECT`) / 0.3 (`BRIDGE`) |
| system | skill của gate, đã điền placeholder |
| stream | ✅ có, trừ chế độ `cycle` (cần JSON hoàn chỉnh) |

---

## 6. Graph loader

```python
class GraphService:
    def __init__(self, path: Path):
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        self.nodes  = {n["id"]: Node(**n) for n in raw["nodes"]}
        self.cycles = [Cycle(**c) for c in raw["cycles"]]
        self.g = nx.DiGraph()
        for n in raw["nodes"]:
            self.g.add_node(n["id"], **n)
        for e in raw["edges"]:
            self.g.add_edge(e["from"], e["to"], **e)
        self._validate()

    def _validate(self):
        """Chạy lúc startup — thà sập ngay còn hơn sai âm thầm."""
        # mọi cạnh trỏ tới node tồn tại
        # mọi content node có content_ref hợp lệ
        # mọi cycle có đủ node
        # mọi evidence node có >= 3 cues
```

> **Luật:** `_validate()` fail → **không cho app khởi động**. Graph sai âm thầm nguy hiểm hơn app không chạy.

---

## 7. Overlay store (Redis)

```python
KEY = "overlay:{session_id}"

async def get(session_id) -> Overlay:      # miss → Overlay rỗng
async def save(session_id, overlay):       # SET + EXPIRE 86400
```

Serialize bằng `overlay.model_dump_json()`.

---

## 8. Config

```python
class Settings(BaseSettings):
    anthropic_api_key: str
    anthropic_model: str = "claude-sonnet-5"
    redis_url: str = "redis://localhost:6379/0"
    overlay_ttl_seconds: int = 86400
    log_path: Path = Path("./data/turns.jsonl")
    cors_origins: list[str] = ["http://localhost:3000"]

    confidence_threshold: float = 0.70
    extract_confidence_cap: float = 0.60
    max_response_sentences: int = 5
    crisis_tier3_max_chars: int = 600

    model_config = SettingsConfigDict(env_file=".env")
```

---

## 9. Xử lý lỗi — không bao giờ để người dùng nhìn thấy stacktrace

| Lỗi | Xử lý |
|---|---|
| LLM timeout / 5xx | Trả câu tĩnh: *"Mình đang hơi chậm, bạn nhắn lại giúp mình nhé."* Log. |
| Redis down | Chạy với overlay rỗng trong RAM. Bot vẫn hoạt động ở mức `CLARIFY`. |
| Graph validate fail | Không khởi động (chủ ý). |
| Post-check chặn | Thay bằng câu an toàn ở [04](04-SAFETY-LAYER.md) §6.1. |
| Exception bất kỳ trong pipeline | Trả câu tĩnh + log full traceback. **Không bao giờ 500 trần cho người dùng.** |

> ⚠️ Khi lỗi, **không được** nói "hệ thống gặp sự cố" bằng giọng lạnh. Người đang tâm sự mà gặp thông báo lỗi kỹ thuật là trải nghiệm rất tệ.

---

## 10. Checklist

- [ ] `main.py` — CORS, startup load graph + skills, health check
- [ ] `POST /api/session`
- [ ] `GET /api/assessment` + `POST /api/assessment` + seed overlay
- [ ] `POST /api/chat/stream` — SSE 5 loại event
- [ ] 10 pipeline step
- [ ] `GraphService` + `_validate()` chặn startup
- [ ] Overlay store Redis + TTL
- [ ] Hợp đồng LLM lượt 1 (JSON, trần 0.60, kiểm verbatim là substring)
- [ ] Hợp đồng LLM lượt 2 (stream, max 400 token)
- [ ] Bảng xử lý lỗi §9
- [ ] Test: `ESCALATE` không phát sinh lời gọi LLM nào
