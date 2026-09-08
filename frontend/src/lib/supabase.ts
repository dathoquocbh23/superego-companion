"use client";

import { createClient, type SupabaseClient } from "@supabase/supabase-js";

/**
 * Client Supabase phía trình duyệt — CHỈ dùng anon key.
 *
 * ⚠️ Không bao giờ đặt SERVICE_ROLE_KEY vào NEXT_PUBLIC_*: key đó bypass RLS,
 * lộ ra client là ai cũng đọc được bộ nhớ của mọi học sinh. Service key chỉ
 * sống ở backend (xem docx/12 §8).
 *
 * Thiếu biến môi trường → trả null, app chạy ở chế độ ẩn danh như cũ. Đăng
 * nhập là TUỲ CHỌN, không được phép làm vỡ luồng chính.
 */
const URL = process.env.NEXT_PUBLIC_SUPABASE_URL;
const ANON = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

let client: SupabaseClient | null = null;

export function getSupabase(): SupabaseClient | null {
  if (!URL || !ANON) return null;
  if (!client) {
    client = createClient(URL, ANON, {
      auth: { persistSession: true, autoRefreshToken: true },
    });
  }
  return client;
}

export const authConfigured = Boolean(URL && ANON);

/** Access token hiện tại, hoặc null nếu chưa đăng nhập. */
export async function getAccessToken(): Promise<string | null> {
  const sb = getSupabase();
  if (!sb) return null;
  const { data } = await sb.auth.getSession();
  return data.session?.access_token ?? null;
}
