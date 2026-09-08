import Link from "next/link";

/**
 * Khung ngoài: cả ứng dụng nằm trong một tấm thẻ bo tròn nổi trên nền gradient
 * tím nhạt. Trên mobile tấm thẻ chiếm trọn màn hình (bỏ viền + bo góc) để không
 * phí không gian.
 */
export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-[100dvh] w-full justify-center p-0 sm:p-4 lg:p-6">
      <div className="flex h-[100dvh] w-full max-w-[1400px] flex-col overflow-hidden bg-[var(--shell)] shadow-none sm:h-[calc(100dvh-2rem)] sm:rounded-[var(--radius-shell)] sm:shadow-[var(--shadow-shell)] lg:h-[calc(100dvh-3rem)]">
        {children}
      </div>
    </div>
  );
}

/**
 * Khung cho các trang phụ (tự đánh giá, đăng nhập, bộ nhớ): cùng tấm thẻ nhưng
 * cuộn được và có thanh tiêu đề đơn giản.
 */
export function PageShell({
  title,
  children,
  back = "/chat",
  backLabel = "Về phòng trò chuyện",
}: {
  title: string;
  children: React.ReactNode;
  back?: string;
  backLabel?: string;
}) {
  return (
    <AppShell>
      <header className="flex shrink-0 items-center justify-between gap-3 border-b border-[var(--border)] px-4 py-3 sm:px-6">
        <div className="flex items-center gap-2.5">
          <BrandMark className="size-8" />
          <span className="text-[15px] font-semibold">{title}</span>
        </div>
        <Link
          href={back}
          className="rounded-full border border-[var(--border-strong)] px-3.5 py-1.5 text-xs font-medium text-[var(--muted)] transition-colors hover:bg-[var(--surface-2)] hover:text-[var(--text)]"
        >
          {backLabel}
        </Link>
      </header>
      <div className="scroll-thin flex-1 overflow-y-auto">{children}</div>
    </AppShell>
  );
}

/** Logo: ô bo tròn dải tím với dấu cộng — lặp lại ở sidebar, header, trang chủ. */
export function BrandMark({ className = "size-8" }: { className?: string }) {
  return (
    <span
      aria-hidden
      className={`grid shrink-0 place-items-center rounded-[10px] bg-[linear-gradient(135deg,var(--accent-2),var(--accent))] text-white shadow-[0_4px_12px_-4px_rgb(124_92_255/0.7)] ${className}`}
    >
      <svg viewBox="0 0 24 24" fill="none" className="size-[55%]" strokeWidth={2.4} stroke="currentColor">
        <path d="M12 6v12M6 12h12" strokeLinecap="round" />
      </svg>
    </span>
  );
}
