import type { ChatMessage } from "./types";

/**
 * Lịch sử hội thoại — lưu LOCAL trên máy người dùng (localStorage), không gửi
 * lên server. Backend chỉ giữ `overlay` theo session_id với TTL 24h
 * (app/overlay/store.py), không lưu transcript. Vì vậy sidebar phải tự giữ
 * message; mở lại một phiên cũ đã hết TTL vẫn chạy được — bot chỉ mất trạng
 * thái graph và bắt đầu lại từ CLARIFY.
 *
 * Lưu ý riêng tư: máy dùng chung sẽ thấy được lịch sử này → sidebar luôn có
 * nút xoá từng phiên và xoá tất cả.
 */

const KEY = "nckh_conversations_v1";
const MAX_CONVERSATIONS = 30;

export type Conversation = {
  id: string;
  sessionId: string;
  title: string;
  createdAt: number;
  updatedAt: number;
  messages: ChatMessage[];
};

export const NEW_TITLE = "Cuộc trò chuyện mới";

function makeLocalId(): string {
  return `c-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
}

/** Tiêu đề = câu đầu tiên người dùng gõ, cắt 42 ký tự. */
export function titleFrom(messages: ChatMessage[]): string {
  const first = messages.find((m) => m.role === "user" && m.content.trim());
  if (!first) return NEW_TITLE;
  const t = first.content.trim().replace(/\s+/g, " ");
  return t.length > 42 ? `${t.slice(0, 42)}…` : t;
}

export function loadConversations(): Conversation[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(KEY);
    if (!raw) return [];
    const parsed: unknown = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return (parsed as Conversation[])
      .filter((c) => c && typeof c.id === "string" && typeof c.sessionId === "string")
      .map((c) => ({ ...c, messages: Array.isArray(c.messages) ? c.messages : [] }))
      .sort((a, b) => b.updatedAt - a.updatedAt);
  } catch {
    return [];
  }
}

function persist(list: Conversation[]): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(KEY, JSON.stringify(list.slice(0, MAX_CONVERSATIONS)));
  } catch {
    // hết quota / chế độ ẩn danh — bỏ qua, phiên hiện tại vẫn chạy bình thường
  }
}

export function newConversation(sessionId: string): Conversation {
  const now = Date.now();
  return { id: makeLocalId(), sessionId, title: NEW_TITLE, createdAt: now, updatedAt: now, messages: [] };
}

/** Thêm mới hoặc ghi đè một phiên; trả về danh sách đã sắp xếp lại. */
export function upsertConversation(list: Conversation[], conv: Conversation): Conversation[] {
  const next = [conv, ...list.filter((c) => c.id !== conv.id)].sort((a, b) => b.updatedAt - a.updatedAt);
  persist(next);
  return next;
}

export function removeConversation(list: Conversation[], id: string): Conversation[] {
  const next = list.filter((c) => c.id !== id);
  persist(next);
  return next;
}

export function clearConversations(): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.removeItem(KEY);
  } catch {
    // bỏ qua
  }
}

/** "Hôm nay 14:32" / "12/09" — nhãn ngắn cho sidebar. */
export function shortWhen(ts: number): string {
  const d = new Date(ts);
  const today = new Date();
  const sameDay =
    d.getDate() === today.getDate() && d.getMonth() === today.getMonth() && d.getFullYear() === today.getFullYear();
  if (sameDay) return `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
  return `${String(d.getDate()).padStart(2, "0")}/${String(d.getMonth() + 1).padStart(2, "0")}`;
}

/**
 * Gom phiên theo mốc thời gian cho sidebar: Hôm nay / Hôm qua / 7 ngày / Cũ hơn.
 * Danh sách vào đã sắp giảm dần theo `updatedAt` nên chỉ cần duyệt một lượt.
 */
export function groupConversations(list: Conversation[]): { label: string; items: Conversation[] }[] {
  const startOfToday = new Date();
  startOfToday.setHours(0, 0, 0, 0);
  const today = startOfToday.getTime();
  const yesterday = today - 86_400_000;
  const week = today - 6 * 86_400_000;

  const buckets: { label: string; items: Conversation[] }[] = [
    { label: "Hôm nay", items: [] },
    { label: "Hôm qua", items: [] },
    { label: "7 ngày qua", items: [] },
    { label: "Cũ hơn", items: [] },
  ];

  for (const c of list) {
    const i = c.updatedAt >= today ? 0 : c.updatedAt >= yesterday ? 1 : c.updatedAt >= week ? 2 : 3;
    buckets[i].items.push(c);
  }

  return buckets.filter((b) => b.items.length > 0);
}
