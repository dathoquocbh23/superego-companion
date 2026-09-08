"use client";

import { Suspense, useCallback, useEffect, useRef, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { DisclaimerBanner } from "@/components/disclaimer-banner";
import { createSession, setActiveSession } from "@/lib/api";
import {
  clearConversations,
  loadConversations,
  newConversation,
  NEW_TITLE,
  removeConversation,
  titleFrom,
  upsertConversation,
  type Conversation,
} from "@/lib/conversations";
import { exportChat } from "@/lib/export-chat";
import { ChatComposer } from "@/features/chat/chat-composer";
import { ChatHeader } from "@/features/chat/chat-header";
import { ChatWelcome } from "@/features/chat/chat-welcome";
import { MessageList } from "@/features/chat/message-list";
import { SessionSidebar } from "@/features/chat/session-sidebar";
import { useChatSession } from "@/features/chat/use-chat-session";
import type { ChatMessage } from "@/lib/types";

const GREETING: ChatMessage = {
  id: "greeting",
  role: "assistant",
  messageType: "REFLECT",
  content:
    "Chào bạn. Đây là nơi bạn có thể nói ra điều khó nói mà không bị phán xét. Có chuyện gì đang làm bạn nặng lòng không?",
  createdAt: 0,
};

function ChatInner() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [error, setError] = useState(false);
  const [busy, setBusy] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  /** Mở một phiên mới trên backend + đưa vào đầu danh sách. */
  const startNew = useCallback(async () => {
    setBusy(true);
    try {
      const sessionId = await createSession();
      const conv = newConversation(sessionId);
      setConversations((prev) => upsertConversation(prev, conv));
      setActiveId(conv.id);
      setDrawerOpen(false);
    } catch {
      setError(true);
    } finally {
      setBusy(false);
    }
  }, []);

  // Khởi động: nạp lịch sử local; chưa có gì → mở phiên đầu tiên.
  // Ref chặn StrictMode chạy effect 2 lần → tránh tạo 2 phiên rỗng ở dev.
  const booted = useRef(false);
  useEffect(() => {
    if (booted.current) return;
    booted.current = true;
    const list = loadConversations();
    if (list.length) {
      setConversations(list);
      setActiveId(list[0].id);
      setActiveSession(list[0].sessionId);
      return;
    }
    void startNew();
  }, [startNew]);

  const handleSelect = useCallback(
    (id: string) => {
      const conv = conversations.find((c) => c.id === id);
      if (!conv) return;
      setActiveId(id);
      setActiveSession(conv.sessionId);
      setDrawerOpen(false);
    },
    [conversations],
  );

  const handleDelete = useCallback(
    (id: string) => {
      const next = removeConversation(conversations, id);
      setConversations(next);
      if (id !== activeId) return;
      if (next.length) {
        setActiveId(next[0].id);
        setActiveSession(next[0].sessionId);
      } else {
        setActiveId(null);
        void startNew();
      }
    },
    [activeId, conversations, startNew],
  );

  const handleClearAll = useCallback(() => {
    clearConversations();
    setConversations([]);
    setActiveId(null);
    void startNew();
  }, [startNew]);

  /** Ghi lại transcript sau mỗi lượt (gọi khi stream đã kết thúc). */
  const handleMessages = useCallback(
    (id: string, messages: ChatMessage[]) => {
      setConversations((prev) => {
        const current = prev.find((c) => c.id === id);
        if (!current) return prev;
        const title = current.title === NEW_TITLE ? titleFrom(messages) : current.title;
        const unchanged = current.messages.length === messages.length && current.title === title;
        if (unchanged) return prev;
        return upsertConversation(prev, { ...current, title, messages, updatedAt: Date.now() });
      });
    },
    [],
  );

  if (error) {
    return (
      <AppShell>
        <div className="grid flex-1 place-items-center p-6 text-center">
          <p className="max-w-sm text-sm leading-relaxed text-[var(--muted)]">
            Không kết nối được máy chủ. Kiểm tra backend đang chạy ở{" "}
            {process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000"}.
          </p>
        </div>
      </AppShell>
    );
  }

  const active = conversations.find((c) => c.id === activeId) ?? null;

  return (
    <AppShell>
      <div className="flex min-h-0 flex-1">
        <SessionSidebar
          conversations={conversations}
          activeId={activeId}
          onSelect={handleSelect}
          onNew={startNew}
          onDelete={handleDelete}
          onClearAll={handleClearAll}
          open={drawerOpen}
          onClose={() => setDrawerOpen(false)}
          busy={busy}
          collapsed={sidebarCollapsed}
          onToggleCollapse={() => setSidebarCollapsed(true)}
        />

        <div className="flex min-w-0 flex-1 flex-col">
          {active ? (
            <ChatBody
              key={active.id}
              conversation={active}
              onMessages={handleMessages}
              onOpenSidebar={() => setDrawerOpen(true)}
              onExpandSidebar={() => setSidebarCollapsed(false)}
              sidebarCollapsed={sidebarCollapsed}
            />
          ) : (
            <p className="p-6 text-sm text-[var(--muted)]">Đang mở phiên…</p>
          )}
        </div>
      </div>
    </AppShell>
  );
}

function ChatBody({
  conversation,
  onMessages,
  onOpenSidebar,
  onExpandSidebar,
  sidebarCollapsed,
}: {
  conversation: Conversation;
  onMessages: (id: string, messages: ChatMessage[]) => void;
  onOpenSidebar: () => void;
  onExpandSidebar: () => void;
  sidebarCollapsed: boolean;
}) {
  const { messages, awaitingReply, crisisShown, send } = useChatSession(
    conversation.sessionId,
    conversation.messages.length ? conversation.messages : [GREETING],
  );

  // Chỉ ghi khi stream đã xong — tránh ghi localStorage mỗi token.
  useEffect(() => {
    if (awaitingReply) return;
    onMessages(conversation.id, messages);
  }, [awaitingReply, messages, conversation.id, onMessages]);

  // Chưa có lượt nào của người dùng → màn hình chào, ô nhập nằm giữa.
  const started = messages.some((m) => m.role === "user");

  return (
    <>
      <ChatHeader
        showSupport={crisisShown}
        onOpenSidebar={onOpenSidebar}
        onExpandSidebar={onExpandSidebar}
        sidebarCollapsed={sidebarCollapsed}
        onExport={() => exportChat(conversation.title, messages)}
        canExport={started}
      />

      {started ? (
        <>
          <main className="scroll-thin min-h-0 flex-1 overflow-y-auto">
            <div className="mx-auto w-full max-w-2xl">
              <MessageList messages={messages} onQuickReply={send} awaitingReply={awaitingReply} />
            </div>
          </main>
          <ChatComposer
            onSend={send}
            disabled={awaitingReply}
            footer={<DisclaimerBanner variant="attached" />}
          />
        </>
      ) : (
        <ChatWelcome onPick={send}>
          <ChatComposer
            onSend={send}
            disabled={awaitingReply}
            variant="hero"
            autoFocus
            footer={<DisclaimerBanner variant="attached" />}
          />
        </ChatWelcome>
      )}
    </>
  );
}

export default function ChatPage() {
  return (
    <Suspense fallback={<p className="p-6 text-sm text-[var(--muted)]">Đang tải…</p>}>
      <ChatInner />
    </Suspense>
  );
}
