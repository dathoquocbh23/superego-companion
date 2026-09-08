"use client";

/**
 * Cơ chế chip — port từ `nudge-card.tsx` của repo tham chiếu (docx/07 §1).
 * Click chip = gửi NGUYÊN VĂN text đó như một lượt chat bình thường.
 *
 * `rounded-xl`, KHÔNG `rounded-full` — chip mang tên đầy đủ và đôi khi xuống 2
 * dòng; `rounded-full` bo quá lớn sẽ cắt góc chip 2 dòng.
 *
 * Kích thước: gọn hơn bong bóng chat để chip đọc như "gợi ý", không tranh chỗ
 * với nội dung. Vùng chạm cao 34px — dưới mức 44px khuyến nghị của WCAG 2.5.5
 * (AAA), vẫn đạt WCAG 2.5.8 (AA, ≥24px); gap 6px giữ khoảng cách chống bấm nhầm.
 */
export function QuickReplies({
  replies,
  onReply,
  disabled = false,
}: {
  replies: string[];
  onReply: (text: string) => void;
  disabled?: boolean;
}) {
  if (!replies.length) return null;
  return (
    <div className="mt-1.5 flex flex-wrap gap-1.5">
      {replies.map((reply) => (
        <button
          key={reply}
          type="button"
          disabled={disabled}
          onClick={() => onReply(reply)}
          className="min-h-[34px] max-w-full rounded-xl border border-[var(--accent)]/30 bg-[var(--accent-soft)] px-3 py-1.5 text-left text-[13px] leading-snug text-[var(--accent-ink)] transition-colors hover:border-[var(--accent)]/60 hover:bg-[var(--accent)]/15 focus-visible:outline focus-visible:outline-2 focus-visible:outline-[var(--accent)] disabled:cursor-not-allowed disabled:opacity-50"
        >
          {reply}
        </button>
      ))}
    </div>
  );
}
