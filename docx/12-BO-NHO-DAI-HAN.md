# 12 — ĐĂNG NHẬP & BỘ NHỚ DÀI HẠN THEO GRAPH

> Thêm ngày 07/09/2026. Sửa quyết định #2 ở [00](00-TONG-QUAN.md) và §8 ở [03](03-OVERLAY-VA-GATE.md).
>
> **Mặc định vẫn là ẩn danh.** Không đăng nhập → hệ thống chạy y hệt trước khi có file này.
> Đăng nhập → mở thêm bộ nhớ xuyên phiên, và bộ nhớ đó vẫn phải **tự bật** mới hoạt động.

---

## 1. Vì sao không đẻ ra cấu trúc nhớ mới

Câu hỏi ban đầu là "làm long-term memory theo tree hay graph?". Câu trả lời:
**đã có graph rồi** — `data/domain_graph.yaml`, 24 evidence node + các cạnh
`triggers / produces / impairs / reinforces`. Thứ khác nhau giữa hai học sinh
không phải cấu trúc graph, mà là **trọng số trên graph đó**.

| Tầng | Nội dung | Nơi sống | Phạm vi |
|---|---|---|---|
| Ontology | node + cạnh + policy edge | `domain_graph.yaml` | chung cho mọi người |
| Overlay | trọng số node trong **một phiên** | Redis, TTL 24h | một phiên |
| **Bộ nhớ dài hạn** | trọng số node + cạnh của **một người** | Supabase | nhiều phiên |

Bộ nhớ dài hạn chính là `Overlay`, kéo dài phạm vi từ *một phiên* sang *một
người*. Dựng một cây khái niệm riêng song song với graph sẵn có chỉ tạo ra hai
nguồn sự thật phải đồng bộ.

---

## 2. Cái lưu và cái KHÔNG lưu

> **Sửa 07/09/2026 (`004_verbatim.sql`).** Bản đầu KHÔNG lưu nguyên văn — chỉ
> trọng số node. Chạy thử thì lộ ra giới hạn: người dùng hỏi *"bạn nhớ mình
> được bao nhiêu điểm không?"* và bot không trả lời được. Trí nhớ mà không nhớ
> nổi sự việc thì không phải trí nhớ. Đã đổi sang **có lưu nguyên văn**, kèm
> hàng rào.

**Lưu:**

- trọng số node: `confidence`, `observations`, `first_seen`, `last_seen`
- trọng số cạnh: cặp node nào hay cùng sáng ở người này
- ✅ **nguyên văn** — MỘT câu cho mỗi node, tối đa 200 ký tự

**KHÔNG lưu:**

- ❌ lịch sử hội thoại (chỉ vài câu lẻ, không phải transcript)
- ❌ `session_id` gốc — chỉ `session_hash` 6 ký tự trong nhật ký
- ❌ nguyên văn của nguồn `INFERRED` — câu LLM tự suy ra KHÔNG BAO GIỜ được
  lưu như thể học sinh đã nói vậy

### 2.1. Bốn hàng rào, tất cả nằm ở DB

Đặt ở SQL chứ không chỉ ở Python: tầng nào gọi vào cũng bị chặn như nhau.

| # | Hàng rào | Ở đâu |
|---|---|---|
| 1 | chỉ nguồn `SELF_REPORT` / `LIKERT` / `CONFIRMED` mới giữ câu chữ | `ghi_nho_luot()` |
| 2 | tối đa 200 ký tự | `CHECK user_memory_verbatim_ngan` |
| 3 | xoá riêng câu chữ, giữ chủ đề | `xoa_nguyen_van()` |
| 4 | hiện đúng từng câu trên `/memory` | trang `/memory` |

Hàng rào 3 tách khỏi `quen_toi_di()` có chủ ý. *"Đừng nhắc lại lời tôi nói
nữa"* và *"quên sạch tôi đi"* là hai mong muốn khác nhau; gộp một nút thì
người ta phải chọn tất-hoặc-không, và thường sẽ không chọn gì.

### 2.2. Quan hệ với luật trong `app/telemetry/log.py`

Luật đó **không đổi**: file log nghiên cứu (`turns.jsonl`, bảng `turn_logs`)
vẫn tuyệt đối không có `user_message`, `verbatim`, `response_text`. Hai thứ
khác nhau:

| | log nghiên cứu | bộ nhớ dài hạn |
|---|---|---|
| thuộc về | tập dữ liệu, ẩn danh | **cá nhân người dùng** |
| có nguyên văn | không, không bao giờ | có, người đó xem và xoá được |
| người dùng kiểm soát | không | có — bật/tắt/xoá |

