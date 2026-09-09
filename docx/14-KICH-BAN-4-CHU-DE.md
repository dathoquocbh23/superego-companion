# 14 — KỊCH BẢN 4 CHỦ ĐỀ (để duyệt)

> Phụ lục kịch bản của [13-MENU-4-CHU-DE.md](13-MENU-4-CHU-DE.md). Cùng mục đích với
> [11-KICH-BAN-CHAT-MAU.md](11-KICH-BAN-CHAT-MAU.md): **đọc và duyệt trước khi code**.
>
> Câu hỏi cần trả lời khi đọc: *"Nếu em mình 17 tuổi bấm vào thẻ này, cái nó nhận
> được có ổn không?"*
>
> ⚠️ File này phát hiện thêm **4 chỗ spec chưa khớp** (đánh dấu ⚠️ trong từng kịch
> bản). Đọc hết trước khi implement mục 5 của file `13`.

---

## Cách đọc

| Ký hiệu | Nghĩa |
|---|---|
| 🧑 | Học sinh gõ hoặc bấm |
| 🤖 | Bot trả lời (đúng thứ người dùng nhìn thấy) |
| 📄 | Thẻ nội dung — **nguyên văn tài liệu**, không phải lời bot viết |
| ⚙️ | Trạng thái nội bộ — **người dùng KHÔNG thấy** |
| 💬 | Quick replies hiện dưới bubble |
| 📝 | Ghi chú thiết kế — chỗ cần duyệt kỹ |

## Hằng số dùng trong file này

| Hằng | Giá trị | Ở đâu |
|---|---|---|
| `confidence_threshold` | **0.70** | `config.py:54` |
| `min_nodes_for_reflect` | **3** | `config.py:57` |
| `cycle_activation_confidence` | 0.60 | `config.py:68` |
| `ORIENT_MIN_TURN` | 2 | `gate/decide.py:30` |
| `LIKERT_CONFIDENCE` | `5→0.80 · 4→0.65 · 3→0.40 · 2→0.15 · 1→0.15` | `overlay/model.py:32` |

## Bối cảnh chung

- Học sinh lớp 11, phiên ẩn danh, chưa đăng nhập, overlay bắt đầu **rỗng**
- Vào bằng cách **bấm thẻ chủ đề** ở màn chào (không gõ ô nhập trước)
- Banner *"Công cụ tìm hiểu kiến thức — không thay thế tư vấn tâm lý"* hiện suốt phiên

---

# A — CHỦ ĐỀ 1 · "Hiểu về cái siêu tôi"

## Lượt 1 — bấm thẻ

```
🧑  [bấm thẻ "Hiểu về cái siêu tôi"]
```

```
⚙️  TOPIC       topic_id = hieu-sieu-toi          (mới, cất trong Overlay)
⚙️  SAFETY      tier = null
⚙️  EXTRACT     — (không có text người dùng)
⚙️  OVERLAY     0 node
⚙️  GATE        SUPPORT — reason: topic_opening
⚙️  CONTENT     c-id-ego-superego  →  message_type = KNOWLEDGE_CARD
⚙️  TÌM HIỂU    luot_tim_hieu = 1
```

```
🤖  Được, mình bắt đầu từ chỗ dễ hình dung nhất nhé.
```

```
📄  Ba cách phản ứng bên trong mỗi người

    Theo Sigmund Freud, tâm lý con người có thể được nhìn nhận thông qua ba
    thành tố: Id, Ego và Superego. Có thể hiểu đơn giản đây là ba cách phản
    ứng khác nhau bên trong mỗi người khi chúng ta đứng trước một tình huống.

    Id → "Mình muốn!" — những mong muốn, nhu cầu và cảm xúc bản năng.
    Ego → "Mình có thể làm gì?" — nhìn vào thực tế và cân nhắc trước khi hành động.
    Superego → "Mình nên / phải làm gì?" — những quy tắc, giá trị, chuẩn mực
    và kỳ vọng mà chúng ta dần hình thành trong quá trình lớn lên.

    Ví dụ: Ngày mai có bài kiểm tra nhưng hôm nay bạn rất muốn chơi game.
    Id: "Chơi một chút đi, học sau cũng được!" → Ego: "Mình có thể học trước
    một tiếng rồi chơi sau." → Superego: "Mình phải học thật tốt. Không được
    lãng phí thời gian!"

    Superego không phải lúc nào cũng tiêu cực. Vấn đề có thể xuất hiện khi
    những tiêu chuẩn và yêu cầu dành cho bản thân trở nên quá khắt khe.
```

```
💬  [ Có phải cái siêu tôi luôn xấu không? ]   [ Vậy khắt khe tới mức nào thì là quá? ]
    [ Vậy mình có đang bị gì không? ]          [ Nghe giống chuyện của mình ]
    [ — Mình chỉ đọc thôi ]
```

> 📝 **Duyệt gì ở đây:**
> - Bot **chỉ viết 1 câu dẫn**. Toàn bộ phần lý thuyết là thẻ nguyên văn. Đây là
>   cách duy nhất thoả mãn cùng lúc yêu cầu *"giải thích chay về lý thuyết"* của
>   khách và luật *"2–5 câu, không giảng đạo"* của `00_CORE_PERSONA.md` — xem
>   [13 mục 5.7](13-MENU-4-CHU-DE.md).
> - Ví dụ chơi game/bài kiểm tra **đã nằm sẵn trong thẻ**. Đó là ví dụ DUY NHẤT có
>   trong toàn bộ docx này, nên bước "đưa vô tình huống cụ thể" của khách coi như
>   xong ngay ở lượt 1 — không phải bịa thêm vignette nào.
> - 3 chip TÌM HIỂU + 1 chip bắc cầu + 1 chip thoát = đúng công thức
>   [13 mục 4](13-MENU-4-CHU-DE.md).

