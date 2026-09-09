# 07 — FRONTEND (Next.js)

> Tuần 3. **Chiến lược: port nặng từ repo `front-end`, viết mới càng ít càng tốt.**
> Repo tham chiếu: `E:\fpt_university\Semester9\source-code\front-end`

---

## 1. Danh sách port

| Component gốc | Đường dẫn trong repo tham chiếu | Sửa gì |
|---|---|---|
| `message-list.tsx` | `apps/web-client/src/features/chat/components/` | Gần như giữ nguyên |
| `message-bubble.tsx` | cùng thư mục | Đổi bảng dispatch `messageType` |
| `chat-composer.tsx` | cùng thư mục | Bỏ upload ảnh, bỏ model-picker |
| `nudge-card.tsx` | `components/bubbles/` | **Đây là mẫu cho quick replies** — giữ nguyên cơ chế chip |
| `knowledge-card.tsx` | `components/bubbles/` | Đổi nội dung, giữ layout |
| `use-chat-session.ts` | `features/chat/` | **Đổi WebSocket → SSE** |
| `types.ts` | `features/chat/` | Giữ zod pattern, đổi schema |
| `display-message.ts` | `features/chat/` | Giữ pattern discriminated union |

### Đặc biệt: `nudge-card.tsx`

Đây là component quan trọng nhất để port — nó đã giải quyết đúng bài toán quick replies:

```tsx
// Cơ chế đã đúng, giữ nguyên:
quickReplies.map((reply) => (
  <button onClick={() => onReply?.(reply)}>{reply}</button>
))
// click chip = gửi NGUYÊN VĂN text đó như một lượt chat bình thường
```

Kèm ghi chú kỹ thuật đã có sẵn trong file (giữ lại):
> *`rounded-2xl`, not `rounded-full` — chip mang tên đầy đủ và thường xuống 2 dòng; `rounded-full` bo quá lớn sẽ cắt góc chip 2 dòng.*

---

## 2. Trang

### 2.1. `/` — ~~Trang chủ~~ → chuyển thẳng vào `/chat` (đổi 09/09/2026)

> **Trang giới thiệu đã BỎ.** `app/page.tsx` giờ chỉ còn `redirect("/chat")`.
>
> Lý do: từ khi màn chào `/chat` thành menu 4 chủ đề ([13](13-MENU-4-CHU-DE.md)),
> trang này thành một cửa thừa — bắt học sinh bấm thêm một lần nữa mới tới chỗ có
> việc để làm, trong khi câu dẫn, hotline và disclaimer đều đã có sẵn ở màn chào chat.
>
> **Không mất gì về an toàn:** dòng hotline `0832000202` nằm cuối `chat-welcome.tsx`
> và `DisclaimerBanner` gắn ngay dưới ô nhập → cả hai vẫn hiện ở màn hình ĐẦU TIÊN
> người dùng thấy, đúng luật "hotline không giấu sau menu" bên dưới.
>
> Đăng nhập vẫn TUỲ CHỌN — `AuthGate` không đá ai về `/login` từ 08/09.
>
> Sơ đồ dưới đây giữ lại làm hồ sơ thiết kế của bản trước.

### ~~2.1b~~. Trang chủ bản cũ (đã gỡ)

```
┌──────────────────────────────────────────────┐
│  ⚠️ Công cụ tìm hiểu kiến thức — nội dung    │  ← banner thường trực
│     trích nguyên văn từ tài liệu nghiên cứu, │
│     chưa qua thẩm định chuyên môn độc lập.   │
│     Không thay thế tư vấn tâm lý.            │
├──────────────────────────────────────────────┤
│                                              │
│      Đôi khi, điều khó nhất không phải       │
│      là chuyện đã xảy ra —                   │
│      mà là cách mình nói với chính mình      │
│      sau đó.                                 │
│                                              │
│   ┌────────────────────────────────────────┐ │
│   │  Vào trò chuyện                      → │ │
│   └────────────────────────────────────────┘ │
│                                              │
│   Nếu bạn đang trong tình trạng khẩn cấp:    │
│   ☎ Hotline sơ cứu tâm lý 0832000202        │  ← LUÔN hiện, không ẩn
└──────────────────────────────────────────────┘
```

> **Luật:** hotline hiện ngay trang chủ, không giấu sau menu. Người cần nhất không có sức đi tìm.