Nguyên văn nằm ở nơi **chủ nhân của nó nhìn thấy và xoá được**, không nằm
trong tập dữ liệu ẩn danh. Đó mới là chỗ ranh giới thật sự.

**Đổi consent version.** Ai đã đồng ý ở `v1` là đồng ý cho một cách xử lý dữ
liệu KHÁC (không lưu chữ). Đồng ý đó không bao trùm `v2` → `use-auth.ts` so
`consent_version` với `CONSENT_VERSION` và coi như **chưa bật** cho tới khi
hỏi lại. Yêu cầu pháp lý, không phải lựa chọn UX.

---

## 3. Phân rã theo thời gian

`app/memory/decay.py` — bán rã mặc định **30 ngày**:

```
confidence_hiện_tại = confidence_lưu × 0.5 ^ (số_ngày / 30)
```

Một học sinh lo lắng hồi tháng 3 không có nghĩa tháng 9 vẫn vậy. Bộ nhớ không
quên sẽ đóng đinh người ta vào phiên bản cũ của chính họ — đúng thứ mà cả sản
phẩm đang cố gỡ ra. Node phân rã xuống dưới `0.15` thì thôi nạp.

---

## 4. Lưu trữ — PostgREST, không phải driver Postgres

DDL chạy một lần bằng `backend/db/migrations/*.sql` (dán vào Supabase SQL
Editor). CRUD lúc chạy đi qua PostgREST bằng `httpx` — đã có sẵn vì client LLM
dùng. Thêm `psycopg` chỉ để insert vài dòng là gánh thêm một phụ thuộc nhị
phân cho mỗi máy cài dự án.

Ghi một lượt gọi đúng **một** RPC — `ghi_nho_luot()` — gộp 3 việc vào một giao
dịch: trọng số node, trọng số cạnh, nhật ký. Ba lời gọi REST riêng mà lỗi nửa
chừng thì bộ nhớ lệch: có cạnh mà không có node.

### Bảng

| Bảng | Vai trò |
|---|---|
| `app_users` | hồ sơ + cờ `memory_enabled` (**mặc định false**) |
| `user_memory` | trọng số **node**: `confidence`, `observations`, `last_seen` |
| `user_memory_edges` | trọng số **cạnh**: số lần 2 node cùng sáng ở người này |
| `user_memory_events` | nhật ký append-only — để trả lời "vì sao bot nhớ điều này?" |

`user_memory_edges` là phần "graph" thật sự. Ontology nói *"về lý thuyết
`a-lo-lang` dẫn tới `i-kho-tap-trung`"*; bảng này nói *"với bạn A, hai cái đó
đi cùng nhau 7 lần"*. Cái sau mới là hiểu người, cái trước là thuộc bài.

---

## 5. 🔒 Hai luật an toàn không được phá

### Luật 1 — bộ nhớ để BIẾT NÊN HỎI GÌ, không bao giờ để KHẲNG ĐỊNH

Evidence nạp vào mang `source=REMEMBERED`:

- `can_be_spoken` → **False**. Không lọt vào `speakable_verbatims()`, nên không
  vào được `INSIGHT_CARD` hay câu REFLECT.
- Trần confidence **0.50** < `confidence_threshold` **0.70** ⇒ node nhớ lại
  **không bao giờ tự đủ mạnh** để kích `REFLECT`. Luôn phải có bằng chứng mới
  trong phiên này.
- Node `risk_adjacent` (`a-vo-vong`) **không bao giờ được nạp**. Mở phiên mà đã
  nghiêng sẵn về vô vọng là mớm đúng thứ nguy hiểm nhất.

Nó chỉ vào `frontier` của `highest_information_gain_node()` — bot hỏi trúng chỗ
hơn, chứ không mở lời bằng *"lần trước bạn bảo bạn kém cỏi"*.

`can_be_spoken = False` chặn được verbatim, nhưng KHÔNG chặn được việc LLM tự
nói *"mình nhớ bạn từng…"*. Đó là lỗ hổng thật, đã vá 07/09/2026 bằng luật 7
trong `00_CORE_PERSONA.md` + post-check §6.6 ([04](04-SAFETY-LAYER.md)).

### 5.1. Sau khi có nguyên văn: NHỚ SỰ VIỆC ≠ NHẮC LỜI TỰ PHÁN XÉT

Bot giờ nhớ được câu chữ, nên Luật 1 cần một đường cắt sắc hơn. Cắt theo
**loại node**, không theo confidence — `memory_quotes()` trong
`app/memory/service.py`:

