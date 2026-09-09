import { z } from "zod";

import {
  assessmentResultSchema,
  assessmentSpecSchema,
  topicSchema,
  type AssessmentResult,
  type AssessmentSpec,
  type Topic,
} from "./types";
import { getAccessToken } from "./supabase";

export const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

const SESSION_KEY = "nckh_session_id";

/**
 * Đánh thức backend sớm. Render free tier cho service ngủ sau ~15 phút không có
 * request và mất ~50s để dậy lại. Gọi cái này lúc người dùng vừa mở app hoặc
 * bấm logo, để tới khi họ gửi tin nhắn đầu thì máy chủ đã sẵn sàng.
 *
 * Nuốt mọi lỗi và tự chặn gọi dồn (tối đa 1 lần / 60s): đây chỉ là cú hích cho
 * ấm máy, không phải thao tác bắt buộc — hỏng cũng không được chặn luồng chat.
 */
let lastPingAt = 0;

export function pingBackend(): void {
  if (typeof window === "undefined") return;
  const now = Date.now();
  if (now - lastPingAt < 60_000) return;
  lastPingAt = now;
  void fetch(`${API_BASE}/health`, { method: "GET", cache: "no-store" }).catch(() => {});
}

/** Phiên ẩn danh — cache trong sessionStorage để 2 lối vào dùng chung. */
export async function ensureSession(): Promise<string> {
  if (typeof window !== "undefined") {
    const cached = window.sessionStorage.getItem(SESSION_KEY);
    if (cached) return cached;
  }
  const res = await fetch(`${API_BASE}/api/session`, {
    method: "POST",
    headers: await authHeaders(),
  });
  if (!res.ok) throw new Error(`POST /api/session ${res.status}`);
  const { session_id } = (await res.json()) as { session_id: string };
  if (typeof window !== "undefined") window.sessionStorage.setItem(SESSION_KEY, session_id);
  return session_id;
}

/**
 * Gắn token Supabase nếu đã đăng nhập. Backend coi token thiếu/sai là phiên
 * ẩn danh chứ không phải lỗi (docx/12 §6), nên ở đây không cần xử lý gì thêm.
 */
async function authHeaders(): Promise<Record<string, string>> {
  const token = await getAccessToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

/**
 * Bỏ session_id đang cache. Gọi mỗi khi DANH TÍNH đổi (đăng nhập / đăng xuất /
 * vào thử ẩn danh).
 *
 * Vì sao cần: backend gắn user_id vào overlay TẠI LÚC mở phiên, đọc từ header
 * Authorization (app/api/session.py). Đổi tài khoản mà vẫn dùng lại session_id
 * cũ thì overlay giữ nguyên chủ cũ — bộ nhớ dài hạn ghi nhầm người, và từ GĐ6
 * thì transcript cũng ghi nhầm người.
 */
export function clearCachedSession(): void {
  if (typeof window === "undefined") return;
  window.sessionStorage.removeItem(SESSION_KEY);
}

export function getCachedSession(): string | null {
  if (typeof window === "undefined") return null;
  return window.sessionStorage.getItem(SESSION_KEY);
}

/** 4 chủ đề cửa vào cho màn chào. Chỉ trả chủ đề đang bật (docx/13 §5.4). */
export async function fetchTopics(): Promise<Topic[]> {
  const res = await fetch(`${API_BASE}/api/topics`);
  if (!res.ok) throw new Error(`GET /api/topics ${res.status}`);
  return z.array(topicSchema).parse(await res.json());
}

/** Luôn mở phiên MỚI — dùng khi người dùng bấm "Cuộc trò chuyện mới" ở sidebar. */
export async function createSession(topic?: string | null): Promise<string> {
  const res = await fetch(`${API_BASE}/api/session`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...(await authHeaders()) },
    body: JSON.stringify({ topic: topic ?? null }),
  });
  if (!res.ok) throw new Error(`POST /api/session ${res.status}`);
  const { session_id } = (await res.json()) as { session_id: string };
  setActiveSession(session_id);
  return session_id;
}

/**
 * Trỏ "phiên đang mở" sang một session_id khác (đổi cuộc trò chuyện ở sidebar).
 * Trang /assessment đọc lại qua ensureSession() nên bài đánh giá luôn gắn đúng
 * phiên đang xem.
 */
export function setActiveSession(sessionId: string): void {
  if (typeof window === "undefined") return;
  window.sessionStorage.setItem(SESSION_KEY, sessionId);
}

export async function getAssessment(): Promise<AssessmentSpec> {
  const res = await fetch(`${API_BASE}/api/assessment`);
  if (!res.ok) throw new Error(`GET /api/assessment ${res.status}`);
  return assessmentSpecSchema.parse(await res.json());
}

export async function submitAssessment(
  sessionId: string,
  answers: Record<string, number>,
): Promise<AssessmentResult> {
  const res = await fetch(`${API_BASE}/api/assessment`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, answers }),
  });
  if (!res.ok) throw new Error(`POST /api/assessment ${res.status}`);
  return assessmentResultSchema.parse(await res.json());
}