---

## Lượt 2 — bấm chip TÌM HIỂU

```
🧑  [bấm] Vậy mình có đang bị gì không?
```

```
⚙️  CHIP        LEARN  →  serves = c-khong-phai-chan-doan
⚙️  SAFETY      tier = null
⚙️  EXTRACT     — (chip LEARN không đi qua bước trích)
⚙️  OVERLAY     0 node  — KHÔNG tính là giậm chân (xem ⚠️ A-1)
⚙️  GATE        SUPPORT — reason: topic_learn
⚙️  TÌM HIỂU    luot_tim_hieu = 2
```

```
🤖  Câu này tài liệu có nói thẳng luôn.
```

```
📄  Đây không phải một chẩn đoán

    "Cái siêu tôi trừng phạt" là một khái niệm lý thuyết trong phân tâm học,
    không nên trình bày như một chẩn đoán / bệnh độc lập. Vì vậy nên nói
    "khi có biểu hiện của Siêu tôi trừng phạt", thay vì "khi mắc bệnh".

    Những biểu hiện tự trách, đặt tiêu chuẩn cao hay khó chấp nhận sai sót
    là những đặc điểm có thể xuất hiện ở các mức độ khác nhau. Việc nhận diện
    chúng giúp mỗi người hiểu rõ hơn về cách mình đang phản ứng với sai lầm
    và áp lực — không phải để gắn nhãn hay đánh giá một người.
```

```
💬  [ Vậy khắt khe tới mức nào thì là quá? ]   [ Nghe giống chuyện của mình ]
    [ — Mình chỉ đọc thôi ]
```

> 📝 **Đây là lượt quan trọng nhất của cả file.**
>
> Khách phát biểu mục đích là *"để học sinh hiểu mình đang bị gì"*
> ([13 mục 6/D2](13-MENU-4-CHU-DE.md)). Học sinh cũng sẽ hỏi đúng câu đó. Và câu trả
> lời **đã có sẵn nguyên văn trong tài liệu của chính khách** — nó nói: đây không
> phải chẩn đoán, không ai "bị" gì cả.
>
> Nên bot **không phải né câu hỏi, cũng không phải phá luật**. Nó trả lời thẳng,
> bằng chữ của tài liệu. Ý khách được phục vụ, luật 1 của persona vẫn nguyên.
>
> **Đừng gỡ chip này khỏi `topics.yaml`.**

> ### ⚠️ A-1 — nếu không sửa D3 thì lượt này đã hỏng
>
> Chip LEARN không mang cue → overlay vẫn 0 node. Mà `_bi_giam_chan()` hiện tại:
>
> ```python
> if not overlay.so_node_noi_duoc():
>     return overlay.turn_count >= ORIENT_MIN_TURN   # = 2
> ```
>
> `turn_count = 2` → **gate bắn ORIENT**, và bot nói *"Mình thấy mình đang hỏi hơi
> lòng vòng mà chưa giúp được gì thật"* — giữa lúc học sinh vừa bấm một câu hỏi rất
> rõ ràng và đang đọc bình thường.
>
> **Sửa:** trừ `luot_tim_hieu` ra khỏi `turn_count` khi xét giậm chân. Xem
> [13 mục 6/D3](13-MENU-4-CHU-DE.md).

---

## Lượt 3 — bấm chip bắc cầu

```
🧑  [bấm] Nghe giống chuyện của mình
```

```
⚙️  CHIP        — (chip bắc cầu CỐ Ý không mang tiền tố hệ thống: nó phải đi
                   qua bước trích như một tin nhắn thường)
⚙️  SAFETY      tier = null
⚙️  EXTRACT     0 node  — câu này không khớp cue nào, đúng như thiết kế
⚙️  OVERLAY     0 node
⚙️  GIẬM CHÂN   turn_count 3 − luot_tim_hieu 2 = 1  <  ORIENT_MIN_TURN 2  → KHÔNG bắn ORIENT
⚙️  GATE        CLARIFY — reason: empty_overlay
⚙️  TARGET      (chưa nhắm node — vùng graph còn trống)
```

```
🤖  Vậy kể mình nghe với. Giống ở chỗ nào?
```

```
💬  [ Chuyện điểm số ]   [ Chuyện ở nhà ]   [ — Mình chưa muốn kể ]
```

> 📝 Từ lượt này trở đi **chế độ đã đổi**: không còn là bài giảng, mà là cỗ máy
> overlay/gate cũ. Bot ngắn lại, hỏi đúng một câu, không kèm thẻ. Đây chính là bước
> [2] trong luồng của khách — và là lý do **ô nhập tự do không thể bỏ**.

---

## Lượt 4 — học sinh gõ chuyện của mình

```
🧑  Mình vừa được 6.5 môn Toán. Ba mẹ không mắng gì cả mà mình vẫn thấy mình tệ.
    Với mình ít nhất phải 8.
```

