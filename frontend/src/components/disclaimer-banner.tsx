"use client";

import { useEffect, useState } from "react";
import { AlertTriangle } from "lucide-react";

/**
 * Banner thường trực trên MỌI trang (docx/00 §4, docx/07 §4.3).
 * Không cho tắt — chỉ thu gọn thành 1 dòng sau 5 giây.
 *
 * `variant="attached"` là dải mỏng bo tròn gắn ngay dưới ô nhập ở phòng chat:
 * ô nhập luôn nằm trong khung nhìn nên câu cảnh báo cũng luôn nhìn thấy, mà
 * không phải chiếm một dải ngang trên đầu trang.
 */
export function DisclaimerBanner({ variant = "bar" }: { variant?: "bar" | "attached" }) {
  const [collapsed, setCollapsed] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => setCollapsed(true), 5000);
    return () => clearTimeout(t);
  }, []);

  // Câu thu gọn nói sản phẩm LÀ cái gì trước, rồi mới tới giới hạn. Bản cũ là ba
  // lời phủ định liên tiếp ("demo học thuật" / "chưa thẩm định" / "không thay
  // thế") — học sinh đọc xong kết luận cả app không đáng tin, rồi bỏ qua luôn
  // phần nội dung ĐÁNG tin nhất là các thẻ nguyên văn.
  //
  // Bản cũ còn ghi "nội dung tổng hợp từ WHO/NIMH/APA". Kiểm 08/09/2026: corpus
  // CÓ trích (WHO ×8, NIMH ×10, APA ×2) nhưng gần như toàn bộ nằm trong RỐI LOẠN
  // LO ÂU & TRẦM CẢM.docx — tài liệu chưa được trích thành content node nào. Tức
  // là câu đó đang bảo chứng cho thứ bot chưa nói được. Nội dung bot thật sự phát
  // ra là nguyên văn 5 docx của nhóm, nên ghi đúng như vậy: vừa thật hơn, vừa là
  // điểm mạnh của đề tài, khỏi phải mượn tên WHO.
  const text = collapsed ? (
    <>Công cụ tìm hiểu kiến thức — không thay thế tư vấn tâm lý.</>
  ) : (
    <>
      Công cụ tìm hiểu kiến thức — nội dung trích nguyên văn từ tài liệu nghiên cứu, chưa qua thẩm
      định chuyên môn độc lập. Không thay thế tư vấn tâm lý.
    </>
  );

  if (variant === "attached") {
    return (
      <div
        role="note"
        className="mt-2 flex items-start gap-2 rounded-2xl bg-[var(--amber-bg)] px-3.5 py-2 text-[var(--amber-ink)]"
      >
        <AlertTriangle className="mt-px size-3.5 shrink-0" aria-hidden />
        <p className="text-[11px] leading-snug">{text}</p>
      </div>
    );
  }

  return (
    <div
      role="note"
      className="flex shrink-0 items-start gap-2 border-b border-[var(--amber-ink)]/15 bg-[var(--amber-bg)] px-4 py-2 text-[var(--amber-ink)]"
    >
      <AlertTriangle className="mt-0.5 size-4 shrink-0" aria-hidden />
      <p className="text-xs leading-snug">{text}</p>
    </div>
  );
}
