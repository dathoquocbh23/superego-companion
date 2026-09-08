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

### 2.1. `/` — Trang chủ, hai lối vào

```
┌──────────────────────────────────────────────┐
│  ⚠️ Sản phẩm demo học thuật — chưa qua thẩm  │  ← banner thường trực
│     định chuyên môn. Không thay thế tư vấn.  │
├──────────────────────────────────────────────┤
│                                              │
│      Đôi khi, điều khó nhất không phải       │
│      là chuyện đã xảy ra —                   │
│      mà là cách mình nói với chính mình      │
│      sau đó.                                 │
│                                              │
│   ┌────────────────────┐  ┌────────────────┐ │
│   │  Trò chuyện ngay   │  │ Thử bài tự     │ │
│   │                    │  │ đánh giá (2')  │ │
│   └────────────────────┘  └────────────────┘ │
│                                              │
│   Nếu bạn đang trong tình trạng khẩn cấp:    │
│   ☎ Hotline sơ cứu tâm lý 0832000202        │  ← LUÔN hiện, không ẩn
└──────────────────────────────────────────────┘
```

> **Luật:** hotline hiện ngay trang chủ, không giấu sau menu. Người cần nhất không có sức đi tìm.

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

Layout chuẩn: list cuộn + composer dưới + banner trên. Không sidebar (không có lịch sử phiên).

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

```
⚠️ Sản phẩm demo học thuật — nội dung tổng hợp từ WHO/NIMH/APA,
   chưa qua thẩm định chuyên môn độc lập. Không thay thế tư vấn tâm lý.
```

Hiện ở **mọi** trang. Không cho tắt (có thể thu gọn thành 1 dòng sau 5 giây).

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
