"use client";

import type { Card } from "@/lib/types";

/**
 * ⭐ Điểm nhấn demo (docx/07 §4.1).
 * Mỗi dòng là verbatim người dùng đã nói — hiển thị trong ngoặc kép + nghiêng.
 * Tối đa 5 dòng. Chỉ 2 chip: xác nhận / phủ nhận. Không chip thứ ba.
 */
export function InsightCard({
  card,
  onReply,
  disabled,
}: {
  card: Card;
  onReply: (t: string) => void;
  disabled: boolean;
}) {
  const lines = (card.lines ?? []).slice(0, 5);
  return (
    <div className="max-w-[90%] rounded-r-xl border-l-4 border-[var(--amber)] bg-[var(--amber-bg)] p-4">
      <div className="mb-3 text-[10px] font-semibold tracking-wider text-[var(--amber-ink)] uppercase">
        Điều mình để ý thấy
      </div>

      {lines.map((line, i) => (
        <div key={i}>
          <p className="text-[15px] italic">&ldquo;{line}&rdquo;</p>
          {i < lines.length - 1 && <div className="my-1 ml-2 text-[var(--amber)]">↓</div>}
        </div>
      ))}

      <p className="mt-2 text-xs text-[var(--muted)]">… rồi lại quay về đầu</p>
      {card.closing && <p className="mt-3 text-[15px]">{card.closing}</p>}

      <div className="mt-3 flex gap-1.5">
        <button
          type="button"
          disabled={disabled}
          onClick={() => onReply("✓ Đúng vậy")}
          className="min-h-[34px] rounded-xl border border-[var(--amber-ink)]/40 px-3 py-1.5 text-[13px] leading-snug text-[var(--amber-ink)] transition-colors hover:bg-[var(--amber)]/10 disabled:opacity-50"
        >
          Đúng vậy
        </button>
        <button
          type="button"
          disabled={disabled}
          onClick={() => onReply("✗ Không hẳn")}
          className="min-h-[34px] rounded-xl border border-[var(--border)] px-3 py-1.5 text-[13px] leading-snug transition-colors hover:bg-black/5 disabled:opacity-50"
        >
          Không hẳn
        </button>
      </div>
    </div>
  );
}
