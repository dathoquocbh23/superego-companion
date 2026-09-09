import Link from "next/link";

/**
 * Khung ngoài: ứng dụng chiếm TRỌN màn hình (không còn tấm thẻ bo tròn nổi trên
 * nền tím). Bỏ padding / max-width / bo góc / đổ bóng.
 */
export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-[100dvh] w-full flex-col overflow-hidden bg-[var(--shell)]">
      {children}
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

/**
 * Logo: ô bo tròn dải tím với dấu cộng — lặp lại ở sidebar, header, trang chủ.
 *
 * Truyền `onClick` thì logo thành nút bấm được (dùng để ping đánh thức backend);
 * không truyền thì vẫn là hình trang trí thuần, `aria-hidden` như cũ.
 */
export function BrandMark({
  className = "size-8",
  onClick,
  title,
}: {
  className?: string;
  onClick?: () => void;
  title?: string;
}) {
  const box = `grid shrink-0 place-items-center rounded-[10px] bg-[linear-gradient(135deg,var(--accent-2),var(--accent))] text-white shadow-[0_4px_12px_-4px_rgb(124_92_255/0.7)] ${className}`;
  const glyph = (
    <svg viewBox="0 0 24 24" fill="none" className="size-[55%]" strokeWidth={2.4} stroke="currentColor">
      <path d="M12 6v12M6 12h12" strokeLinecap="round" />
    </svg>
  );

  if (onClick) {
    return (
      <button
        type="button"
        onClick={onClick}
        title={title}
        aria-label={title ?? "Đánh thức máy chủ"}
        className={`${box} cursor-pointer transition-transform hover:scale-105 active:scale-95`}
      >
        {glyph}
      </button>
    );
  }

  return (
    <span aria-hidden className={box}>
      {glyph}
    </span>
  );
}
