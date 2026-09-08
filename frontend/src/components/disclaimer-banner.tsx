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

  const text = collapsed ? (
    <>Sản phẩm demo học thuật — chưa qua thẩm định chuyên môn. Không thay thế tư vấn tâm lý.</>
  ) : (
    <>
      Sản phẩm demo học thuật — nội dung tổng hợp từ WHO/NIMH/APA, chưa qua thẩm định chuyên môn độc
      lập. Không thay thế tư vấn tâm lý.
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
