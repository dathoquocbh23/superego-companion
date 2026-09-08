import type { Card, ChatMessage } from "@/lib/types";
import { QuickReplies } from "./quick-replies";

/**
 * COPING_CARD / KNOWLEDGE_CARD (docx/07 §3, docx/11 lượt 4).
 * `lead` là 1 câu dẫn do LLM viết. Toàn bộ phần còn lại là NGUYÊN VĂN tài liệu,
 * có ghi nguồn. Đúng MỘT kỹ năng — không dump danh sách.
 */
export function CopingCard({
  card,
  message,
  onReply,
  disabled,
  variant = "coping",
}: {
  card: Card;
  message: ChatMessage;
  onReply: (t: string) => void;
  disabled: boolean;
  variant?: "coping" | "knowledge";
}) {
  return (
    <div className="max-w-[90%]">
      {card.lead && <p className="mb-2 text-[15px] leading-relaxed">{card.lead}</p>}
      <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-4">
        <div className="mb-2 text-[10px] font-semibold tracking-wider text-[var(--accent-ink)] uppercase">
          {variant === "knowledge" ? "Một điều có thể hữu ích" : "Thử một cách khác"}
        </div>
        {card.title && <p className="text-[15px] font-semibold">{card.title}</p>}
        {card.body && (
          <p className="mt-2 text-[15px] leading-relaxed whitespace-pre-wrap text-[var(--text)]">{card.body}</p>
        )}
        {card.action && (
          <p className="mt-3 rounded-lg bg-[var(--accent)]/8 px-3 py-2 text-sm">▸ {card.action}</p>
        )}
        {card.source && <p className="mt-3 text-xs text-[var(--muted)]">Nguồn: {card.source}</p>}
      </div>
      {!disabled && <QuickReplies replies={message.quickReplies ?? []} onReply={onReply} disabled={disabled} />}
    </div>
  );
}
