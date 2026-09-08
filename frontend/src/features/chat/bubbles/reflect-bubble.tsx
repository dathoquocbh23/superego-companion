import type { ChatMessage } from "@/lib/types";
import { QuickReplies } from "./quick-replies";

/** Bubble thường — gate CLARIFY / REFLECT (chế độ đơn) / REFUSAL. */
export function ReflectBubble({
  message,
  onReply,
  disabled,
}: {
  message: ChatMessage;
  onReply: (t: string) => void;
  disabled: boolean;
}) {
  return (
    <div className="max-w-[85%]">
      <div className="rounded-[8px_20px_20px_20px] border border-[var(--border)] bg-[var(--surface-2)] px-4 py-3 text-[15px] leading-relaxed whitespace-pre-wrap">
        {message.content || <TypingDots />}
      </div>
      {!disabled && <QuickReplies replies={message.quickReplies ?? []} onReply={onReply} disabled={disabled} />}
      {disabled && (message.quickReplies?.length ?? 0) > 0 && (
        <QuickReplies replies={message.quickReplies ?? []} onReply={onReply} disabled />
      )}
    </div>
  );
}

export function TypingDots() {
  return (
    <span className="dot-typing inline-flex gap-1 text-[var(--muted)]" aria-label="Đang trả lời">
      <span>•</span>
      <span>•</span>
      <span>•</span>
    </span>
  );
}
