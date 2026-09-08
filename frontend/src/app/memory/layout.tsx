import { AuthGate } from "@/features/auth/auth-gate";

/** Trang này yêu cầu có phiên (tài khoản email hoặc tài khoản ẩn danh). */
export default function Layout({ children }: { children: React.ReactNode }) {
  return <AuthGate>{children}</AuthGate>;
}