> **Sửa 09/09/2026 — trang chủ còn MỘT lối vào.** Thẻ *"Thử bài tự đánh giá"* đã gỡ:
> bài Likert dời vào **chủ đề 2** ở màn chào chat, vì cả 10 câu đều mang `source_doc`
> của `NHẬN DIỆN TRONG ĐỜI SỐNG HỌC SINH.docx` — nó vốn thuộc chủ đề đó. Xem
> [13 mục 5.7](13-MENU-4-CHU-DE.md).

### 2.2. `/assessment` — Bài tự đánh giá

- 10 câu, radio 5 mức, **hiện từng câu một** hoặc cuộn dọc (chọn cuộn dọc cho nhanh)
- Có nút "Bỏ qua, vào chat luôn" ở mọi thời điểm
- Disclaimer hiện **trước khi làm**, không phải sau

**Màn hình kết quả:**

```
┌──────────────────────────────────────────────┐
│  Điểm trung bình: 3,4                        │
│  ▓▓▓▓▓▓▓░░░  Mức đáng chú ý                 │
│                                              │
│  <nguyên văn đoạn diễn giải của band này>    │
│                                              │
│  ⚠️ Bài đánh giá này giúp bạn nhận diện,     │
│     KHÔNG phải công cụ chẩn đoán tâm lý.     │
│                                              │
│   ┌──────────────────────────────────────┐   │
│   │  Nói chuyện về kết quả này  →        │   │  ← LUÔN có
│   └──────────────────────────────────────┘   │
└──────────────────────────────────────────────┘
```

> ⚠️ **Không bao giờ để màn hình kết quả là điểm dừng.** Đặc biệt với band `CAO` — nhận "Mức cao" rồi bị bỏ lại một mình là điều tệ nhất sản phẩm này có thể làm.

### 2.3. `/chat` — Giao diện chat

Layout chuẩn: list cuộn + composer dưới + banner trên. ~~Không sidebar~~ → **có
sidebar lịch sử phiên** (`session-sidebar.tsx`, đã làm ở tuần 3).

#### 2.3b. Màn chào — MENU 4 CHỦ ĐỀ (đổi 09/09/2026)

Thay 3 thẻ gợi ý cảm xúc cũ. Xem [13](13-MENU-4-CHU-DE.md) và
[14](14-KICH-BAN-4-CHU-DE.md).

```
┌──────────────────────────────────────────────┐
│  Chào bạn. Hãy chọn một chủ đề để bắt đầu    │
│  tìm hiểu về cái siêu tôi và đời sống        │
│  tinh thần.                                  │
│                                              │
│  ┌────────────────────┐ ┌──────────────────┐ │
│  │ Hiểu về cái        │ │ Nhận diện trong  │ │
│  │ siêu tôi           │ │ đời sống học sinh│ │
│  └────────────────────┘ └──────────────────┘ │
│  ┌────────────────────┐ ┌──────────────────┐ │
│  │ Ảnh hưởng đến sức  │ │ Khi nào nên tìm  │ │
│  │ khoẻ tinh thần ⚠️  │ │ hỗ trợ           │ │
│  └────────────────────┘ └──────────────────┘ │
│                                              │
│  ┌────────────────────────────────────────┐  │
│  │ …hoặc kể luôn chuyện của bạn        ↑ │  │  ← Ô NHẬP, KHÔNG ĐƯỢC BỎ
│  └────────────────────────────────────────┘  │
│  ⚠️ Công cụ tìm hiểu kiến thức — không thay  │
│     thế tư vấn tâm lý.                       │
│                                              │
│  Cần giúp ngay bây giờ?                      │
│  ☎ Gọi hotline sơ cứu tâm lý 0832000202     │  ← LUÔN hiện
└──────────────────────────────────────────────┘
```

Thẻ nạp từ `GET /api/topics` (chỉ chủ đề `enabled`). Câu chữ 4 thẻ + subtitle nằm
trong `backend/data/topics.yaml`, **không hardcode ở frontend**.

