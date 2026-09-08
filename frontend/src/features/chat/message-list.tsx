"use client";

import { useEffect, useRef } from "react";

import type { ChatMessage } from "@/lib/types";
import { MessageBubble } from "./message-bubble";

export function MessageList({
  messages,
  onQuickReply,
  awaitingReply,
}: {
  messages: ChatMessage[];
  onQuickReply: (t: string) => void;
  awaitingReply: boolean;
}) {
  const endRef = useRef<HTMLDivElement>(null);
  const lastAssistantIdx = findLastAssistant(messages);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages]);

  return (
    <div className="flex flex-col gap-4 px-4 py-5 sm:px-2">
      {messages.map((m, i) => (
        <MessageBubble
          key={m.id}
          message={m}
          onQuickReply={onQuickReply}
          // chip chỉ bấm được ở lượt assistant CUỐI CÙNG và khi không đang stream
          disabled={awaitingReply || (m.role === "assistant" && i !== lastAssistantIdx)}
        />
      ))}
      <div ref={endRef} />
    </div>
  );
}

function findLastAssistant(messages: ChatMessage[]): number {
  for (let i = messages.length - 1; i >= 0; i -= 1) {
    if (messages[i].role === "assistant") return i;
  }
  return -1;
}