| Loại node | Ví dụ | Nhắc lại? |
|---|---|---|
| `trigger` | "thi được 6.5", "ba mẹ mắng" | ✅ sự việc đã xảy ra, nhắc lại là hữu ích |
| `impact` | "mất ngủ", "học không vô" | ✅ hoàn cảnh, nhắc lại được |
| `manifestation` | "mình dở quá", "tại mình hết" | ❌ **lời tự phán xét** |
| `affect` | "mình kém cỏi", "mình vô dụng" | ❌ **lời tự phán xét** |
| `risk_adjacent` | "chẳng còn hy vọng" | ❌ tuyệt đối không |

Vì sao: một đứa trẻ tháng trước thấy mình vô dụng không có nghĩa hôm nay vẫn
vậy. Câu đầu tiên nó nghe khi mở app **không nên là lời chính nó nói lúc tệ
nhất**. Nhớ "bạn kể thi được 6.5" giúp người ta thấy được nhớ tới; đọc lại
"bạn bảo bạn kém cỏi" thì đóng đinh người ta vào phiên bản cũ — đúng thứ cả
sản phẩm đang cố gỡ ra.

Đổi phạm vi bằng `MEMORY_RECALL_NODE_TYPES` (mặc định `trigger,impact`). Mở
rộng sang `manifestation` / `affect` là mở lại đúng rủi ro mớm ở trên.

Câu được phép nhắc đi vào prompt qua `{MEMORY_QUOTES}` trong
`00_CORE_PERSONA.md`. Mục đó ghi `(không có)` thì LLM được lệnh nói thật là
không nhớ, tuyệt đối không đoán. Post-check §6.6 chặn khoe trí nhớ **chỉ khi**
lượt đó thực sự không có câu nào — có câu thì nhắc lại là đúng chức năng.

> Đây là chỗ dễ hỏng nhất của tính năng này. Cạm bẫy mớm (iatrogenic
> suggestion) đã được cảnh báo ở `app/pipeline/quick_reply.py`; bộ nhớ dài hạn
> khuếch đại nó lên nhiều lần vì bot "biết" cả những thứ hôm nay chưa ai nói.

### Luật 2 — bằng chứng HÔM NAY luôn thắng bằng chứng CŨ

`REMEMBERED` xếp hạng **-1** trong `_SOURCE_RANK`, dưới cả `INFERRED`. Học sinh
nói khác đi so với tháng trước thì lời hôm nay đè lên. Không có chuyện bot cãi
nhau với bộ nhớ của chính nó.

Bộ nhớ cũng **không tự ghi lại chính nó**: `record_turn()` lọc bỏ `REMEMBERED`,
nếu không mỗi phiên bộ nhớ lại tự bơm mình lên, càng ngày càng chắc chắn về
một điều chưa từng được xác nhận lại.

---

## 6. Đăng nhập

`app/memory/auth.py` — không tự verify chữ ký JWT. Project Supabase mới ký
bằng khoá bất đối xứng và xoay khoá định kỳ; tự verify là phải nuôi cache JWKS
+ xử lý xoay khoá, nhiều chỗ sai hơn là lợi. Hỏi thẳng Supabase
`GET /auth/v1/user` **một lần lúc mở phiên** (không phải mỗi lượt chat).

Token sai/thiếu → `user_id = None` → phiên ẩn danh. Không phải lỗi.

---

## 7. ⚖️ Nghĩa vụ theo Nghị định 13/2023/NĐ-CP

[03](03-OVERLAY-VA-GATE.md) §8 đã dẫn nghị định này để biện minh cho việc
KHÔNG lưu gì. Bật bộ nhớ dài hạn là đi ngược lại, nên phải làm đủ:

| Nghĩa vụ | Đã có trong code | Còn phải làm |
|---|---|---|
| Dữ liệu sức khoẻ tâm thần = **dữ liệu nhạy cảm** | `memory_enabled` mặc định `false` | Văn bản thông báo xử lý dữ liệu |
| Chủ thể **dưới 16 tuổi** cần đồng ý của cha mẹ | `003_consent.sql` + popup `MemoryConsentDialog` | Nếu triển khai thật: cách xác thực người giám hộ mạnh hơn một ô tick |
| Quyền xoá | `quen_toi_di()` (RPC) + nút "Quên tôi đi" ở sidebar | — |
| Quyền xem dữ liệu về mình | trang `/memory` — đọc thẳng qua RLS | — |
| Hạn chế truy cập | RLS theo `auth.uid()`, service_role chỉ ở backend | Rà lại trước khi deploy |

### 7.1. Luồng đồng ý

Bật bộ nhớ phải qua popup (`features/auth/memory-consent-dialog.tsx`): nói rõ
**nhớ gì / không nhớ gì / mờ dần bao lâu / xoá thế nào**, hỏi tuổi, dưới 16 thì
bắt xác nhận có đồng ý của cha mẹ.