> ⚠️ **Ba thứ không được bỏ khi dựng lại màn này.** App tham chiếu "Góc Hiểu Mình"
> thiếu cả ba — copy layout của nó mà không chừa chỗ là mất luôn:
>
> | | Vì sao |
> |---|---|
> | **Ô nhập tự do** | Luồng của khách là *lý thuyết → học sinh kể chuyện mình → phân tích*. Bỏ ô nhập là cắt đứt bước giữa. Học sinh đang khó khăn cũng mất đường nói. |
> | **Dòng hotline** | App tham chiếu **không có số điện thoại nào trên toàn trang**. |
> | **Banner disclaimer** | Gắn ngay dưới ô nhập (`variant="attached"`) để luôn trong khung nhìn. |
>
> ⚠️ Chủ đề 3 hiện `enabled: false` (chưa có content node) → **không hiện thẻ**, chứ
> không phải hiện rồi báo lỗi khi bấm.

---

## 3. Loại message & dispatch

```ts
type MessageType =
  | "USER"
  | "REFLECT"          // bubble thường
  | "INSIGHT_CARD"     // ⭐ điểm nhấn demo
  | "KNOWLEDGE_CARD"
  | "COPING_CARD"
  | "BRIDGE_CARD"
  | "CRISIS_CARD";     // 🔴 hardcoded
```

```tsx
// message-bubble.tsx — bảng dispatch
switch (message.messageType) {
  case "CRISIS_CARD":    return <CrisisCard {...} />;      // KHÔNG có quickReplies
  case "INSIGHT_CARD":   return <InsightCard {...} />;
  case "KNOWLEDGE_CARD": return <KnowledgeCard {...} />;
  case "COPING_CARD":    return <CopingCard {...} />;
  case "BRIDGE_CARD":    return <BridgeCard {...} />;
  default:               return <ReflectBubble {...} />;
}
```

---

## 4. Component mới

### 4.1. `InsightCard` — điểm nhấn demo

```tsx
<div className="border-l-4 border-amber-400 bg-amber-50/50 rounded-r-xl p-4">
  <div className="text-[10px] uppercase tracking-wider text-amber-700 mb-3">
    Điều mình để ý thấy
  </div>

  {lines.map((line, i) => (
    <div key={i}>
      <p className="text-sm italic">"{line}"</p>
      {i < lines.length - 1 && (
        <div className="text-amber-500 my-1 ml-2">↓</div>
      )}
    </div>
  ))}

  <p className="text-xs text-muted-foreground mt-2">… rồi lại quay về đầu</p>
  <p className="text-sm mt-3">{closing}</p>

  <div className="flex gap-2 mt-3">
    <button onClick={() => onReply("✓ Đúng vậy")}>Đúng vậy</button>
    <button onClick={() => onReply("✗ Không hẳn")}>Không hẳn</button>
  </div>
</div>
```

**Luật:**
- Mỗi dòng là **verbatim** người dùng đã nói, hiển thị trong ngoặc kép + nghiêng
- Tối đa 5 dòng
- Chỉ 2 chip: xác nhận / phủ nhận. Không chip thứ ba.

### 4.2. `CrisisCard` — 🔴 hardcoded

```tsx
// ⚠️ Nội dung đến từ backend dạng markdown TĨNH (data/crisis_card.md).
//    Component này KHÔNG được nhận nội dung do LLM sinh.
<div className="border-2 border-rose-400 bg-rose-50 rounded-xl p-5">
  <PhoneCall className="text-rose-600" />
  ...
  <a href="tel:0832000202" className="text-2xl font-bold">0832000202</a>
  ...
</div>
```

**Luật:**
- Không thu gọn được, không đóng được
- **Không có quickReplies**
- Số điện thoại là `<a href="tel:">` — bấm là gọi được trên điện thoại
- Sau khi hiện lần đầu → thêm nút "Nguồn hỗ trợ" cố định ở header suốt phiên

### 4.3. `DisclaimerBanner` — thường trực

Hai trạng thái. Hiện ở **mọi** trang, không cho tắt — thu gọn sau 5 giây.

```
đầy đủ (5 giây đầu):
⚠️ Công cụ tìm hiểu kiến thức — nội dung trích nguyên văn từ tài liệu
   nghiên cứu, chưa qua thẩm định chuyên môn độc lập.
   Không thay thế tư vấn tâm lý.

thu gọn (thường trực):
⚠️ Công cụ tìm hiểu kiến thức — không thay thế tư vấn tâm lý.
```

