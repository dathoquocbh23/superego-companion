"use client";

import { Suspense, useCallback, useEffect, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";

import { AppShell } from "@/components/app-shell";
import { createSession, getCachedSession, setActiveSession } from "@/lib/api";
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
import type { ChatMessage, Topic } from "@/lib/types";

/**
 * Câu tự gửi khi người dùng bấm "Nói chuyện về kết quả này" ở màn hình kết quả
 * bài Likert.
 *
 * Vì sao cần (bug 09/09/2026): `/assessment` không tạo message nào trong chat,
 * nên quay về `started` vẫn false và app render đúng màn hình chào với 4 thẻ —
 * người dùng vừa làm 10 câu xong thì bị ném về "cuộc trò chuyện mới", kết quả
 * biến mất. Đúng thứ docx/07 §2.2 cấm: màn hình kết quả không được là điểm dừng.
 *
 * Gửi như một lượt người dùng bình thường (đi qua bước trích, hiện thành bong
 * bóng của họ) — cùng cơ chế với chip. Bot đã biết bối cảnh qua
 * `{HAS_TAKEN_ASSESSMENT}` trong 00_CORE_PERSONA.md và qua evidence LIKERT đã
 * seed sẵn trong overlay, nên không cần nhồi điểm số vào câu này.
 */
const MO_LOI_SAU_BAI_TEST = "Mình vừa làm xong bài tự đánh giá.";

const GREETING: ChatMessage = {
  id: "greeting",
  role: "assistant",
  messageType: "REFLECT",
  content:
    "Chào bạn. Ở đây bạn có thể tìm hiểu, hoặc kể chuyện của mình — cái nào trước cũng được.",
  createdAt: 0,
};

function ChatInner() {
  // /assessment?topic=... quay về mang theo chủ đề, để đoạn chat sau bài test
  // vẫn nằm trong đúng mảng tài liệu đó (docx/13 §5.7).
  const searchParams = useSearchParams();
  const router = useRouter();
  const topicTuUrl = searchParams.get("topic");
  const tuBaiTest = searchParams.get("from") === "assessment";
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
    // Chưa có hội thoại nào nhưng ĐÃ có phiên trong sessionStorage → nhận lại
    // phiên đó thay vì mở phiên mới. Xảy ra khi người dùng vào thẳng
    // /assessment (không qua chat): ensureSession() đã mở phiên và POST
    // /api/assessment đã seed 10 node LIKERT vào overlay của phiên ĐÓ. Gọi
    // createSession() ở đây là vứt toàn bộ bài test vừa làm sang một phiên mồ
    // côi, và bot sẽ hỏi lại từ đầu như chưa có gì.
    const daCo = getCachedSession();
    if (daCo) {
      const conv = newConversation(daCo);
      setConversations((prev) => upsertConversation(prev, conv));
      setActiveId(conv.id);
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
              initialTopic={topicTuUrl}
              tuBaiTest={tuBaiTest}
              onDaMoLoi={() => router.replace("/chat")}
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
  initialTopic,
  tuBaiTest,
  onDaMoLoi,
  onMessages,
  onOpenSidebar,
  onExpandSidebar,
  sidebarCollapsed,
}: {
  conversation: Conversation;
  initialTopic: string | null;
  tuBaiTest: boolean;
  onDaMoLoi: () => void;
  onMessages: (id: string, messages: ChatMessage[]) => void;
  onOpenSidebar: () => void;
  onExpandSidebar: () => void;
  sidebarCollapsed: boolean;
}) {
  const [topic, setTopic] = useState<string | null>(initialTopic);
  const { messages, awaitingReply, crisisShown, send } = useChatSession(
    conversation.sessionId,
    conversation.messages.length ? conversation.messages : [GREETING],
    topic,
  );

  // Bấm thẻ chủ đề = gửi NGUYÊN VĂN tên thẻ như một lượt bình thường, kèm id
  // chủ đề. Cùng cơ chế với chip: người dùng thấy trước mình sắp "nói" gì.
  const pickTopic = useCallback(
    (t: Topic) => {
      setTopic(t.id);
      void send(t.title, t.id);
    },
    [send],
  );

  // Vừa làm xong bài test → mở lượt đầu hộ người dùng. Ref chặn StrictMode
  // chạy effect 2 lần, và chặn luôn việc gửi lại khi họ F5 (query đã được xoá
  // ở onDaMoLoi, nhưng ref là hàng rào thứ hai rẻ tiền).
  const daMoLoi = useRef(false);
  useEffect(() => {
    if (!tuBaiTest || daMoLoi.current) return;
    if (messages.some((m) => m.role === "user")) return;   // đã có lượt rồi thì thôi
    daMoLoi.current = true;
    void send(MO_LOI_SAU_BAI_TEST, initialTopic);
    onDaMoLoi();
  }, [tuBaiTest, messages, send, initialTopic, onDaMoLoi]);

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
            <div className="mx-auto w-full max-w-4xl">
              <MessageList messages={messages} onQuickReply={send} awaitingReply={awaitingReply} />
            </div>
          </main>
          <ChatComposer onSend={send} disabled={awaitingReply} />
        </>
      ) : (
        <ChatWelcome onPickTopic={pickTopic}>
          <ChatComposer onSend={send} disabled={awaitingReply} variant="hero" autoFocus />
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
