import { redirect } from "next/navigation";

/**
 * "/" đi THẲNG vào phòng chat ẩn danh. Đổi 09/09/2026 (docx/07 §2.1).
 *
 * Trước đó đây là một trang giới thiệu có đúng một nút "Vào trò chuyện". Kể từ
 * khi màn chào của /chat trở thành menu 4 chủ đề (docx/13), trang này thành một
 * cửa thừa: nó bắt học sinh bấm thêm một lần nữa mới tới được chỗ có việc để
 * làm, và nội dung của nó — câu dẫn, hotline, disclaimer — đều đã có sẵn ở màn
 * chào chat.
 *
 * KHÔNG mất gì về an toàn: dòng hotline 0832000202 nằm ở cuối chat-welcome.tsx
 * và DisclaimerBanner gắn ngay dưới ô nhập, nên cả hai vẫn hiện ngay màn hình
 * đầu tiên người dùng thấy — đúng luật "hotline không giấu sau menu".
 *
 * Đăng nhập vẫn là TUỲ CHỌN: AuthGate không đá ai về /login nữa (từ 08/09), nó
 * chỉ chờ đọc session để không nháy lời chào sai.
 */
export default function HomePage() {
  redirect("/chat");
}
