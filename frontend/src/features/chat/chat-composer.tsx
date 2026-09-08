"use client";

import { useRef, useState } from "react";
import Link from "next/link";
import { ArrowUp, ClipboardList } from "lucide-react";

/**
 * Ô nhập — bỏ upload ảnh, bỏ model-picker (docx/07 §1). Disabled khi đang stream.
 *
 * Hai dáng: `hero` dùng ở màn hình chào (nằm giữa, thẻ to hơn), `docked` ghim
 * dưới đáy khi đã có hội thoại. Cả hai dùng chung một thẻ nhập để người dùng
 * không thấy hai ô khác nhau khi màn hình chuyển trạng thái.
 */
export function ChatComposer({
  onSend,
  disabled,
  variant = "docked",
  footer,
  autoFocus = false,
}: {
  onSend: (text: string) => void;
  disabled: boolean;
  variant?: "hero" | "docked";
  footer?: React.ReactNode;
  autoFocus?: boolean;
}) {
  const [value, setValue] = useState("");
  const taRef = useRef<HTMLTextAreaElement>(null);

  const submit = () => {
    const t = value.trim();
    if (!t || disabled) return;
    onSend(t);
    setValue("");
    if (taRef.current) taRef.current.style.height = "auto";
  };

  return (
    <div className={variant === "docked" ? "shrink-0 px-3 pb-3 sm:px-5 sm:pb-4" : ""}>
      <div className="mx-auto w-full max-w-2xl">
        <div className="rounded-[22px] border border-[var(--border-strong)] bg-[var(--surface)] p-2.5 shadow-[var(--shadow-card)] transition-colors focus-within:border-[var(--accent)]">
          <textarea
            ref={taRef}
            value={value}
            rows={variant === "hero" ? 2 : 1}
            disabled={disabled}
            autoFocus={autoFocus}
            placeholder="Kể cho mình nghe…"
            aria-label="Nội dung tin nhắn"
            onChange={(e) => {
              setValue(e.target.value);
              e.target.style.height = "auto";
              e.target.style.height = `${Math.min(e.target.scrollHeight, 160)}px`;
            }}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                submit();
              }
            }}
            className="max-h-[160px] w-full resize-none bg-transparent px-2.5 pt-2 pb-1 text-[15px] leading-relaxed outline-none placeholder:text-[var(--muted)] disabled:opacity-60"
          />

          <div className="flex items-end justify-between gap-2 pt-1">
            <div className="flex min-w-0 items-center gap-2">
              <Link
                href="/assessment"
                className="flex items-center gap-1.5 rounded-full border border-[var(--accent)]/35 bg-[var(--accent-soft)] px-3 py-1.5 text-[13px] font-medium text-[var(--accent-ink)] transition-colors hover:bg-[var(--accent)]/15"
              >
                <ClipboardList className="size-3.5" aria-hidden />
                Bài tự đánh giá
              </Link>
              <span className="hidden text-[11px] text-[var(--muted)] sm:inline">
                Enter để gửi · Shift+Enter xuống dòng
              </span>
            </div>

            <button
              type="button"
              onClick={submit}
              disabled={disabled || !value.trim()}
              aria-label="Gửi"
              className="grid size-10 shrink-0 place-items-center rounded-full bg-[linear-gradient(135deg,var(--accent-2),var(--accent))] text-white shadow-[0_6px_16px_-6px_rgb(124_92_255/0.9)] transition-opacity hover:opacity-90 disabled:opacity-35 disabled:shadow-none"
            >
              <ArrowUp className="size-5" />
            </button>
          </div>
        </div>

        {footer}
      </div>
    </div>
  );
}
