"use client";

import { useCallback, useRef, useState } from "react";

import { API_BASE } from "@/lib/api";
import { cardSchema, type ChatMessage, type MessageType } from "@/lib/types";

let idCounter = 0;
const makeId = () => `local-${Date.now()}-${(idCounter += 1)}`;

const MESSAGE_TYPES = new Set<MessageType>([
  "REFLECT",
  "INSIGHT_CARD",
  "KNOWLEDGE_CARD",
  "COPING_CARD",
  "BRIDGE_CARD",
  "CRISIS_CARD",
]);

function coerceType(raw: string): MessageType {
  return MESSAGE_TYPES.has(raw as MessageType) ? (raw as MessageType) : "REFLECT";
}

/**
 * Sở hữu state một phiên chat: danh sách message + gửi lượt tiếp.
 * Chuyển WebSocket → SSE (docx/07 §5). Chip = gửi NGUYÊN VĂN text như một lượt bình thường.
 */
export function useChatSession(sessionId: string, initial: ChatMessage[] = []) {
  const [messages, setMessages] = useState<ChatMessage[]>(initial);
  const [awaitingReply, setAwaitingReply] = useState(false);
  const [crisisShown, setCrisisShown] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  const send = useCallback(
    async (rawInput: string) => {
      const text = rawInput.trim();
      if (!text || awaitingReply) return;

      setMessages((prev) => [
        ...prev,
        { id: makeId(), role: "user", messageType: "USER", content: text, createdAt: Date.now() },
      ]);
      setAwaitingReply(true);

      const assistantId = makeId();
      const ac = new AbortController();
      abortRef.current = ac;

      try {
        const res = await fetch(`${API_BASE}/api/chat/stream`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ session_id: sessionId, message: text }),
          signal: ac.signal,
        });
        if (!res.ok || !res.body) throw new Error(`chat/stream ${res.status}`);

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buf = "";
        let created = false;

        const ensureBubble = (mt: MessageType) => {
          if (created) return;
          created = true;
          setMessages((prev) => [
            ...prev,
            { id: assistantId, role: "assistant", messageType: mt, content: "", createdAt: Date.now() },
          ]);
        };
        const patch = (fn: (m: ChatMessage) => ChatMessage) =>
          setMessages((prev) => prev.map((m) => (m.id === assistantId ? fn(m) : m)));

        for (;;) {
          const { done, value } = await reader.read();
          if (done) break;
          buf += decoder.decode(value, { stream: true });

          const frames = buf.split("\n\n");
          buf = frames.pop() ?? "";
          for (const frame of frames) {
            const evLine = frame.split("\n").find((l) => l.startsWith("event:"));
            const dataLine = frame.split("\n").find((l) => l.startsWith("data:"));
            if (!evLine || !dataLine) continue;
            const event = evLine.slice(6).trim();
            let data: unknown;
            try {
              data = JSON.parse(dataLine.slice(5).trim());
            } catch {
              continue;
            }

            if (event === "meta") {
              const mt = coerceType((data as { message_type: string }).message_type);
              ensureBubble(mt);
              patch((m) => ({ ...m, messageType: mt }));
            } else if (event === "token") {
              ensureBubble("REFLECT");
              const t = (data as { t: string }).t ?? "";
              patch((m) => ({ ...m, content: m.content + t }));
            } else if (event === "card") {
              const parsed = cardSchema.safeParse(data);
              if (parsed.success) {
                ensureBubble(coerceType(parsed.data.type));
                patch((m) => ({ ...m, card: parsed.data, messageType: coerceType(parsed.data.type) }));
              }
            } else if (event === "footer") {
              const f = data as { quickReplies?: string[]; crisis?: boolean };
              patch((m) => ({ ...m, quickReplies: f.quickReplies ?? [] }));
              if (f.crisis) setCrisisShown(true);
            } else if (event === "done") {
              // no-op — loop ends when the stream closes
            }
          }
        }
      } catch (err) {
        if ((err as Error).name !== "AbortError") {
          setMessages((prev) => {
            const exists = prev.some((m) => m.id === assistantId);
            const errMsg: ChatMessage = {
              id: exists ? assistantId : makeId(),
              role: "assistant",
              messageType: "REFLECT",
              content: "Mình đang hơi chậm, bạn nhắn lại giúp mình nhé.",
              createdAt: Date.now(),
            };
            return exists ? prev.map((m) => (m.id === assistantId ? errMsg : m)) : [...prev, errMsg];
          });
        }
      } finally {
        setAwaitingReply(false);
        abortRef.current = null;
      }
    },
    [awaitingReply, sessionId],
  );

  return { messages, awaitingReply, crisisShown, send };
}