> **Sửa 09/09/2026 — hai thay đổi, mỗi cái một lý do khác nhau.**
>
> **1. Bỏ "nội dung tổng hợp từ WHO/NIMH/APA".** Corpus **có** trích (WHO ×8, NIMH ×10,
> APA ×2) nên câu cũ không phải bịa — nhưng gần như toàn bộ trích dẫn nằm trong
> `RỐI LOẠN LO ÂU & TRẦM CẢM.docx`, tài liệu **chưa có content node nào**. Tức là banner
> đang bảo chứng cho thứ bot chưa nói được. Nội dung bot thật sự phát ra là nguyên văn
> 5 docx của nhóm → ghi đúng như vậy: thật hơn, và là điểm mạnh của đề tài, khỏi mượn
> tên WHO.
>
> **2. Mở đầu bằng sản phẩm LÀ gì, không phải KHÔNG PHẢI gì.** Bản cũ là ba lời phủ định
> liên tiếp ("demo học thuật" / "chưa thẩm định" / "không thay thế") — học sinh 16–18 đọc
> xong kết luận cả app không đáng tin, rồi bỏ qua luôn phần đáng tin nhất là các thẻ
> nguyên văn.
>
> Câu **"chưa qua thẩm định chuyên môn độc lập" phải giữ** ở bản đầy đủ: chưa thuê chuyên
> gia là sự thật hội đồng sẽ hỏi, bỏ đi là im lặng đúng chỗ yếu nhất.

---

## 5. Luồng SSE (thay WebSocket)

```ts
// use-chat-session.ts
const res = await fetch(`${API}/api/chat/stream`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ session_id, message }),
});

const reader = res.body!.getReader();
// parse SSE: event: meta | token | card | footer | done

// meta   → tạo message rỗng với messageType tương ứng
// token  → append vào content (streaming)
// card   → set message.card
// footer → set message.quickReplies
// done   → mở khoá composer
```

**Trạng thái UI khi đang stream:** composer **disabled**, chip **disabled** (giống `disabled` prop trong `nudge-card.tsx` gốc).

---

## 6. Zod schema

```ts
// types.ts — giữ pattern của repo cũ
export const ChatMessageSchema = z.object({
  id: z.string(),
  role: z.enum(["user", "assistant"]),
  messageType: z.enum([
    "USER","REFLECT","INSIGHT_CARD","KNOWLEDGE_CARD",
    "COPING_CARD","BRIDGE_CARD","CRISIS_CARD",
  ]),
  content: z.string(),
  card: z.record(z.unknown()).nullish(),
  quickReplies: z.array(z.string()).nullish(),   // ← giống repo cũ
  createdAt: z.number(),
});
```

---

## 7. Giọng UI (microcopy)

| Chỗ | ✅ Nên | ❌ Không |
|---|---|---|
| Placeholder composer | *"Kể cho mình nghe…"* | *"Nhập tin nhắn"* |
| Đang chờ | *"…"* (3 chấm nhấp nháy) | *"AI đang suy nghĩ"* |
| Lỗi | *"Mình đang hơi chậm, bạn nhắn lại giúp mình nhé."* | *"Đã có lỗi xảy ra. Mã lỗi: 500"* |
| Nút test | *"Thử bài tự đánh giá"* | *"Làm bài kiểm tra tâm lý"* |
| Kết quả | *"Mức đáng chú ý"* | *"Bạn có nguy cơ cao"* |

---

## 8. Accessibility & thiết bị

- **Mobile-first** — học sinh dùng điện thoại là chính
- Font ≥ 15px cho nội dung chat
- Vùng chạm chip ≥ 44px
- Tương phản đạt WCAG AA (đặc biệt `CrisisCard`)
- `prefers-reduced-motion` — tắt animation streaming nếu bật

---

## 9. Checklist

- [ ] Khởi tạo Next.js + Tailwind v4 + shadcn
- [ ] Port `message-list`, `message-bubble`, `chat-composer`, `nudge-card`
- [ ] `DisclaimerBanner` thường trực
- [ ] Trang `/` — 2 lối vào + hotline hiện sẵn
- [ ] Trang `/assessment` — 10 câu + kết quả + **nút vào chat**
- [ ] Trang `/chat`
- [ ] `InsightCard` (mới)
- [ ] `CrisisCard` (mới, `tel:` link, không đóng được)
- [ ] `CopingCard`, `BridgeCard`, `KnowledgeCard`
- [ ] `use-chat-session` chuyển sang SSE
- [ ] Zod schema + discriminated union
- [ ] Test trên màn hình điện thoại thật
- [ ] Kiểm: `CrisisCard` có bao giờ nhận nội dung từ LLM không? (phải là **không**)