Ràng buộc thật KHÔNG nằm ở popup mà ở DB — popup bỏ qua được bằng cách gọi
thẳng PostgREST:

```sql
-- 003_consent.sql
check (
  memory_enabled = false
  or (consent_at is not null and duoi_16 is not null
      and (duoi_16 = false or guardian_consent = true))
)
```

Bật cờ + ghi đồng ý đi chung một giao dịch qua RPC `bat_bo_nho()`. Tách ra hai
lệnh thì có khoảnh khắc cờ đã bật mà chưa có bằng chứng đã xin phép — đúng thứ
sau này không ai chứng minh được.

`tat_bo_nho()` ≠ `quen_toi_di()`: **tắt** là ngừng ghi tiếp và giữ dữ liệu cũ,
**xoá** là mất hẳn. Gộp hai thứ vào một nút thì người ta không dám bấm cái nào.

> ⚠️ Ô tick "cha mẹ đã đồng ý" là mức tối thiểu cho demo học thuật. Triển khai
> thật với học sinh thì cần cơ chế mạnh hơn (nhà trường xác nhận, hoặc email
> tới phụ huynh). Đây là điều kiện pháp lý, không phải việc kỹ thuật.

---

## 8. Trang "bot nhớ gì về mình" (`/memory`)

Đọc **thẳng** `user_memory` / `user_memory_edges` từ Supabase bằng anon key —
RLS (`user_id = auth.uid()`) là thứ bảo đảm chỉ thấy hàng của mình. Đi vòng qua
backend bằng service_role thì phải tự viết lại đúng phép kiểm đó bằng tay, thêm
một chỗ để sai.

Backend chỉ cấp nhãn tiếng Việt của node: `GET /api/graph/labels`. Không cần
đăng nhập (ontology chung, không phải dữ liệu của ai) và **không trả `cues`** —
cues lộ ra là mớm.

> Có một căng thẳng cần biết: docx/03 cấm bot **gọi tên node** khi trò chuyện
> (mớm + dán nhãn). Trang này thì hiện nhãn — nhưng đó là quyền xem dữ liệu về
> chính mình, ngữ cảnh khác hẳn. Vì vậy nhãn được gom theo nhóm bằng lời
> thường ("Cách bạn hay nhìn về mình", "Cảm xúc đi kèm"), không phải thuật ngữ
> nội bộ.

---

## 9. Cấu hình

```env
SUPABASE_URL=https://<ref>.supabase.co
SUPABASE_SERVICE_ROLE_KEY=<service_role>   # CHỈ backend, không NEXT_PUBLIC_
MEMORY_ENABLED=true                        # false => app chạy y như cũ
MEMORY_HALF_LIFE_DAYS=30
MEMORY_MAX_SEED_NODES=8
MEMORY_SEED_CONFIDENCE_CAP=0.50
# Loại node được phép nhắc lại NGUYÊN VĂN (§5.1). Thêm manifestation/affect
# là mở lại rủi ro mớm — đọc §5.1 trước khi đổi.
MEMORY_RECALL_NODE_TYPES=trigger,impact
```

`settings.memory_ready` = `memory_enabled` **và** có URL **và** có service key.
Thiếu bất kỳ cái nào → toàn bộ tính năng im lặng tắt, không lỗi.

Bộ nhớ hỏng (Supabase sập, token hết hạn) **không được làm hỏng lượt chat** —
nuốt lỗi giống telemetry và Redis. Mất trí nhớ còn hơn mất phiên tư vấn.

---

## 10. Checklist

- [x] `001_init.sql` + `002_memory.sql` + `003_consent.sql` viết xong
- [x] Chạy `001` + `002` trên Supabase SQL Editor
- [x] Chạy `003_consent.sql` — `python scripts/check_db.py` báo đủ (07/09/2026)
- [ ] **Chạy `004_verbatim.sql`** (bộ nhớ nhớ được câu chữ — xem §2)
- [x] `EvidenceSource.REMEMBERED` + hạng -1 + `can_be_spoken = False`
- [x] `app/memory/` — `decay`, `store`, `service`, `auth`
- [x] Nạp bộ nhớ đầu phiên + ghi cuối lượt trong `runner.py`
- [x] `POST /api/session` nhận `Authorization`
- [x] Test tính chất an toàn (`tests/test_memory.py`, 13 test)
- [x] Frontend: đăng nhập, bật/tắt bộ nhớ, "quên tôi đi", trang `/memory`
- [x] Popup đồng ý + ràng buộc CHECK ở DB (§7.1)
- [ ] ⚠️ Xác thực người giám hộ mạnh hơn ô tick — nếu demo với học sinh thật
