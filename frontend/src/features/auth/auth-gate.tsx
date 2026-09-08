"use client";

import { AppShell, BrandMark } from "@/components/app-shell";
import { useAuth } from "./use-auth";

/**
 * Cổng phiên. Bọc mọi trang trừ /login.
 *
 * 08/09/2026 — KHÔI PHỤC chat ẩn danh. Đăng nhập trở lại thành TUỲ CHỌN: phiên
 * không gắn tài khoản (user_id = null) được trò chuyện bình thường như trước
 * ngày 07/09. Backend vẫn nhận token Supabase nếu có và tự coi thiếu/sai token
 * là phiên ẩn danh (app/api/session.py), nên ở đây không đá ai về /login nữa.
 *
 * Vẫn giữ màn chờ trong lúc đọc session để trang không kịp nháy lời chào sai
 * rồi mới có tên người dùng. Chưa cấu hình Supabase thì bỏ qua luôn bước chờ.
 */
export function AuthGate({ children }: { children: React.ReactNode }) {
  const { configured, loading } = useAuth();

  if (configured && loading) return <GateSplash />;
  return <>{children}</>;
}

/** Màn chờ trong lúc đọc session — tránh nháy nội dung rồi mới có danh tính. */
function GateSplash() {
  return (
    <AppShell>
      <div className="flex flex-1 flex-col items-center justify-center gap-4">
        <BrandMark className="size-10 animate-pulse" />
        <p className="text-[13px] text-[var(--muted)]">Đang mở phiên…</p>
      </div>
    </AppShell>
  );
}
