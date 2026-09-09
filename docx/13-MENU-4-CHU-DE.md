# 13 — MENU 4 CHỦ ĐỀ (topic profile)

> Ngày lập: **08/09/2026**. Đọc sau [03-OVERLAY-VA-GATE.md](03-OVERLAY-VA-GATE.md) và
> [07-FRONTEND.md](07-FRONTEND.md).
>
> Nguồn yêu cầu: tin nhắn khách 08/09/2026 + app tham chiếu
> **"Góc Hiểu Mình"** (https://mindly-sigma-eight.vercel.app/).
>
> ⚠️ File này chứa **5 điều chỉnh spec** (mục 6) phát hiện khi đối chiếu yêu cầu
> khách với tài liệu nghiên cứu và code hiện có. Áp vào `03`, `05`, `07` trước khi
> implement.
>
> 📄 **Lời thoại mẫu nằm ở [14-KICH-BAN-4-CHU-DE.md](14-KICH-BAN-4-CHU-DE.md)** —
> đọc song song. File đó phát hiện thêm **4 chỗ spec chưa khớp** (⚠️ A-1, A-2, B-1,
> B-2, C-1), trong đó **B-1 và B-2 phải chốt trước khi code chủ đề 2**.

---

## 1. Quyết định đã chốt

| Việc | Chốt |
|---|---|
| Màn chào | **Menu 4 chủ đề** thay cho 3 thẻ gợi ý cảm xúc hiện tại |
| 4 chủ đề lấy từ đâu | **4 folder** trong `TÀI LIỆU NGHIÊN CỨU KHOA HỌC\`, map 1:1 |
| Ô nhập tự do | **GIỮ**, đặt ngay dưới 4 thẻ — xem mục 3 |
| Bài Likert 10 câu | **Gộp vào chủ đề 2**, không còn đứng riêng ở `/` |
| Kiến trúc | **1 pipeline + tham số `topic`**, KHÔNG tách 4 agent — xem mục 2 |
| RAG | **Không dùng.** Cả 5 docx ≈ 25.5k token / context 1M. RAG chỉ thêm rủi ro cắt chunk sai, mất bảo đảm nguyên văn |
| Tên hiển thị | Đổi tạm "Đồng hành" → **"Góc Hiểu Mình"** (đã làm, xem mục 5.7) |

### Vì sao 1 pipeline chứ không 4 agent

4 agent rời thì phải nhân 4 tầng an toàn: `check_crisis`, `post_check`, `refusal`,
overlay, memory, 4 bộ skill giữ đồng bộ. Lợi ích so với "1 pipeline + 1 tham số"
bằng 0.

Rủi ro cụ thể: học sinh chọn chủ đề kiến thức rồi giữa chừng nhắn câu có ý tự hại.
Agent kiến thức mà thiếu tầng ESCALATE là hỏng. Với 1 pipeline thì **không thể
quên**, vì `check_crisis` chạy trước gate ở mọi lượt.

---

## 2. Luồng mục tiêu

Khách mô tả nguyên văn: *"trước hết là giải thích chay về lý thuyết xong đưa vô
tình huống cụ thể"* + *"phân biệt lành mạnh và trừng phạt là kiểu câu hỏi phụ lựa
chọn sau đó"* + *"giáo viên sẽ dựa vô đó phân tích để học sinh hiểu mình đang bị
gì"*.

Tức là dáng **bài giảng**: trình bày → minh hoạ → hỏi kiểm tra. Ánh xạ sang máy:

```
[1] lý thuyết + ví dụ            ->  KNOWLEDGE_CARD nguyên văn      ✓ ĐÃ CÓ
        |                             (topics.yaml: `opening`)
        v
[2] "nếu như em bị như vậy thì…" ->  HỌC SINH GÕ / chip bắc cầu     ← CẦN Ô NHẬP
        |
        v
[3] giáo viên dựa vô đó phân tích ->  REFLECT / INSIGHT_CARD        ✓ ĐÃ CÓ
                                      (overlay + gate + cycle)
```

**Bước [2] chính là lý do ô nhập tự do không thể bỏ.** Không phải sở thích thiết
kế — luồng của khách đứt ở giữa nếu thiếu nó. App tham chiếu "Góc Hiểu Mình" bỏ ô
nhập, tức là đã cắt mất đúng bước [2]; **đừng copy chỗ đó**.

Bước [3] đã dựng xong từ tuần 2. `steer` của `vong-lap-tu-phe-phan` ghi đúng việc
mà khách gọi là "phân tích":

> *"Việc của bot là cho họ thấy TRÌNH TỰ, bằng chính lời họ đã nói ra."*

---

## 3. Bảng vật liệu — nội dung 4 chủ đề LỆCH NẶNG

Đã đếm ngày 08/09/2026. Con số này quyết định thứ tự làm.

| # | Chủ đề | Folder / docx | Node bằng chứng | **Content node bot NÓI được** |
|---|---|---|---|---|
| 1 | Hiểu về cái siêu tôi | `SƠ LƯỢC VỀ _SIÊU TÔI TRỪNG PHẠT_` → `HIỂU VỀ CÁI SIÊU TÔI TRỪNG PHẠT.docx` | 3 trigger | **7** — phủ hết mục 2·3·4·5·6·7 của docx |
| 2 | Nhận diện trong đời sống học sinh | `NHẬN DIỆN…` → cùng tên | 12 (gồm đúng 10 câu Likert) | **2** — `c-bieu-hien-thuong-gap`, `c-thang-do-likert`; cộng bài Likert + 2 thẻ mượn từ docx siêu tôi |
| 3 | Ảnh hưởng đến sức khoẻ tinh thần | `ẢNH HƯỞNG…` → `RỐI LOẠN LO ÂU & TRẦM CẢM.docx` | 8 | **4** — `c-suc-khoe-va-sieu-toi` (opening) · `c-lo-au-la-gi` · `c-tram-cam-la-gi` · `c-vong-lap-tram-cam`; chip 4 mượn `c-khong-phai-chan-doan` (✅ trích 09/09) |
| 4 | Khi nào nên tìm hỗ trợ | `KHI NÀO NÊN TÌM HỖ TRỢ` → `KHI NÀO CẦN TÌM HỖ TRỢ.docx` + `CÁC CÁCH KHẮC PHỤC TẠI NHÀ.docx` | 8 | **17** — 3 concept + 5 resource + 9 coping *(đợt 4: +3 coping)* |

> **Lưu ý kỹ thuật:** 24 node bằng chứng có field `source_doc` nên lọc theo chủ đề
> được ngay. **30 content node thì KHÔNG có `source_doc`** — nguồn nằm trong
> `content/*.yaml` ở field `source`. Vì vậy `topics.yaml` phải liệt kê content node
> theo id **một cách tường minh**, không suy ra tự động được.

### Chủ đề 3 — đã trích nội dung 09/09/2026

Trước 09/09 bấm vào chủ đề 3 thì bot **không có một chữ nguyên văn nào để phát**;
`topics.yaml` để `enabled: false` — thà giấu một ô còn hơn bày ra để bấm vào rồi
bot bịa.

Ngày 09/09/2026 đã trích **4 concept node** từ `RỐI LOẠN LO ÂU & TRẦM CẢM.docx`
(xem [mục 7](#7-việc-cần-người-không-phải-code)), chủ đề 3 **đã bật**. Điểm cần
người duyệt nắm khi đối chiếu với docx gốc:

- Docx viết dạng **literature review cho bài nghiên cứu**, không phải copy cho học
  sinh. Chỉ 4 đoạn nói được với học sinh được trích. **ĐÃ BỎ:** các danh sách
  triệu chứng (xem [mục 12](#12-xoay-chip-tìm-hiểu--và-vì-sao-không-random) — không
  bày nút cho học sinh bấm đọc triệu chứng rồi tự soi), số liệu tử vong – tự sát
  (chính người soạn docx đã tự lược), bản dịch tiếng Anh, các câu xưng "nghiên cứu
  của bạn".
- **Hai chỗ cắt câu giữa dòng** ở thẻ `c-suc-khoe-va-sieu-toi`, ghi trong comment
  đầu block `concepts.yaml`: bỏ "Trong đoạn bạn gửi," và "Vì vậy, với nghiên cứu
  của bạn,". Không đổi nghĩa, nhưng người duyệt cần biết đó là cắt chủ ý.
- Thẻ mở đầu là **cơ chế + câu phân biệt "WHO không nói siêu tôi trừng phạt gây
  ra trầm cảm"**, đúng tinh thần [mục 6/D2](#d2--để-học-sinh-hiểu-mình-đang-bị-gì-đụng-luật-cấm-chẩn-đoán--quan-trọng-nhất):
  mô tả để học sinh tự đối chiếu, không dán nhãn.
- Chip 4 "Vậy mình có đang bị gì không?" dùng lại `c-khong-phai-chan-doan` như chủ
  đề 1 và 2 — câu này phải được trả lời bằng tài liệu, nói rằng không ai "bị" gì cả.

---

## 4. Hai loại chip — phân biệt cho rõ trước khi code

App tham chiếu dùng chip kiểu **FAQ** ("Cái siêu tôi là gì?"), khác hẳn cơ chế chip
hiện có trong `pipeline/quick_reply.py`.

| | Chip TÌM HIỂU (mới) | Chip KỂ CHUYỆN (đã có) |
|---|---|---|
| Giọng | Người dùng hỏi bot về khái niệm | Người dùng kể về mình |
| Ví dụ | "Có phải cái siêu tôi luôn xấu không?" | "Ít nhất phải 8" |
| Khớp `cues`? | **Không** — 0 bằng chứng | **Có** — nuôi overlay |
| Bot làm gì | Phát node nguyên văn tương ứng | Phản chiếu + hỏi sâu |
| Vai bot | Người biết → giáo viên | Người nghe → bạn đồng hành |

**Phải có cả hai.** Nếu 4 chủ đề × 4 chip đều là FAQ thì sản phẩm thành Wikipedia
có nút bấm. Công thức đề xuất mỗi chủ đề:

```
2–3 chip TÌM HIỂU  +  1 chip BẮC CẦU sang chuyện cá nhân  +  1 chip thoát
```

Chip thoát là **bắt buộc** theo luật đã có ở `quick_reply.py` (docstring đầu file).

---

## 5. Thay đổi cần làm — theo file

### 5.1. `backend/data/topics.yaml` — ✅ ĐÃ TẠO 08/09

4 hồ sơ chủ đề: `id`, `title`, `subtitle`, `folder`, `source_docs[]`, `opening`,
`learn_chips[] {text, serves}`, `bridge_chip`, `enabled`.

Đã kiểm chéo: **cả 9 node id được trỏ tới đều tồn tại** trong `domain_graph.yaml`.
Giữ nguyên luật này khi sửa file — chip không có node là một lời hứa không giữ được.

### 5.2. `backend/app/graph/loader.py`

Thêm vào `GraphService`:

- `load_topics()` — đọc `data/topics.yaml`, cache bằng `lru_cache` như
  `_assessment()` trong `api/assessment.py`.
- `topic(topic_id) -> Topic | None`.
- `topics_enabled() -> list[Topic]` — chỉ trả cái `enabled` khác `false`.
- `uu_tien_theo_topic(node_ids, topic_id) -> list[str]` — sắp xếp lại danh sách
  node theo `source_docs` của chủ đề. **Sắp xếp, KHÔNG lọc bỏ** — xem mục 6/D5.

Validate lúc nạp: mọi `opening` và `serves` phải trỏ tới node có thật, sai thì raise
ngay lúc khởi động chứ đừng để lòi ra giữa demo.

### 5.3. `backend/app/overlay/model.py`

Thêm 2 field vào `class Overlay`:

```python
topic_id: str | None = None      # chủ đề đang chọn, None = vào bằng ô nhập
luot_tim_hieu: int = 0           # số lượt ở chế độ TÌM HIỂU (xem 6/D3)
```

### 5.4. `backend/app/api/session.py` + `chat.py`

- `SessionRequest` mới (hiện `create_session` không nhận body): `{ topic: str | None }`.
- Gán `overlay.topic_id` trước khi `save()`.
- `ChatRequest` thêm `topic: str | None = None` để đổi chủ đề giữa phiên mà không
  phải mở phiên mới.
- Endpoint mới `GET /api/topics` → trả danh sách chủ đề `enabled` cho frontend
  dựng thẻ. Không cần đăng nhập, giống `GET /api/graph/labels`.

### 5.5. `backend/app/gate/decide.py`

Hai nhánh mới, và **đặt đúng chỗ mới chạy đúng**:

- **Chip TÌM HIỂU → mục §0 (khối CHIP), cùng chỗ với `CONFIRM_NO` / `CONFIRM_PARTIAL`
  / `DECLINE`.** Không phải cuối hàm. Lý do: §0 là khối "ý định đã biết chắc", chạy
  **trước** cả §1 an toàn. Nếu để chip LEARN xuống dưới, học sinh đã kể đủ 3 node rồi
  bấm hỏi một câu kiến thức thì §4 REFLECT thắng và **câu hỏi của họ bị nuốt mất**.
  → `GateDecision(gate=SUPPORT, concept_node=<serves>, reason="topic_learn")`.
  ⚠️ Nhưng §0 hiện nằm TRƯỚC §1 an toàn — chip LEARN phải để `safety.forces_escalate`
  đi trước nó, nếu không một tin nhắn khủng hoảng gõ ngay sau khi bấm chip có thể bị
  che. An toàn luôn thắng.
- **Mở chủ đề → nhánh riêng đặt sau §4 REFLECT, trước §4b ORIENT.** Lượt 1 overlay
  rỗng nên không nhánh nào khác nổ, nó fire ngay. Đặt sau REFLECT có chủ đích: nếu
  hội thoại đã đủ chín để phản chiếu thì **chuyện của học sinh thắng bài giảng**.
  → `GateDecision(gate=SUPPORT, concept_node=<opening>, reason="topic_opening")`.

`runner.py:320` đã tự đặt `message_type = "KNOWLEDGE_CARD"` khi có `concept_node` mà
không có `coping_node` — không phải sửa runner cho concept. **Nhưng phải sửa cho
`resource` node**: chủ đề 4 có chip trỏ tới `s-gvcn` / `s-ba-me`, cần ra `BRIDGE_CARD`
và **không** được set `bridge_offered`. Xem [14 ⚠️ C-1](14-KICH-BAN-4-CHU-DE.md).
- `_bi_giam_chan()` phải **trừ** `luot_tim_hieu` ra khỏi `turn_count` và
  `stall_streak` — xem mục 6/D3.
- Khi có `topic_id`, `highest_information_gain_node()` dùng
  `uu_tien_theo_topic()` làm **khoá phụ** khi điểm bằng nhau (chèn trước
  `_TYPE_RANK_*`), không phải khoá chính.

Ưu tiên gate giữ nguyên: `ESCALATE > BRIDGE > SUPPORT > REFLECT > ORIENT > CLARIFY`.
Nhánh topic nằm trong SUPPORT nên **ESCALATE vẫn luôn thắng**.

### 5.6. `backend/app/pipeline/quick_reply.py`

- Thêm hằng `CHIP_LEARN` vào `safety/phrases.py`. **Không tái dùng `CHIP_ASK` (`"? "`)** —
  prefix đó hiện mang nghĩa "chip nội dung người dùng chọn", trộn vào thì
  `detect_chip()` không phân biệt được TÌM HIỂU với trả lời thường.
- Nhánh mới cho `reason == "topic_opening" | "topic_learn"`: đọc `learn_chips` của
  chủ đề, gắn prefix `CHIP_LEARN`, cộng `bridge_chip` (**không** prefix — nó phải đi
  qua bước trích như tin nhắn thường) + 1 chip thoát.
- Menu ORIENT ở [`quick_reply.py:161`](../backend/app/pipeline/quick_reply.py) hiện
  hardcode 4 **tình huống** (điểm số / tình cảm / bạn bè / gia đình). Giữ nguyên —
  đó là van xả khi hội thoại chết máy, khác mục đích với menu 4 **chủ đề**. Đừng gộp.

### 5.7. Frontend

| File | Sửa gì |
|---|---|
| `features/chat/chat-welcome.tsx` | Thay 3 `SUGGESTIONS` cảm xúc bằng 4 thẻ chủ đề nạp từ `GET /api/topics`. **Giữ nguyên** `<ChatComposer variant="hero">` và dòng hotline ở cuối |
| `lib/api.ts` | `createSession(topic?)`, `fetchTopics()` |
| `features/chat/use-chat-session.ts` | Gửi kèm `topic` trong body `chat/stream` |
| `app/page.tsx` | Bỏ thẻ "Thử bài tự đánh giá" — bài test dời vào chủ đề 2 |
| `features/assessment/*` | Cho phép nhúng inline trong luồng chat, không chỉ ở route `/assessment` |

Câu chữ 4 thẻ **lấy nguyên của app tham chiếu**, đã ghi sẵn trong `topics.yaml`.
Câu intro: *"Hãy chọn một chủ đề để bắt đầu tìm hiểu về cái siêu tôi và đời sống
tinh thần."*

**Đã làm 08/09:**
- Gỡ dòng `Nguồn: <tên file>.docx` khỏi `bubbles/coping-card.tsx` (giữ ở payload +
  transcript — xem 6/D4).
- Đổi tên hiển thị → **"Góc Hiểu Mình"**: `app/page.tsx`, `app/login/page.tsx` (2 chỗ),
  `features/chat/session-sidebar.tsx`, `features/chat/chat-header.tsx`,
  `app/layout.tsx` (metadata), `components/brand-ping.tsx` (comment).
  **Không đụng** cụm "trợ lý đồng hành cảm xúc" trong `skills/00_CORE_PERSONA.md` và
  `99_REFUSAL.md` — đó là mô tả VAI, và `tests/test_turn.py:194` assert đúng chuỗi đó.

---

## 6. NĂM ĐIỀU CHỈNH SPEC — áp trước khi implement

### D1 — `steer` của `id-ego-superego` mâu thuẫn với chính chủ đề 1

`content/concepts.yaml` ghi: *"Đừng gọi tên Id/Ego/Superego ra trước mặt người
dùng."* Nhưng chủ đề 1 tên là "Hiểu về cái siêu tôi" và thẻ nguyên văn nêu đủ ba tên.

**Sửa:** viết lại câu đó thành phân biệt rõ hai việc —
- **Thẻ nguyên văn ĐƯỢC PHÉP** nêu khái niệm (nó là tài liệu, có nguồn).
- **Văn nói của bot VẪN CẤM** dán nhãn lên người dùng.

Nêu khái niệm ≠ gán nhãn cho người. Không sửa thì mô hình đọc thành lệnh cấm rồi né
cả thẻ.

### D2 — "để học sinh hiểu mình đang bị gì" đụng luật cấm chẩn đoán ⚠️ QUAN TRỌNG NHẤT

Khách phát biểu mục đích bằng câu này. Nhưng **chính docx của khách** cấm cách nói
đó — `HIỂU VỀ CÁI SIÊU TÔI TRỪNG PHẠT.docx — mục 7`, đã trích nguyên văn vào node
`c-khong-phai-chan-doan`:

> *"Cái siêu tôi trừng phạt" là một khái niệm lý thuyết trong phân tâm học, **không
> nên trình bày như một chẩn đoán / bệnh độc lập**. […] không phải để gắn nhãn hay
> đánh giá một người.*

Và `00_CORE_PERSONA.md` luật 1: *"KHÔNG nói người dùng bị / mắc / có bất kỳ rối loạn
nào. Đây là lỗi nghiêm trọng nhất."*

**Sửa câu chữ, KHÔNG sửa mục tiêu:**

| Khách muốn | ❌ Không được nói | ✅ Nói thế này |
|---|---|---|
| học sinh hiểu mình đang bị gì | "Bạn đang có cái siêu tôi trừng phạt" | "Điều bạn vừa kể trùng với biểu hiện mà tài liệu mô tả — bạn thấy có giống không?" |

Mục đích khách nói ra là **"nâng cao mức độ nhận biết"**. Nhận biết không cần dán
nhãn, chỉ cần mô tả rồi để học sinh tự đối chiếu. Cùng đích, khác chỗ **ai là người
kết luận**.

Corpus đã có sẵn câu trả lời cho đúng câu hỏi đó → `topics.yaml` chủ đề 1 có chip
**"Vậy mình có đang bị gì không?"** → phát nguyên văn `c-khong-phai-chan-doan`.
**Đừng gỡ chip này.**

### D3 — chip TÌM HIỂU làm gate tưởng hội thoại chết máy

Chip FAQ không mang cue → matcher rỗng → overlay rỗng. Mà `_bi_giam_chan()`:

```python
if not overlay.so_node_noi_duoc():
    return overlay.turn_count >= ORIENT_MIN_TURN   # = 2
```

→ tới lượt 2 gate bắn **ORIENT**, bot nói *"Mình thấy mình đang hỏi hơi lòng vòng mà
chưa giúp được gì thật"* giữa lúc học sinh đang bấm đọc kiến thức bình thường.

**Sửa:** đếm `overlay.luot_tim_hieu` riêng và trừ ra khỏi `turn_count` /
`stall_streak` khi xét giậm chân. Đây là bug sẽ lòi ra ở **lượt 2 của demo** nếu bỏ
qua.

### D4 — dòng "Nguồn: `<tên file>.docx`" gỡ khỏi màn hình

Học sinh 16–18 đọc tên file không thấy đó là bảo chứng — thấy một tờ photo. Đã gỡ
khỏi `coping-card.tsx`; `card.source` vẫn được backend gửi và
`persistence/transcript.py` vẫn ghi, nên bằng chứng truy nguồn để bảo vệ đề tài
**không mất**, chỉ chuyển từ màn hình sang bản ghi.

`bridge-card.tsx` giữ nguyên dòng nguồn — thẻ đó là hotline / phòng tham vấn, ghi
nguồn ở đó làm tăng độ tin.

### D5 — hai thứ app tham chiếu THIẾU, tuyệt đối không copy

Kiểm ngày 08/09 trên https://mindly-sigma-eight.vercel.app/ :

1. **Không có hotline / số điện thoại nào trên toàn trang.** Bản của mình phải giữ
   `0832000202` + `check_crisis` chạy trước gate mọi lượt + `CRISIS_CARD`.
2. **Không có ô nhập tự do** — chỉ bấm được nút. Xem mục 2: bỏ ô nhập là cắt đứt
   bước [2] của chính khách.

**Disclaimer — đã sửa 08/09, lấy một nửa của app tham chiếu.** Câu *"Công cụ tìm
hiểu kiến thức — không thay thế tư vấn tâm lý"* định vị sản phẩm **là** cái gì, hợp
với hướng menu 4 chủ đề; bản cũ là ba lời phủ định liên tiếp nên học sinh đọc xong
mất tin luôn cả phần thẻ nguyên văn. Đã dùng nó làm **câu thu gọn** của
`DisclaimerBanner`, còn câu đầy đủ (5 giây đầu) giữ thêm *"chưa qua thẩm định chuyên
môn độc lập"* — chưa thuê chuyên gia là sự thật hội đồng sẽ hỏi, bỏ đi là im lặng
đúng chỗ yếu nhất.

Nhân đó sửa một claim sai trong bản cũ: *"nội dung tổng hợp từ WHO/NIMH/APA"* →
*"nội dung trích nguyên văn từ tài liệu nghiên cứu"*. Corpus **có** trích (WHO ×8,
NIMH ×10, APA ×2) nhưng gần như toàn bộ nằm trong `RỐI LOẠN LO ÂU & TRẦM CẢM.docx`.

> **Cập nhật 09/09/2026:** chủ đề 3 nay đã có 4 content node trích từ đúng docx đó
> (WHO "Tổng quan" + "Khái quát", NIMH "Lo âu là gì?"). Câu disclaimer thu gọn
> *"trích nguyên văn từ tài liệu nghiên cứu"* vẫn giữ nguyên — nó đúng cho cả 4 chủ
> đề. Không quay lại câu "tổng hợp từ WHO/NIMH/APA": bot phát **một số đoạn** WHO/NIMH
> đã được người của nhóm chọn, không phải "tổng hợp" toàn bộ ba nguồn.

Ngoài ra `source_docs` là **ưu tiên, không phải bộ lọc cứng**: học sinh gõ chuyện
ngoài chủ đề thì overlay và gate vẫn làm việc bình thường. Chủ đề là cửa vào, không
phải nhà tù.

---

## 7. Chủ đề 3 — đã trích nội dung (09/09/2026)

> Nhóm xác nhận **đã soạn nội dung chủ đề 3 vào `RỐI LOẠN LO ÂU & TRẦM CẢM.docx`**
> và yêu cầu trích thẳng từ docx đó. Trước đây mục này ghi "việc cần NGƯỜI" — nay
> nội dung đã có người viết, việc còn lại là **chép nguyên văn**, không diễn giải.

Đã làm theo công thức [mục 11](#11-thêm-một-mục-lý-thuyết-mới--công-thức-4-bước):

| Node | Nguồn trong docx | Vai |
|---|---|---|
| `c-suc-khoe-va-sieu-toi` | "Tác động… đến vấn đề trầm cảm" mục 1 + đoạn phân biệt với WHO | `opening` — cơ chế + "không phải nhân–quả" |
| `c-lo-au-la-gi` | NIMH "Lo âu là gì?" + WHO "Khái quát" | chip |
| `c-tram-cam-la-gi` | WHO "Tổng quan" | chip |
| `c-vong-lap-tram-cam` | "Tác động… đến vấn đề trầm cảm" mục 2 + mục 3 | chip |
| `c-tram-cam-yeu-to-phong-ngua` | WHO "Các yếu tố góp phần và phòng ngừa" | chip *(đợt 2)* |
| `c-tram-cam-tu-cham-soc` | WHO "Tự chăm sóc" | chip *(đợt 2)* |
| `c-tram-cam-dieu-tri` | WHO "Chẩn đoán và điều trị" (lược tên thuốc) | chip *(đợt 2)* |
| `c-cac-dang-lo-au` | NIMH "Các dạng rối loạn lo âu" (bản 4 dạng) | chip *(đợt 3 — xem cảnh báo dưới)* |
| `c-khong-phai-chan-doan` | (đã có sẵn, mượn chéo) | chip |
| `c-dau-hieu-lo-au` | WHO "Triệu chứng và biểu hiện" (rối loạn lo âu) | **KHÔNG chip** — tới qua `explained_by` từ `i-ne-tranh` |
| `c-dau-hieu-tram-cam` | WHO "Các triệu chứng và biểu hiện" (lược phân loại) | **KHÔNG chip** — tới qua `explained_by` từ `i-mat-dong-luc` · `i-thu-minh` |

Content node: **26 → 44** (chủ đề 3: +4 +5 +1 +5 · chủ đề 4: +3). `topics.yaml`
chủ đề 3 đã bật. `pytest` 279 xanh.

**Đợt 5 (09/09) — QUÉT TRỌN `RỐI LOẠN LO ÂU & TRẦM CẢM.docx` (yêu cầu khách).**
Sau 5–6 vòng "sao lại thiếu / sao lại cắt", chốt lại nguyên tắc (đã lưu memory
`nckh-trich-nguyen-van-khong-tu-cat`): **chép nguyên văn, đủ mục, giữ đúng tiêu
đề** — chỉ cắt quảng cáo / tên cơ sở y tế / "cho nghiên cứu của bạn" / bản dịch
tiếng Anh / tên thuốc. Rủi ro "tự soi" xử bằng CÁCH HIỂN THỊ (thẻ không-chip),
không bằng cắt nội dung.

Khôi phục các chỗ đã cắt: `c-lo-au-la-gi` (+triệu chứng đi kèm) · `c-tram-cam-la-gi`
(+"Những thông tin chính" + dịch tễ + rào cản) · `c-cac-dang-lo-au` (bảng **7 dòng**
WHO, không phải 4) · `c-tram-cam-yeu-to-phong-ngua` (+sức khỏe thể chất, +can thiệp
cha mẹ) · `c-tram-cam-dieu-tri` (+tác dụng phụ, +lưỡng cực) · `c-dau-hieu-tram-cam`
(+phân loại nhẹ/vừa/nặng, đơn cực/tái diễn/lưỡng cực). Đồng bộ `k-nhan-dien-tu-phe-phan`
+ `k-tu-tran-an` về nguyên văn.

5 node mới: `c-lo-au-tong-quan` (điểm chính + tỷ lệ + rào cản + NIMH "tại sao nghiên
cứu") · `c-lo-au-yeu-to-phong-ngua` (yếu tố + phòng ngừa + NIMH yếu tố môi trường /
chuyển tiếp) · `c-lo-au-dieu-tri` (CBT) · `c-tram-cam-nguyen-nhan` (di truyền / não
bộ / hormone / lối sống — 1 thẻ dài) · `c-sieu-toi-phan-tam` (APA "superego sadism",
Blatt "introjective depression"). Chủ đề 3 chip **8 → 13**.

**Vẫn để ngoài (đúng nguyên tắc):** bản dịch tiếng Anh, dòng "Nguồn: <tên báo>",
tên thuốc (SSRI/SNRI/MAOI/TCA/fluoxetine…), số liệu tự sát, và các đoạn "Liên hệ
với đề tài / nghiên cứu của bạn" / "Trích dẫn học thuật cho Literature Review" /
"Câu có thể dùng trong bài nghiên cứu".

**Đợt 4 (09/09) — chủ đề 4, yêu cầu khách:** thêm chip cho 2 mục lớn của
`CÁC CÁCH KHẮC PHỤC TẠI NHÀ.docx`:
- `k-ngung-tu-huy-hoai` ← phần "Cách giúp con người ngừng tự hủy hoại bản thân".
  **Sửa sau feedback customer:** (1) giữ nguyên từ **"tự hủy hoại bản thân"** —
  bản đầu mình làm nhẹ thành "tự cản trở bản thân", customer không đồng ý (docx
  định nghĩa rõ Self-sabotage ngay dưới tiêu đề nên không cần tránh); (2) thẻ giờ
  liệt kê **đủ 6 chiến lược** nguyên văn, không phải 3. Chiến lược 4·5·6 vẫn còn
  node riêng (`k-growth-mindset` · `k-chia-nho-muc-tieu` · `k-chanh-niem`) để gate
  phát một-lần-một-cái; thẻ tổng quan này là đường "xem trọn cách tiếp cận".
- `k-nguyen-nhan-goc-re` ← chiến lược 2 (trước đó chưa trích) — chip riêng vì
  khách nêu đích danh "Tìm hiểu nguyên nhân gốc rễ".
- `k-xa-stress-nhanh` ← "Hướng dẫn cách xả stress hiệu quả, giúp giảm bớt triệu
  chứng nhanh chóng". **Sửa sau feedback customer:** giữ nguyên tiêu đề docx (bản
  đầu mình bỏ chữ "hiệu quả", đổi thành "Vài cách xả stress nhanh"), và trích
  **đủ 18 mục** nguyên văn (bản đầu chỉ lấy 6). Chỉ lược **tên bệnh viện + đoạn
  quảng cáo BVĐK Tâm Anh TP.HCM** ở cuối docx (test canh "Tâm Anh"/"Bệnh viện"
  không lọt vào body).

Chủ đề 4 chip: **5 → 8**.

> **Còn tồn:** hai node `k-nhan-dien-tu-phe-phan` (chiến lược 1) và `k-tu-tran-an`
> (chiến lược 3) đứng riêng từ trước có bản trích **rút gọn** ("việc học" thay vì
> "sự nghiệp", lược "lạm dụng chất kích thích"). Thẻ tổng quan `k-ngung-tu-huy-hoai`
> đã dùng bản nguyên văn. Nếu customer muốn đồng bộ, cập nhật 2 node kia theo.

> ### ⚠️ Đợt 3 (09/09) — `c-cac-dang-lo-au` thêm theo yêu cầu khách, NGƯỢC default
>
> Khách hỏi 3 lần vì sao "Các dạng rối loạn lo âu" không có, và chốt: *"các dạng
> đó là mục lý thuyết mà"*. Đã thêm thành chip, **biết là ngược [03 §7 luật 3]**
> (không bày danh sách hạng mục để học sinh tự soi) và ngược tiền lệ [§12](#12-xoay-chip-tìm-hiểu--và-vì-sao-không-random).
>
> Ba lớp giảm rủi ro, để hội đồng thấy đây là quyết định có cân nhắc chứ không
> phải sơ suất:
> 1. Trích **bản 4 dạng của NIMH** (GAD · hoảng sợ · lo âu xã hội · ám ảnh sợ),
>    KHÔNG lấy bảng 7 dòng của WHO (có thêm câm chọn lọc, lo âu chia ly — càng
>    hiếm càng dễ hiểu sai).
> 2. `steer` cứng: bot **cấm** hỏi "bạn thuộc dạng nào", cấm xác nhận khi học sinh
>    tự nhận, phải đóng khung "điểm chung của cả 4 là sợ/lo quá mức và kéo dài".
> 3. Trong `topics.yaml`, chip này đặt **ngay trước** `c-khong-phai-chan-doan` —
>    đọc "các dạng" xong thấy chip phủ nhận chẩn đoán ngay bên cạnh. Có test canh
>    thứ tự này (`test_chip_cac_dang_lo_au_co_va_di_kem_chip_chan_doan`).
>
> Nếu buổi chạy thử thấy học sinh vẫn tự soi bất chấp 3 lớp trên → gỡ chip này,
> giữ node để tới qua explained_by như `c-dau-hieu-*`.

**Đợt 2 (09/09, sau khi khách hỏi "sao không thấy mấy mục lớn"):** thêm 3 chip
khái niệm an toàn + 2 thẻ triệu chứng KHÔNG-chip. Hai thẻ `c-dau-hieu-*` chỉ lên
qua gate SUPPORT khi một node IMPACT (né tránh / mất động lực / thu mình) đã
CONFIRMED — "khi học sinh nói cụ thể thì lý thuyết tự lên", không phải nút bấm.
Cạnh `explained_by` CỐ Ý chỉ móc từ node IMPACT, không từ affect lõi (`a-lo-lang`,
`a-buon` nằm trong vòng lặp siêu tôi, dùng chung mọi chủ đề — §11).

**Vẫn KHÔNG trích:** "Tại sao / Cách NIMH nghiên cứu rối loạn lo âu" — meta về
nghị trình của một cơ quan nghiên cứu, chủ đề ngoài lứa tuổi (mang thai, sau sinh,
Addison…); số liệu tử vong – tự sát; bản dịch tiếng Anh; tên thuốc.
("Các dạng rối loạn lo âu" ban đầu cũng trong danh sách này — đã chuyển thành chip
ở đợt 3, xem cảnh báo trên.)

**Bốn thứ trong docx CỐ Ý không trích** — người duyệt cần biết để không tưởng là bỏ sót:
- **Danh sách triệu chứng** (lo âu: tim đập nhanh, đổ mồ hôi, mất ngủ… / trầm cảm:
  thay đổi thèm ăn, vô vọng…). Lý do: [mục 12](#12-xoay-chip-tìm-hiểu--và-vì-sao-không-random)
  — bày nút cho học sinh bấm đọc triệu chứng rồi tự soi là "gợi ý mang tính mớm".
  Cùng luật đã áp cho mục 3–4 của docx tìm hỗ trợ.
- **Số liệu tử vong / tự sát ở nhóm 15–29 tuổi.** Chính người soạn docx đã tự lược
  (`[Phần tiếp theo… mình không tái hiện chi tiết này]`).
- **Bản dịch tiếng Anh** xen kẽ trong phần "Trầm cảm" (nguồn Science News / Victoria
  University…).
- **Các câu xưng "nghiên cứu của bạn" / "đoạn bạn gửi" / "Gợi ý trích dẫn cho
  Literature Review"** — văn bản của bài nghiên cứu, không phải nội dung nói với học
  sinh (cùng lý do mục 1 "Giới thiệu đề tài" của docx siêu tôi không trích).

**Hai chỗ cắt câu giữa dòng** (ghi trong comment `concepts.yaml`, để người duyệt đối
chiếu docx): ở `c-suc-khoe-va-sieu-toi` bỏ `"Trong đoạn bạn gửi,"` và
`"Vì vậy, với nghiên cứu của bạn,"`. Không đổi nghĩa câu.

Ràng buộc cũ vẫn giữ:
- **"Tình huống cụ thể" là tình huống CỦA NGƯỜI DÙNG**, không phải vignette soạn sẵn.
  Docx chủ đề 3 có ví dụ "điểm thấp → khiến bố mẹ thất vọng → …" nằm trong
  `c-vong-lap-tram-cam` — đó là ví dụ MINH HOẠ CƠ CHẾ có nguồn, không phải vignette
  bịa; bot dùng nó để hỏi người dùng dừng ở bước nào, không kể thay họ.
- Từ **"lương tâm" xuất hiện 0 lần** trong cả 5 docx → chip sinh từ node có thật.

---

## 8. Kịch bản mẫu để duyệt — chủ đề 1

Phần **in đậm** là nguyên văn `concepts.yaml`, còn lại là chỗ LLM viết.

**Lượt 1** — bấm thẻ "Hiểu về cái siêu tôi" · `gate: SUPPORT (topic_opening)` ·
`KNOWLEDGE_CARD`

> Được, mình bắt đầu từ chỗ dễ hình dung nhất nhé.
> → thẻ **"Ba cách phản ứng bên trong mỗi người"** (`c-id-ego-superego`, đầy đủ, gồm
> ví dụ chơi game/bài kiểm tra)
> chip: `[Có phải cái siêu tôi luôn xấu không?]` `[Vậy khắt khe tới mức nào thì là
> quá?]` `[Vậy mình có đang bị gì không?]` `[Nghe giống chuyện của mình]` `[— Mình chỉ đọc thôi]`

**Lượt 2** — học sinh gõ tự do · `gate: CLARIFY` · `REFLECT`

> *Học sinh:* "Mình vừa được 6.5 môn Toán. Ba mẹ không mắng gì cả mà mình vẫn thấy
> mình tệ."
>
> Matcher bắt `"6.5"` + `"điểm"` → `t-diem-so`. Overlay 1 node, dưới
> `MIN_NODES_FOR_REFLECT = 3` → chưa được phản chiếu.
>
> *Bot:* "Ba mẹ không mắng gì cả mà mình vẫn thấy mình tệ" — câu đó nghe như cái tiêu
> chuẩn đang nằm ở phía bạn, chứ không phải phía ba mẹ. Con 6.5 đó, bạn thấy đáng lẽ
> nó phải là bao nhiêu?
> chip: `[Ít nhất phải 8]` `[Không có con số nào, chỉ thấy chưa đủ]`

**Lượt 3** — lý thuyết đáp xuống trên chính câu họ vừa nói · `gate: SUPPORT` ·
`KNOWLEDGE_CARD`

> *Học sinh:* "Ít nhất phải 8. Dưới đó là mình thấy không chấp nhận được."
>
> `"ít nhất phải"` là cue nguyên văn của `m-tieu-chuan-cao` → khớp chắc. Đủ bối cảnh
> + biểu hiện → mở được concept.
>
> *Bot:* Bạn vừa tự đặt ra một cái mốc — dưới 8 là không chấp nhận được. Chỗ này tài
> liệu có nói khá rõ:
> → thẻ **"Siêu tôi lành mạnh và Siêu tôi trừng phạt khác nhau ở đâu"**
> (`c-lanh-manh-vs-trung-phat`)
> *Bot:* Hai câu cuối khác nhau đúng một chữ "vì". Bạn thấy mình hay nói theo câu nào hơn?

**Điều kịch bản chứng minh:** menu kiến thức không giết vai bạn đồng hành. Chủ đề chỉ
là cửa; từ lượt 2 vẫn là hội thoại của họ, và lý thuyết đợi tới lượt 3 mới xuất hiện
— *sau* câu "ít nhất phải 8" — nên đọc như nói về họ, không như bài giảng.

---

## 9. Thứ tự làm

| # | Việc | Trạng thái |
|---|---|---|
| 1 | `backend/data/topics.yaml` | ✅ 08/09 |
| 2 | Áp D1 + D2 vào `concepts.yaml` / `00_CORE_PERSONA.md` | ✅ 09/09 |
| 3 | `app/graph/topics.py` — nạp + validate lúc khởi động | ✅ 09/09 |
| 4 | `overlay/model.py` · `api/session.py` · `api/chat.py` · `GET /api/topics` | ✅ 09/09 |
| 5 | `gate/decide.py` — topic_opening, topic_learn, D3, B-2, an toàn lên §0 | ✅ 09/09 |
| 6 | `phrases.py` + `chips.py` + `quick_reply.py` — chip `CHIP_LEARN` (`"◦ "`) | ✅ 09/09 |
| 7 | Frontend: 4 thẻ + giữ composer + giữ hotline | ✅ 09/09 |
| 8 | Gộp bài Likert vào chủ đề 2 (`?topic=` xuyên suốt) | ✅ 09/09 |
| 9 | Trích nội dung chủ đề 3 → bật `enabled` | ✅ 09/09 — xem [mục 7](#7-chủ-đề-3--đã-trích-nội-dung-09092026) |

**Kiểm chứng 09/09:** `pytest` **276 xanh** (thêm 2 test chủ đề 3:
`test_mo_chu_de_3_phat_the_co_che`, `test_chip_tim_hieu_chu_de_3_phat_dung_node`;
`test_ca_4_chu_de_deu_bat_va_co_noi_dung` thay cho test cũ canh `enabled: false`) ·
`npm run build` sạch · chạy thật qua TestClient khớp kịch bản A và E.

> **Việc 9 — mở lại 09/09 sau khi nhóm xác nhận đã soạn xong nội dung chủ đề 3 vào
> docx.** Quyết định hoãn trước đó ("làm tốt 3 chủ đề trước, khách gật rồi mới soạn
> chủ đề 3") đã được chính nhóm gỡ: nội dung có người viết trong
> `RỐI LOẠN LO ÂU & TRẦM CẢM.docx`, yêu cầu trích thẳng. Việc còn lại là chép nguyên
> văn — 4 đoạn nói được với học sinh; phần literature-review / triệu chứng / số liệu
> tử vong bỏ lại, lý do ghi ở [mục 7](#7-chủ-đề-3--đã-trích-nội-dung-09092026).

---

## 10. Checklist test trước demo

- [ ] Bấm từng chủ đề `enabled` → có thẻ nguyên văn phát ra, không lượt nào trống.
- [ ] Bấm **mọi** `learn_chip` → đều có node nguyên văn trả về, không có câu nào do
      mô hình tự chế.
- [ ] Bấm 3 chip TÌM HIỂU liên tiếp → **KHÔNG** rơi vào ORIENT (kiểm tra D3).
- [ ] Ở mỗi chủ đề, gõ một câu khủng hoảng → **ESCALATE + CRISIS_CARD + hotline**,
      bất kể đang ở chủ đề nào. Thêm vào `tests/test_safety_crisis.py`.
- [ ] Gõ chuyện hoàn toàn ngoài chủ đề → bot vẫn theo được, không ép quay lại bài
      giảng (kiểm tra D5: ưu tiên chứ không lọc).
- [ ] Bấm "Vậy mình có đang bị gì không?" → trả `c-khong-phai-chan-doan`, và bot
      **không** nói người dùng "bị" gì (kiểm tra D2).
- [ ] Chủ đề 3 `enabled: false` → **không hiện** trên màn chào, không phải hiện rồi
      báo lỗi.
- [ ] `npm run build` sạch · `pytest` xanh (81 test hiện có không được vỡ).


---

## 11. Thêm một mục lý thuyết mới — công thức 4 bước

Câu hỏi 09/09/2026: *"các mục lý thuyết như này phải được đề xuất trong quick
replies, và khi người ta bấm thì đưa lý thuyết lên?"* — **đúng, và đó chính là cơ
chế chip TÌM HIỂU ở mục 4.** Mỗi mục lý thuyết muốn bấm ra được cần đủ 4 thứ, thiếu
một là app không khởi động (cố ý):

| # | Làm gì | Ở đâu |
|---|---|---|
| 1 | Chép **NGUYÊN VĂN** đoạn docx vào `body`, thêm `steer` + `source` ghi rõ mục nào | `backend/data/content/concepts.yaml` |
| 2 | Khai node `c-<tên>` trỏ tới anchor vừa tạo | `backend/data/domain_graph.yaml` |
| 3 | Sửa số content node trong validator **và** 2 test chốt cứng số đó | `app/graph/loader.py` · `tests/test_graph.py` · `tests/test_api.py` |
| 4 | Thêm `learn_chips` trỏ tới node đó, ở **mọi chủ đề** thấy hợp | `backend/data/topics.yaml` |

Ba điều dễ vấp:

- **`steer` là bắt buộc với node `concept`** — `_validate()` chặn ở startup. `steer`
  là chỉ dẫn cho mô hình (viết mới được), khác `body` là nguyên văn tài liệu (không
  được sửa).
- **Chip trỏ theo `id`, không theo `source_doc`** — nên một node của docx A vẫn bày
  được ở chủ đề của docx B khi nội dung hợp. Đó là cách chủ đề 2 mượn được mục 6 và
  mục 7 của docx siêu tôi dù nó không có concept node nào của riêng mình.
- **Đừng thêm cạnh `explained_by` chỉ để "cho đủ"** — cạnh đó đổi concept mà gate
  SUPPORT phục vụ cho các node đã CONFIRMED, tức là đổi hành vi của luồng chính.
  Chip TÌM HIỂU tới được node mà không cần cạnh nào.

### Đã làm theo công thức này — 09/09/2026

`c-nhan-dien-hang-ngay` ← **`HIỂU VỀ CÁI SIÊU TÔI TRỪNG PHẠT.docx — mục 6**
("Nhận diện Cái siêu tôi trừng phạt trong đời sống hằng ngày"). Content node lên
**19**.

Mục này đáng chú ý vì nó là mục **duy nhất** trong toàn bộ 5 docx được viết dưới
dạng **câu hỏi để người đọc tự soi** — ba tình huống, mỗi tình huống hai vế đối
nhau (mắc lỗi · không đạt mục tiêu · được khen). Nên nó là bậc thang tự nhiên nhất
từ chế độ TÌM HIỂU sang chế độ KỂ CHUYỆN: bấm xong là có sẵn ba tình huống cụ thể
để hỏi tiếp *"bạn thấy mình ở vế nào"* — mà không phải bịa vignette nào, đúng lối
ra đã chốt ở mục 7.

Chip: `"Làm sao biết mình đang ở vế nào?"` (chủ đề 1) ·
`"Nhìn ra nó trong ngày thường kiểu gì?"` (chủ đề 2).

Chip cũ *"Vậy khắt khe tới mức nào thì là quá?"* đã **gỡ** — nó phát ra đúng cùng
một thẻ với chip *"Có phải cái siêu tôi luôn xấu không?"*, tức bày hai nút cho một
nội dung. Xem [03 §7 luật 8](03-OVERLAY-VA-GATE.md): hai chip cùng một hướng tính
là một chip.


---

## 12. Xoay chip TÌM HIỂU — và vì sao KHÔNG random

Sau đợt trích 09/09, chủ đề 1 có **6 chip** mà mỗi lượt chỉ hiện được **3**. Phải chọn.

**Luật đã cài** (`pipeline/quick_reply.py`): chip **chưa đọc lên trước**, trong mỗi
nhóm giữ nguyên thứ tự khai báo ở `topics.yaml`. Thẻ đã phát ghi vào
`overlay.the_da_xem`. Đọc hết một vòng thì chip cũ quay lại.

Yêu cầu ban đầu là *"ngẫu nhiên xuất hiện"*. Đã **đổi sang tất định**, vì random có
hai cái hại thật, không phải hại lý thuyết:

1. **Chip biến mất trước khi kịp bấm.** Học sinh nhìn thấy "Còn siêu tôi trừng phạt
   là gì?", đọc xong thẻ hiện tại, quay lên thì nó không còn — thay bằng một chip họ
   vừa đọc rồi. Random không phân biệt được đã đọc hay chưa.
2. **Demo và test mất tính lặp lại.** Kịch bản [14](14-KICH-BAN-4-CHU-DE.md) và bộ
   `tests/test_topics.py` không canh được gì nữa, và buổi demo trước hội đồng không
   diễn lại được đúng như lúc tập.

Cách tất định vẫn đạt đúng mục tiêu em muốn — **chip đổi qua từng lượt, và mọi mục lý
thuyết đều tới lượt được bày ra** — mà không mất hai thứ trên. Chạy thật 09/09, chủ đề
1: 6 lượt bấm liên tiếp đi qua đủ 6 mục, không lặp lại mục nào trước khi hết vòng.

### Đợt trích 09/09 — 8 mục, content node 18 → 26

| Chủ đề | Node mới | Nguồn |
|---|---|---|
| 1 | `c-sieu-toi-la-gi` · `c-sieu-toi-trung-phat-la-gi` · `c-nhan-dien-hang-ngay` · `c-vi-sao-dang-quan-tam` | HIỂU VỀ… mục 3, 4, 6, 7 |
| 2 | `c-bieu-hien-thuong-gap` · `c-thang-do-likert` | NHẬN DIỆN… phần mở đầu, phần thang đo |
| 4 | `c-tu-phe-phan-qua-muc` · `c-giup-mot-nguoi-ban` | KHI NÀO CẦN TÌM HỖ TRỢ… mục 1+2, phần giúp một người bạn |

**Hai mục CỐ Ý không làm chip** — `KHI NÀO CẦN TÌM HỖ TRỢ.docx` mục 3 ("dấu hiệu
giống triệu chứng trầm cảm") và mục 4 ("biểu hiện lo âu kéo dài"). Bày một nút mời
học sinh bấm để đọc danh sách triệu chứng rồi tự soi là đúng cạm bẫy **gợi ý mang
tính mớm** mà [03 §7 luật 3](03-OVERLAY-VA-GATE.md) cấm. Nội dung đó vẫn tới được —
qua gate BRIDGE, tức là khi hệ thống **đã có bằng chứng**, chứ không phải vì học sinh
tò mò bấm thử. Có test canh (`test_khong_bay_chip_trieu_chung_o_chu_de_4`).

Mục 1 của docx siêu tôi ("Giới thiệu về đề tài") cũng không trích: đó là văn bản hành
chính của bài nghiên cứu, không phải nội dung để nói với học sinh.


---

## 13. Lỗi phát hiện khi dùng thật — 09/09/2026

### 13.1. Làm xong bài test, bấm "Nói chuyện về kết quả này" → rơi về màn hình chào

**Triệu chứng:** làm 10 câu, ra band, bấm nút — và nhận về đúng màn "cuộc trò chuyện
mới" với 4 thẻ chủ đề. Kết quả biến mất.

**Nguyên nhân:** `/assessment` không tạo message nào trong chat. Quay về `/chat` thì
`started = messages.some(m => m.role === "user")` vẫn `false`, nên `ChatBody` render
`ChatWelcome` — đúng như code được viết. Đây là thứ [07 §2.2](07-FRONTEND.md) cấm:
*"Không bao giờ để màn hình kết quả là điểm dừng"* — nó không phải điểm dừng về mặt
điều hướng, nhưng là điểm dừng về mặt nội dung.

**Sửa:** `/chat?from=assessment` tự gửi hộ lượt đầu — `"Mình vừa làm xong bài tự đánh
giá."` — như một lượt người dùng bình thường (qua bước trích, hiện thành bong bóng của
họ), cùng cơ chế với chip. Không nhồi điểm số vào câu đó: bot đã biết bối cảnh qua
`{HAS_TAKEN_ASSESSMENT}` và qua 10 node LIKERT đã seed trong overlay.

Gate của lượt này là **CLARIFY**, đúng theo [B-2](03-OVERLAY-VA-GATE.md) — mọi bằng
chứng đều là LIKERT với `verbatim` rỗng nên chưa phản chiếu được, bot phải hỏi để lấy
lời thật trước. Đã chạy thử: đúng CLARIFY.

### 13.2. Vào thẳng `/assessment` → bài test rơi vào phiên mồ côi

Tìm ra khi đọc lại luồng ở 13.1. `/assessment` gọi `ensureSession()` (dùng lại phiên
trong sessionStorage, không có thì mở mới) và `POST /api/assessment` seed 10 node
LIKERT vào overlay của phiên **đó**. Nhưng `/chat` lúc khởi động chỉ đọc
`loadConversations()` từ localStorage; danh sách rỗng thì gọi `createSession()` — mở
một phiên **khác**. Toàn bộ bài test vừa làm nằm lại ở phiên cũ, bot hỏi lại từ đầu
như chưa có gì.

**Sửa:** khởi động `/chat` mà chưa có hội thoại nào nhưng `getCachedSession()` có giá
trị → nhận lại phiên đó thay vì mở phiên mới.

### 13.3. Dòng "Nguồn: …docx" vẫn hiện ở thẻ BRIDGE

[D4](#d4--dòng-nguồn-tên-filedocx-gỡ-khỏi-màn-hình) hôm 08/09 cố ý giữ dòng nguồn ở
riêng `bridge-card.tsx` với lập luận "thẻ hotline / phòng tham vấn thì ghi nguồn làm
tăng độ tin".

Lập luận đó **hỏng** kể từ khi chủ đề 4 có chip TÌM HIỂU trỏ tới `s-gvcn` / `s-ba-me`:
học sinh bấm *"Nói với thầy cô thì nói thế nào?"* và nhận về một cái tên file `.docx`.
Đã gỡ. Giờ **không màn hình nào** hiện `card.source`; trường này vẫn đi trong payload
và vẫn ghi vào transcript để bảo vệ đề tài.


### 13.4. Bot QUÊN SẠCH bài test — nó hỏi ngược lại người dùng ⚠️ nặng nhất

**Triệu chứng (quan sát thật 09/09):** làm xong 10 câu, bấm nút, và bot trả lời

> *"Cảm ơn bạn đã chia sẻ. Bạn có thể kể thêm về bài tự đánh giá đó không, cụ thể là
> bạn đã đánh giá những gì vậy?"*

Người vừa ngồi trả lời xong 10 câu bị bắt kể lại chính 10 câu đó.

**Nguyên nhân — hai tầng, cả hai đều là thiếu sót thiết kế:**

1. **`{HAS_TAKEN_ASSESSMENT}` chỉ là chuỗi `"có"` / `"chưa"`** — một cờ boolean.
   Mô hình biết CÓ một bài test nhưng không biết bài đó ra cái gì. Overlay có sẵn 10
   node LIKERT nhưng `verbatim` rỗng (họ tick ô, không gõ chữ) và
   **không có cây cầu `node_id` → phát biểu gốc**.
2. **Gate nhắm sai chỗ.** B-2 chặn REFLECT (đúng), nên lượt rơi xuống §5 và
   `highest_information_gain_node` chọn một node BẤT KỲ còn thiếu thông tin — chẳng
   liên quan gì tới bài vừa làm.

**Sửa:**

| Chỗ | Làm gì |
|---|---|
| `app/graph/likert.py` *(mới)* | Bắc cầu `node_id → phát biểu Likert`, nguyên văn `assessment.yaml` |
| `overlay/model.py` | Giữ `assessment_band_label` · `assessment_average` · `assessment_debriefed` |
| `api/assessment.py` | Ghi band + điểm vào overlay lúc chấm |
| `llm/turn.py::_khoi_bai_test()` | Dựng khối chữ thật cho `{HAS_TAKEN_ASSESSMENT}` |
| `00_CORE_PERSONA.md` | Mục "BÀI TỰ ĐÁNH GIÁ" + luật: **đừng hỏi lại họ đã đánh giá gì** |
| `gate/decide.py` §4a0 | Nhánh `assessment_debrief` — nhắm vào câu họ chấm CAO NHẤT, chỉ một lần |

Khối mô hình nhận được bây giờ:

```
RỒI — mức "Mức đáng chú ý" (trung bình 3.4/5). Những câu họ chọn "Hoàn toàn đúng":
  • Tôi thường tự trách bản thân khi mắc lỗi.
  • Tôi cảm thấy mình chưa đủ tốt dù đã cố gắng.
  • Tôi hiếm khi hài lòng với chính mình.
```

**CHỈ liệt kê câu chọn mức 5 (0.80).** Mức 4 = 0.65, dưới ngưỡng 0.70 — xem
[§3.1](03-OVERLAY-VA-GATE.md): "khá đúng" nghĩa là CHƯA CHẮC, kể nó ra như một lời
tự thú là sai. Có test canh (`test_chi_liet_ke_cau_chon_hoan_toan_dung`).

**Nhánh `assessment_debrief` chỉ chạy MỘT lần** (`assessment_debriefed`). Hỏi mãi về
cùng một câu Likert đọc như đang truy bài.

Ba điều persona bị cấm làm với kết quả: đọc lại cả danh sách (thành bảng chẩn đoán) ·
nói mức điểm nghĩa là họ "bị" gì (luật 1) · trấn an kiểu "điểm vậy cũng bình thường".
