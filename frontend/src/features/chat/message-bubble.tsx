import type { ChatMessage } from "@/lib/types";
import { BridgeCard } from "./bubbles/bridge-card";
import { CopingCard } from "./bubbles/coping-card";
import { CrisisCard } from "./bubbles/crisis-card";
import { InsightCard } from "./bubbles/insight-card";
import { ReflectBubble } from "./bubbles/reflect-bubble";

/**
 * Bảng dispatch theo messageType (docx/07 §3).
 * Chip từ lượt cũ (không phải lượt cuối) render disabled.
 */
export function MessageBubble({
  message,
  onQuickReply,
  disabled,
}: {
  message: ChatMessage;
  onQuickReply: (t: string) => void;
  disabled: boolean;
}) {
  if (message.role === "user") {
    return (
      <div className="ml-auto max-w-[80%] rounded-[20px_8px_20px_20px] bg-[linear-gradient(135deg,var(--accent-2),var(--accent))] px-4 py-2.5 text-[15px] leading-relaxed text-white shadow-[0_8px_20px_-12px_rgb(124_92_255/0.9)]">
        {message.content}
      </div>
    );
  }

  switch (message.messageType) {
    case "CRISIS_CARD":
      return message.card ? <CrisisCard card={message.card} /> : null;
    case "INSIGHT_CARD":
      return message.card ? (
        <InsightCard card={message.card} onReply={onQuickReply} disabled={disabled} />
      ) : (
        <ReflectBubble message={message} onReply={onQuickReply} disabled={disabled} />
      );
    case "COPING_CARD":
      return message.card ? (
        <CopingCard card={message.card} message={message} onReply={onQuickReply} disabled={disabled} />
      ) : (
        <ReflectBubble message={message} onReply={onQuickReply} disabled={disabled} />
      );
    case "KNOWLEDGE_CARD":
      return message.card ? (
        <CopingCard
          card={message.card}
          message={message}
          onReply={onQuickReply}
          disabled={disabled}
          variant="knowledge"
        />
      ) : (
        <ReflectBubble message={message} onReply={onQuickReply} disabled={disabled} />
      );
    case "BRIDGE_CARD":
      return message.card ? (
        <BridgeCard card={message.card} message={message} onReply={onQuickReply} disabled={disabled} />
      ) : (
        <ReflectBubble message={message} onReply={onQuickReply} disabled={disabled} />
      );
    default:
      return <ReflectBubble message={message} onReply={onQuickReply} disabled={disabled} />;
  }
}