```
⚙️  SAFETY      tier = null
⚙️  EXTRACT     t-diem-so        | literal | 0.75 | "6.5 môn Toán"
⚙️              m-tieu-chuan-cao | literal | 0.75 | "ít nhất phải 8"
⚙️  OVERLAY     2 node (SELF_REPORT: 2)
⚙️  CYCLE       chưa hoạt hoá
⚙️  GATE        CLARIFY — reason: default
⚙️              (REFLECT cần ≥ 3 node ≥ 0.70; SUPPORT cần có CONFIRMED + đã REFLECT)
⚙️  TARGET      m-chua-du-tot
```

```
🤖  "Ba mẹ không mắng gì cả mà mình vẫn thấy mình tệ" — nghe như cái tiêu chuẩn
    đang nằm ở phía bạn, chứ không phải phía ba mẹ. Lúc nhìn con 6.5 đó, bạn
    nói gì với mình trong đầu?
```

```
💬  [ Kiểu "cố mãi vẫn vậy" ]   [ Mình không nghĩ gì cả, chỉ thấy nặng ]
    [ Không phải chuyện điểm ]  [ — Mình chưa muốn nói về chuyện này ]
```

> 📝 Bot **dùng lại nguyên văn chữ của học sinh**, đúng một câu hỏi, không lời khuyên,
> không thẻ. Chip 3 là **chip bác bỏ tiền đề** — bot vừa giả định ("tiêu chuẩn nằm ở
> phía bạn") nên bắt buộc chừa đường nói "sai rồi".

> ### ⚠️ A-2 — bước "giáo viên phân tích" KHÔNG đến ở lượt 3–4
>
> Khách hình dung: lý thuyết → học sinh hỏi → *"giáo viên dựa vô đó phân tích"*. Nhưng
> gate hiện tại đòi khá nhiều trước khi được "phân tích":
>
> ```
> SUPPORT  cần:  có evidence CONFIRMED  +  REFLECT đã từng chạy  +  lượt trước không phải SUPPORT
> REFLECT  cần:  ≥ 3 node ≥ 0.70 (SELF_REPORT/LIKERT), hoặc một cycle đã hoạt hoá
> ```
>
> Thực tế là **lượt 6–7**, không phải lượt 3–4: cần thêm 1 node nữa → REFLECT →
> học sinh bấm "Đúng vậy" (CONFIRMED) → mới tới SUPPORT.
>
> **Khuyến nghị: KHÔNG nới điều kiện gate cho chế độ chủ đề.** Ba node là mức tối
> thiểu để một lời phản chiếu không phải là đoán mò — nới ra là quay lại đúng lỗi
> ngày 08/09 đã ghi ở [11 Phần C](11-KICH-BAN-CHAT-MAU.md).
>
> Đường tắt đã có sẵn mà không phải phá luật: chip **"Vậy khắt khe tới mức nào thì là
> quá?"** phát thẳng thẻ `c-lanh-manh-vs-trung-phat` bất cứ lúc nào. Tức là mình có
> **hai đường giao cùng một nội dung** — chip là *theo yêu cầu*, gate là *cá nhân
> hoá*. Đừng nhầm hai đường đó với nhau.

---

# B — CHỦ ĐỀ 2 · "Nhận diện trong đời sống học sinh"

Chủ đề này **không có concept node nào** — nội dung của nó chính là bài tự đánh giá
10 câu, vì cả 10 câu Likert đều mang `source_doc` của docx này.

## Lượt 1 — bấm thẻ

```
🧑  [bấm thẻ "Nhận diện trong đời sống học sinh"]
```

```
⚙️  TOPIC       topic_id = nhan-dien-hoc-sinh
⚙️  GATE        SUPPORT — reason: topic_opening
⚙️  CONTENT     opening = assessment  →  KHÔNG gọi LLM, frontend nhúng form Likert
```

```
🤖  Chủ đề này mình làm ngược lại một chút: thay vì mình kể, bạn tự chấm trước nhé.
    10 câu, khoảng 2 phút. Không phải bài kiểm tra.
```

```
📄  [FORM 10 CÂU LIKERT — thang 1..5]
    1. Tôi thường tự trách bản thân khi mắc lỗi.
    2. Tôi khó tha thứ cho bản thân dù chỉ là sai sót nhỏ.
    …
    10. Tôi thường chỉ nhớ đến những lỗi sai của mình hơn là những điều mình làm tốt.

    Bài đánh giá này được xây dựng nhằm giúp bạn nhận diện những đặc điểm liên
    quan đến Cái siêu tôi trừng phạt, không phải công cụ chẩn đoán tâm lý.
```

---

## Lượt 2 — nộp bài

```
🧑  [nộp: trung bình 3.4 — trả lời 5 ở câu 1, 3, 9]
```

```
⚙️  POST /api/assessment
⚙️  OVERLAY     has_taken_assessment = true
⚙️  SEED        10 node LIKERT, nhưng chỉ 3 node ≥ 0.70 (xem ⚠️ B-1)
⚙️              m-tu-trach 0.80 · m-chua-du-tot 0.80 · m-hiem-hai-long 0.80
⚙️  BAND        DANG_CHU_Y (3.01–4.00)
```

```
📄  Bạn đang có khá nhiều biểu hiện liên quan

    Bạn đang ghi nhận khá nhiều đặc điểm thường liên quan đến Cái siêu tôi
    trừng phạt, chẳng hạn như tự phê bình, khó chấp nhận sai sót, đặt tiêu
    chuẩn cao hoặc cảm thấy mình chưa đủ tốt dù đã cố gắng. Điều đáng chú ý
    không chỉ là bạn đã mắc lỗi gì, mà còn là cách bạn đối xử với chính mình
    sau khi mắc lỗi.

    Bạn có thể đang trải qua một vòng lặp như: Đặt kỳ vọng cao → Không đạt
    kỳ vọng → Tự phê bình → Cảm thấy chưa đủ tốt → Tiếp tục đặt áp lực lên
    bản thân.

    Bạn nên làm gì? Đừng vội cố gắng trở nên "hoàn hảo" hơn. Trước tiên, hãy
    học cách nhận diện những suy nghĩ quá khắt khe với bản thân và phân biệt
    chúng với những phản hồi thực sự giúp bạn tiến bộ.
```

```
💬  [ Nói chuyện về kết quả này ]
```

> 📝 Kết quả **không bao giờ là màn hình cuối** — luật đã ghi ở đầu `assessment.yaml`.
> Nút duy nhất dẫn thẳng sang chat, và giờ là chat **trong cùng chủ đề**, không phải
> nhảy route như bản cũ.

---

## Lượt 3 — nói chuyện về kết quả

```
🧑  [bấm] Nói chuyện về kết quả này
```

```
⚙️  OVERLAY     3 node ≥ 0.70, tất cả source = LIKERT
⚙️  GATE        REFLECT — reason: min_nodes_reached, mode = single
⚙️  TARGET      m-tu-trach · m-chua-du-tot · m-hiem-hai-long
⚙️  VERBATIM    (rỗng — xem ⚠️ B-2)
```

```
🤖  ??? — chưa duyệt được, xem ⚠️ B-2
```

> ### ⚠️ B-1 — trả lời "Khá đúng" KHÔNG đủ để vào overlay
>
> `LIKERT_CONFIDENCE`: `5 → 0.80` · **`4 → 0.65`** · `3 → 0.40`. Ngưỡng là **0.70**.
>
> Nghĩa là chỉ câu nào học sinh chọn **"Hoàn toàn đúng"** mới vượt ngưỡng. Chọn
> "Khá đúng" cả 10 câu → điểm trung bình 4.0 (band *Đáng chú ý*) nhưng **0 node nào
> đủ mạnh**, gate rơi về CLARIFY và bot hỏi lại từ đầu như chưa có bài test.
>
> Cần quyết: (a) chấp nhận — coi 4 là "chưa chắc", hay (b) nâng `4 → 0.72`. Anh
> nghiêng về **(a)**, vì hạ ngưỡng cho một câu tick chọn là biến một cú bấm thành
> lời tự thú. Nhưng phải **ghi rõ trong docx**, không để lòi ra lúc demo.

> ### ⚠️ B-2 — REFLECT ngay sau bài test KHÔNG có chữ nào để phản chiếu
>
> `api/assessment.py` seed evidence với `verbatim=""` cho cả 10 node. Mà REFLECT được
> dựng quanh việc **đọc lại nguyên văn lời người dùng** (`_verbatim_list`,
> `speakable_verbatims`), và `00_CORE_PERSONA.md` cấm thẳng câu *"Mình hiểu cảm giác
> của bạn"* — thay bằng dùng lại chính chữ họ nói.
>
> Sau bài test thì **không có chữ nào của họ cả** — chỉ có 10 ô tick.
>
> Ba lối ra, cần chọn trước khi code:
> 1. Seed `verbatim` = chính câu Likert học sinh chọn 5 (*"Tôi thường tự trách bản
>    thân khi mắc lỗi."*). Rẻ nhất, nhưng đó là **chữ của tài liệu, không phải chữ
>    của học sinh** — phản chiếu lại nghe như đọc bài.
> 2. Chặn REFLECT khi mọi evidence đều là LIKERT → ép CLARIFY một lượt để lấy lời
>    thật trước, rồi mới phản chiếu. **Anh nghiêng về cách này.**
> 3. Viết một skill riêng cho "phản chiếu sau bài test", nói thẳng là dựa trên bài
>    test chứ không giả vờ nhớ lời họ nói.
>
> Chưa chọn thì **chưa viết được lời thoại lượt 3**, nên ô 🤖 ở trên để trống có chủ ý.

---

# C — CHỦ ĐỀ 4 · "Khi nào nên tìm hỗ trợ"

## Lượt 1 — bấm thẻ

```
🧑  [bấm thẻ "Khi nào nên tìm hỗ trợ"]
```

```
⚙️  TOPIC       topic_id = khi-nao-tim-ho-tro
⚙️  GATE        SUPPORT — reason: topic_opening
⚙️  CONTENT     c-vong-lap-tu-phe-phan  →  KNOWLEDGE_CARD
⚙️  TÌM HIỂU    luot_tim_hieu = 1
```

```
🤖  Chủ đề này mình bắt đầu bằng cái vòng mà tài liệu mô tả, rồi tính tiếp nhé.
```

```
📄  Khi tự phê phán chuyển thành một vòng lặp khó thoát

    Tiêu chuẩn quá khắt khe
     → Không đạt tiêu chuẩn
     → Tự phê phán
     → Tội lỗi / xấu hổ
     → Cảm thấy bản thân kém giá trị
     → Căng thẳng
     → Càng cố gắng hoàn hảo
     → Lại tự phê phán

    Khi một người không còn tự mình phá vỡ được vòng lặp này, đó là lúc tìm
    kiếm sự hỗ trợ trở nên phù hợp.
```

```
💬  [ Mình có thể tự làm gì ở nhà không? ]   [ Nói với ba mẹ thì mở lời sao? ]
    [ Nói với thầy cô thì nói thế nào? ]     [ Mình chưa biết mình có cần không ]
    [ — Mình chỉ đọc thôi ]
```

---

## Lượt 2 — bấm chip TÌM HIỂU trỏ tới nguồn hỗ trợ

```
🧑  [bấm] Nói với ba mẹ thì mở lời sao?
```

```
⚙️  CHIP        LEARN  →  serves = s-ba-me   (node type = resource, KHÔNG phải concept)
⚙️  GATE        SUPPORT — reason: topic_learn
⚙️  CONTENT     s-ba-me  →  message_type = BRIDGE_CARD   (xem ⚠️ C-1)
⚙️  OVERLAY     0 node · bridge_offered = false          (xem ⚠️ C-1)
⚙️  TÌM HIỂU    luot_tim_hieu = 2
```

```
🤖  Tài liệu có sẵn một đoạn để bạn mượn lời luôn.
```

```
📄  Nếu bạn muốn nói với ba mẹ

    Bạn không cần phải giải thích ngay về "cái Siêu tôi trừng phạt" hay dùng
    các thuật ngữ tâm lý. Hãy bắt đầu bằng những gì bạn đang cảm thấy và nó
    ảnh hưởng đến bạn ra sao. Bạn có thể nói:

    "Dạo này con cảm thấy mình tự trách bản thân rất nhiều. Những lỗi nhỏ
    cũng khiến con suy nghĩ mãi và con thường cảm thấy mình chưa đủ tốt.
    Điều này đang làm con khá căng thẳng và ảnh hưởng đến việc học / ngủ của
    con. Con muốn kể cho ba mẹ nghe và mong ba mẹ giúp con tìm người có
    chuyên môn để nói chuyện."

    Nếu khó nói trực tiếp, bạn có thể nhắn tin hoặc viết thư cho ba mẹ trước.
    […]
```

---

## Lượt 3 — học sinh phản đối

```
🧑  Ba mẹ mình không hiểu mấy chuyện này đâu, nói ra kiểu gì cũng bị mắng.
```

```
⚙️  SAFETY      tier = null
⚙️  EXTRACT     t-gia-dinh | literal | 0.75 | "ba mẹ mình không hiểu"
⚙️  OVERLAY     1 node
⚙️  GATE        CLARIFY — reason: default
```

```
🤖  "Nói ra kiểu gì cũng bị mắng" — vậy là chuyện này bạn cân nhắc rồi chứ không
    phải chưa nghĩ tới. Ngoài ba mẹ, ở trường có ai bạn thấy dễ nói hơn không?
```

```
💬  [ Có một cô mình khá quý ]   [ Không ai cả ]   [ — Mình chưa muốn nói chuyện này ]
```

> 📝 Bot **không cãi lại** và **không nài** ("thử nói với ba mẹ đi mà"). Nó công nhận
> phản đối rồi mở một cửa khác — đúng luật ở `15_BRIDGE.md`.

> ### ⚠️ C-1 — chip LEARN trỏ tới `resource` node cần xử lý riêng
>
> `topics.yaml` chủ đề 4 có 2 chip trỏ tới node `s-*` (`s-gvcn`, `s-ba-me`), không
> phải `c-*`. Hai chỗ phải sửa:
>
> 1. **`message_type` phải là `BRIDGE_CARD`**, không phải `KNOWLEDGE_CARD`.
>    `runner.py:320` hiện chỉ nhìn `concept_node` / `coping_node` — thêm nhánh cho
>    `resource_node` khi `reason == "topic_learn"`.
> 2. **KHÔNG được set `overlay.bridge_offered = true`.** Cờ đó dùng để chặn gate
>    BRIDGE nổ hai lần. Học sinh tự bấm đọc thử cách mở lời **không phải** là hệ
>    thống đã bắc cầu cho họ — set nhầm thì sau này thật sự cần bắc cầu, gate im
>    lặng.

---

# D — CHỦ ĐỀ 3 · "Ảnh hưởng đến sức khoẻ tinh thần"

> Viết 09/09/2026 sau khi trích 4 concept node từ `RỐI LOẠN LO ÂU & TRẦM CẢM.docx`
> ([13 mục 7](13-MENU-4-CHU-DE.md)). Phần 📄 là **nguyên văn `concepts.yaml`**; phần
> 🤖 không có 📄 là chỗ LLM viết (1–2 câu dẫn).

## Lượt 1 — bấm thẻ

```
🧑  [bấm thẻ "Ảnh hưởng đến sức khoẻ tinh thần"]
```

```
⚙️  TOPIC       topic_id = anh-huong-suc-khoe
⚙️  SAFETY      tier = null
⚙️  OVERLAY     0 node
⚙️  GATE        SUPPORT — reason: topic_opening
⚙️  CONTENT     c-suc-khoe-va-sieu-toi  →  message_type = KNOWLEDGE_CARD
⚙️  TÌM HIỂU    luot_tim_hieu = 1
```

```
🤖  Chủ đề này nói về chuyện áp lực bên trong ảnh hưởng tới sức khoẻ tinh thần
    thế nào. Bắt đầu bằng cái khung mà tài liệu mô tả nhé.
```

```
📄  Cái siêu tôi trừng phạt liên hệ với sức khoẻ tinh thần thế nào

    Điều đầu tiên cần phân biệt: WHO không nói rằng "cái Siêu tôi trừng phạt
    gây ra trầm cảm". WHO giải thích trầm cảm là kết quả của sự tương tác
    phức tạp giữa các yếu tố xã hội, tâm lý và sinh học.

    Cách diễn đạt đúng hơn là: Cái Siêu tôi trừng phạt có thể là một cơ chế
    tâm lý góp phần làm gia tăng tính dễ tổn thương đối với các biểu hiện
    trầm cảm, đặc biệt thông qua tự phê phán, cảm giác tội lỗi và cảm nhận
    bản thân có giá trị thấp.

    Có thể hình dung theo một mô hình:
    Cái Siêu tôi trừng phạt hoạt hóa
     → Tự phê phán, tự buộc tội, cảm giác tội lỗi quá mức
     → Cảm nhận bản thân tiêu cực + giảm giá trị bản thân
     → Căng thẳng tâm lý kéo dài
     → Khó thích nghi với thất bại / xung đột
     → Tăng nguy cơ xuất hiện các triệu chứng trầm cảm

    Điểm mấu chốt là học sinh không chỉ trải qua một thất bại, mà có thể diễn
    giải thất bại đó thành một phán xét về chính bản thân mình, chẳng hạn:
    "Mình làm bài không tốt" → "Mình kém cỏi" → "Mình luôn làm mọi thứ sai"
    → "Mình không có giá trị."
```

```
💬  [ Rối loạn lo âu là gì? ]   [ Trầm cảm là gì? ]
    [ Áp lực trong đầu thành suy nghĩ về bản thân kiểu gì? ]
    [ Dạo này mình thấy mệt lắm ]   [ — Mình chỉ đọc thôi ]
```

> 📝 **Duyệt gì ở đây:**
> - Thẻ mở đầu KHÔNG phải danh sách triệu chứng — nó là **cơ chế** + câu phân biệt
>   *"WHO không nói siêu tôi trừng phạt gây ra trầm cảm"*. Đây là chỗ [13 mục 6/D2](13-MENU-4-CHU-DE.md)
>   đòi: mô tả để học sinh tự đối chiếu, không dán nhãn.
> - Chủ đề 3 có **8 chip TÌM HIỂU**, mỗi lượt hiện 3 (xoay vòng tất định, chưa đọc
>   lên trước): *lo âu là gì · trầm cảm là gì · áp lực thành suy nghĩ về bản thân ·
>   vì sao có người bị có người không · mình tự làm gì được · trầm cảm chữa được
>   không · lo âu có mấy dạng · mình có đang bị gì không*. + 1 chip bắc cầu + 1 chip
>   thoát. Chip "lo âu có mấy dạng" (`c-cac-dang-lo-au`) thêm theo yêu cầu khách,
>   ngược default an toàn — xem ⚠️ D-3.
> - Chuỗi *"Mình làm bài không tốt → … → Mình không có giá trị"* nằm SẴN trong thẻ —
>   nó là bậc thang sang bước [2], y như ví dụ chơi game ở chủ đề 1.
> - **KHÔNG có chip** cho `c-dau-hieu-lo-au` / `c-dau-hieu-tram-cam` (danh sách
>   triệu chứng). Hai thẻ đó chỉ lên ở **lượt 4+** qua gate SUPPORT, khi học sinh
>   đã kể ra một biểu hiện chức năng (né tránh / mất động lực / thu mình) và node
>   đó được CONFIRMED — xem ⚠️ D-2.

---

## Lượt 2 — bấm chip TÌM HIỂU

```
🧑  [bấm] Trầm cảm là gì?
```

```
⚙️  CHIP        LEARN  →  serves = c-tram-cam-la-gi
⚙️  SAFETY      tier = null
⚙️  OVERLAY     0 node  — KHÔNG tính giậm chân (D3, trừ luot_tim_hieu)
⚙️  GATE        SUPPORT — reason: topic_learn
⚙️  TÌM HIỂU    luot_tim_hieu = 2
```

```
🤖  Đoạn này là định nghĩa của WHO.
```

```
📄  Trầm cảm là gì

    Rối loạn trầm cảm (còn được gọi là trầm cảm) là một rối loạn tâm thần
    phổ biến. Trầm cảm biểu hiện bằng khí sắc trầm hoặc sự mất hứng thú hay
    mất khả năng cảm nhận niềm vui trong các hoạt động và kéo dài trong một
    khoảng thời gian đáng kể.

    Trầm cảm khác với những thay đổi tâm trạng thông thường và những cảm xúc
    xuất hiện trong đời sống hằng ngày. Trầm cảm có thể ảnh hưởng đến mọi mặt
    của cuộc sống, bao gồm các mối quan hệ với gia đình, bạn bè và cộng đồng.
    Trầm cảm có thể là nguyên nhân dẫn đến hoặc làm gia tăng các vấn đề trong
    học tập và công việc.

    Trầm cảm có thể xảy ra với bất kỳ ai. Những người từng trải qua sự ngược
    đãi, những mất mát nghiêm trọng hoặc các sự kiện gây căng thẳng khác có
    khả năng mắc trầm cảm cao hơn.
```

```
💬  [ Rối loạn lo âu là gì? ]
    [ Áp lực trong đầu thành suy nghĩ về bản thân kiểu gì? ]
    [ Dạo này mình thấy mệt lắm ]   [ — Mình chỉ đọc thôi ]
```

> 📝 Bấm 2 chip TÌM HIỂU liên tiếp (lượt 1→2) **không** làm gate bắn ORIENT — cùng
> cơ chế D3 đã canh ở [⚠️ A-1](#-a-1--nếu-không-sửa-d3-thì-lượt-này-đã-hỏng). Thẻ đã
> đọc (`c-suc-khoe-va-sieu-toi`) tụt xuống cuối, chip mới lên.

---

## Lượt 3 — bấm chip bắc cầu

```
🧑  [bấm] Dạo này mình thấy mệt lắm
```

```
⚙️  CHIP        — (bắc cầu, KHÔNG mang tiền tố — đi qua bước trích như tin thường)
⚙️  SAFETY      tier = null        ← "mệt" một mình KHÔNG phải cue khủng hoảng (docx/04)
⚙️  EXTRACT     0 node  (câu quá chung, chưa khớp cue nào)
⚙️  OVERLAY     0 node
⚙️  GIẬM CHÂN   turn_count 3 − luot_tim_hieu 2 = 1  <  2  → KHÔNG bắn ORIENT
⚙️  GATE        CLARIFY — reason: empty_overlay
```

```
🤖  Kể mình nghe với — "mệt" ở đây là mệt kiểu gì? Mệt người, hay mệt trong đầu?
```

```
💬  [ Mệt kiểu không muốn làm gì ]   [ Chuyện học ]   [ — Mình chưa muốn kể ]
```

> 📝 Từ lượt này chế độ đã đổi: hết bài giảng, quay về cỗ máy overlay/gate. Bot ngắn,
> hỏi một câu, không kèm thẻ. Đây là bước [2] của khách — lý do ô nhập tự do không bỏ.

---

## Lượt 4 — học sinh kể chuyện của mình

```
🧑  Mình học kiểu gì cũng thấy chưa đủ. Điểm cao vẫn thấy mình lẽ ra phải hơn,
    tối nào cũng nằm nghĩ lại mấy chỗ làm sai.
```

```
⚙️  SAFETY      tier = null
⚙️  EXTRACT     m-tieu-chuan-cao   | literal | 0.75 | "kiểu gì cũng thấy chưa đủ"
⚙️              m-suy-nghi-lai-loi | literal | 0.70 | "nằm nghĩ lại mấy chỗ làm sai"
⚙️  OVERLAY     2 node (SELF_REPORT: 2)
⚙️  GATE        CLARIFY — reason: default   (chưa đủ 3 node ≥ 0.70 để REFLECT)
⚙️  TARGET      m-chua-du-tot
```

```
🤖  "Điểm cao vẫn thấy mình lẽ ra phải hơn" — nghe như cái mốc nó tự dời lên mỗi
    lần bạn với tới. Lúc nằm nghĩ lại mấy chỗ sai đó, trong đầu bạn nói gì với mình?
```

```
💬  [ Kiểu "biết vậy mà vẫn để sai" ]   [ Không thành câu, chỉ thấy khó chịu ]
    [ Không hẳn vậy đâu ]   [ — Mình chưa muốn nói thêm ]
```

> 📝 Bot dùng lại **nguyên văn chữ học sinh**, đúng một câu hỏi, không thẻ, không lời
> khuyên. Chip 3 là chip bác bỏ tiền đề. Lý thuyết ở lượt 1 giờ đọc như nói về chính
> chuyện họ vừa kể — không phải bài giảng.

> ### ⚠️ D-1 — chuỗi "điểm thấp → khiến bố mẹ thất vọng → …" trong thẻ là VÍ DỤ CÓ NGUỒN
>
> Thẻ `c-vong-lap-tram-cam` chứa ví dụ leo thang cụ thể. Đây **không** vi phạm luật
> "không vignette soạn sẵn" ở [13 mục 7](13-MENU-4-CHU-DE.md): ví dụ này nằm nguyên
> văn trong docx, có nguồn. Nhưng bot **không được kể nó thay học sinh** — chỉ dùng
> để hỏi *"bạn có dừng ở bước nào giống vậy không"*. Kể thay = mớm.

> ### ⚠️ D-2 — thẻ triệu chứng chỉ lên khi IMPACT đã CONFIRMED, không sớm hơn
>
> `c-dau-hieu-lo-au` / `c-dau-hieu-tram-cam` (danh sách triệu chứng WHO) **không có
> chip**. Đường duy nhất tới chúng: học sinh kể ra một biểu hiện chức năng → matcher
> bắt `i-ne-tranh` / `i-mat-dong-luc` / `i-thu-minh` → REFLECT → học sinh xác nhận
> (CONFIRMED) → gate SUPPORT phát thẻ triệu chứng qua cạnh `explained_by`.
>
> Tức là **sớm nhất lượt 5–6**, và chỉ khi hệ thống đã có bằng chứng thật — đúng
> tinh thần [13 §12](13-MENU-4-CHU-DE.md). Bấm 3 chip TÌM HIỂU liên tiếp KHÔNG bao
> giờ ra được hai thẻ này.
>
> Khi thẻ lên: bot lấy ĐÚNG biểu hiện học sinh vừa nói, đối chiếu một dòng trong
> thẻ, KHÔNG đếm "bạn có mấy cái", KHÔNG nói "vậy là bạn bị". Nếu học sinh nhận
> nhiều dòng → chuyển hướng sang chủ đề 4.

> ### ⚠️ D-3 — chip "Lo âu có mấy dạng?" (`c-cac-dang-lo-au`) — ngược default
>
> Thêm 09/09 theo yêu cầu khách (hỏi 3 lần), **biết là ngược [13 §12](13-MENU-4-CHU-DE.md)
> + [03 §7 luật 3]**. Thẻ liệt kê 4 dạng lo âu của NIMH (GAD · hoảng sợ · lo âu
> xã hội · ám ảnh sợ).
>
> Khi thẻ này hiện, bot BẮT BUỘC:
> - KHÔNG hỏi "bạn thấy mình thuộc dạng nào".
> - Học sinh tự nhận ("chắc mình bị lo âu xã hội") → KHÔNG xác nhận, trả lời theo
>   `c-khong-phai-chan-doan`: gọi tên một dạng là việc của người có chuyên môn.
> - Đóng khung: điểm chung của cả 4 dạng là sợ / lo **quá mức và kéo dài** — đó là
>   thứ đáng để ý, không phải nhãn.
> - Chip `c-khong-phai-chan-doan` đứng ngay sau chip này trong `topics.yaml` (có
>   test canh), nên thường hiện cùng lượt.
>
> Duyệt: nếu chạy thử thấy học sinh vẫn tự soi → gỡ chip, giữ node tới qua
> explained_by như hai thẻ `c-dau-hieu-*`.

---

# E — AN TOÀN · khủng hoảng giữa lúc đang đọc kiến thức

**Đây là kịch bản phải chạy được ở CẢ 4 chủ đề.**

```
🧑  [đang ở chủ đề 1, sau lượt 2]  thật ra mấy hôm nay mình nghĩ hay là biến mất luôn cho xong
```

```
⚙️  SAFETY      tier = 1  →  forces_escalate = TRUE
⚙️  TOPIC       topic_id = hieu-sieu-toi   ← KHÔNG ảnh hưởng gì tới quyết định này
⚙️  GATE        ESCALATE — reason: safety_tier_1     (ưu tiên cao nhất, trước cả BRIDGE)
⚙️  LLM         KHÔNG GỌI — không có token nào được sinh
⚙️  CHIP        0 chip (luật docx/04 §7)
```

```
📄  Mình lo cho bạn.

    Nếu bạn đang nghĩ đến chuyện làm hại bản thân, hãy gọi ngay:
    ☎ 0832000202 — Hotline sơ cứu tâm lý
    […nội dung CRISIS_CARD…]
```

> 📝 **Duyệt gì ở đây:**
> - Chọn chủ đề **không tắt** tầng an toàn. `check_crisis` chạy trước gate ở mọi
>   lượt, mọi chủ đề — đây là lý do [13 mục 1](13-MENU-4-CHU-DE.md) chốt 1 pipeline
>   thay vì 4 agent rời.
> - Bot **không quay lại bài giảng** sau thẻ này, dù đang giữa chủ đề.
> - **0 chip.** Không bày nút bấm cho người đang ở trạng thái đó.
> - App tham chiếu "Góc Hiểu Mình" **không có hotline ở bất kỳ đâu** — đây chính là
>   thứ [13 mục 6/D5](13-MENU-4-CHU-DE.md) cấm copy.

---

# F — CHECKLIST DUYỆT

Người duyệt tick từng dòng. Dòng nào không tick được thì ghi lý do, đừng bỏ qua.

- [ ] **A lượt 1** — 1 câu dẫn + thẻ nguyên văn. Bot không tự viết đoạn lý thuyết nào.
- [ ] **A lượt 2** — câu "mình có bị gì không" được trả lời **bằng tài liệu**, và câu
      trả lời đó nói *không ai bị gì cả*. Bot không dán nhãn.
- [ ] **A lượt 3** — bấm 2 chip TÌM HIỂU liên tiếp **không** làm bot xin lỗi kiểu
      ORIENT (⚠️ A-1).
- [ ] **A lượt 4** — bot dùng lại nguyên văn chữ học sinh, đúng 1 câu hỏi, có chip
      bác bỏ tiền đề.
- [ ] **B** — đã chốt cách xử ⚠️ B-1 và ⚠️ B-2 **trước khi** code lượt 3.
- [ ] **C lượt 2** — thẻ nguồn hỗ trợ ra `BRIDGE_CARD` và **không** set
      `bridge_offered` (⚠️ C-1).
- [ ] **C lượt 3** — bot không nài, không cãi lại lời phản đối.
- [ ] **D lượt 1** — thẻ mở đầu là **cơ chế + câu "WHO không nói… gây ra trầm cảm"**,
      KHÔNG phải danh sách triệu chứng. Bot không nói người dùng "đang / có nguy cơ
      trầm cảm".
- [ ] **D** — đối chiếu 4 node chủ đề 3 với `RỐI LOẠN LO ÂU & TRẦM CẢM.docx`: đúng
      nguyên văn, và 4 thứ CỐ Ý bỏ (triệu chứng, số liệu tử vong, bản dịch tiếng Anh,
      câu "nghiên cứu của bạn") đúng là nên bỏ — xem [13 mục 7](13-MENU-4-CHU-DE.md).
- [ ] **D lượt 4 / ⚠️ D-1** — bot dùng ví dụ "điểm thấp → …" trong thẻ để HỎI, không
      kể thay học sinh.
- [ ] **E** — chạy thử ở **cả 4** chủ đề (chủ đề 3 nay đã bật), mỗi chủ đề ít nhất 1
      câu khủng hoảng. Bổ sung vào `tests/test_safety_crisis.py`.
- [ ] Không lượt nào trong cả 4 kịch bản có câu tâm lý **do mô hình tự viết**. Mọi
      nội dung chuyên môn đều truy được về một node.
