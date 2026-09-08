"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";

import { AppShell, BrandMark } from "@/components/app-shell";
import { useAuth } from "./use-auth";

/**
 * Cổng đăng nhập. Bọc mọi trang trừ /login.
 *
 * ĐỔI LUẬT 07/09/2026 — trước đây đăng nhập là TUỲ CHỌN và phiên ẩn danh
 * (user_id = null) được phép chat bình thường. Từ nay không còn phiên nào
 * không có chủ.
 *
 * Vì sao đổi: dự án bắt đầu lưu nguyên văn hội thoại vào Supabase để phục vụ
 * nghiên cứu. Dữ liệu không có chủ thì không xoá theo yêu cầu được, không áp
 * RLS được, và không có cơ sở đồng ý nào gắn vào nó. "Ẩn danh" giờ có nghĩa là
 * TÀI KHOẢN ẨN DANH của Supabase — một hàng thật trong auth.users, có UUID,
 * chỉ là chưa gắn email. Người dùng vẫn không phải khai gì, nhưng dữ liệu của
 * họ có chủ và họ đòi xoá được.
 *
 * Chưa cấu hình Supabase (`configured=false`) thì KHÔNG chặn — bản chạy thiếu
 * biến môi trường phải demo được, không thì lỗi cấu hình biến thành app chết.
 */
export function AuthGate({ children }: { children: React.ReactNode }) {
  const { configured, user, loading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  const canGo = !configured || Boolean(user);

  useEffect(() => {
    if (loading || canGo) return;
    // Nhớ chỗ họ định tới để đăng nhập xong quay lại đúng đó.
    const next = pathname && pathname !== "/" ? `?next=${encodeURIComponent(pathname)}` : "";
    router.replace(`/login${next}`);
  }, [loading, canGo, pathname, router]);

  if (loading || !canGo) return <GateSplash />;
  return <>{children}</>;
}

/** Màn chờ trong lúc đọc session — tránh nháy nội dung rồi mới đá đi. */
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
