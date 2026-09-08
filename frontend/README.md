# Frontend — Chatbot đồng hành "Cái siêu tôi trừng phạt"

**Tuần 3** theo `../docx/07-FRONTEND.md`. Next.js 16 (App Router) · React 19 · TypeScript · Tailwind v4.

Ứng dụng **độc lập** — port *pattern* từ repo tham chiếu (`front-end/apps/web-client`)
chứ không copy file phụ thuộc `@repo/*`.

## Chạy

```bash
cd frontend
npm install
cp .env.local.example .env.local     # NEXT_PUBLIC_API_BASE=http://localhost:8000
npm run dev                          # http://localhost:3000
```

Cần backend chạy song song (xem `../backend/README.md`). Backend ở chế độ
`LLM_OFFLINE=true` là đủ để thử toàn bộ luồng.

## Trang (docx/07 §2)

| Route | Nội dung |
|---|---|
| `/` | 2 lối vào (Trò chuyện ngay · Thử bài tự đánh giá) + hotline hiện sẵn |
| `/assessment` | 10 câu Likert (cuộn dọc, nút "Bỏ qua vào chat" mọi lúc), disclaimer TRƯỚC khi làm, màn kết quả **luôn có nút vào chat** |
| `/chat` | List cuộn + composer + banner. Không sidebar (không lịch sử phiên) |

## Cơ chế (docx/07 §3–§5)

- **SSE thay WebSocket** — `use-chat-session.ts` đọc `fetch().body.getReader()`, tách
  frame theo `\n\n`, xử lý `meta` / `token` / `card` / `footer` / `done`. Token gộp vào
  bubble assistant đang mở; `card` gắn payload; `footer` set `quickReplies`.
- **Chip** (`quick-replies.tsx`, port `nudge-card.tsx`) — click = gửi **nguyên văn** text
  như một lượt bình thường. `rounded-2xl` (không `rounded-full`), vùng chạm ≥ 44px.
- **Composer disabled** khi đang stream (`awaitingReply`).
- **Dispatch theo `messageType`** (`message-bubble.tsx`): CRISIS_CARD · INSIGHT_CARD ·
  KNOWLEDGE_CARD · COPING_CARD · BRIDGE_CARD · REFLECT (mặc định).

## Component mới (docx/07 §4)

| Component | Ghi chú |
|---|---|
| `DisclaimerBanner` | Mọi trang, không tắt được, thu gọn sau 5s |
| `InsightCard` | ⭐ điểm nhấn — mỗi dòng là verbatim (nghiêng, ngoặc kép), tối đa 5, đúng 2 chip |
| `CrisisCard` | 🔴 hardcoded · `tel:` link · không đóng được · **không quick replies** · chỉ nhận markdown TĨNH từ backend |
| `ChatHeader` | Sau CRISIS_CARD hiện lần đầu → giữ nút "Nguồn hỗ trợ" suốt phiên |
| `CopingCard` / `BridgeCard` | `lead` do LLM viết; phần thân là nguyên văn tài liệu + ghi nguồn |

## Kiểm tra nhanh

```bash
npm run build      # ✓ compile + typecheck, 4 route
```

## Chưa làm

- shadcn/ui (dùng Tailwind thuần cho gọn, không kéo monorepo UI kit).
- Test component (Vitest) — chưa; luồng đã kiểm bằng build + smoke SSE với backend offline.
- `next-themes` / dark mode — palette sáng cố định cho demo.
