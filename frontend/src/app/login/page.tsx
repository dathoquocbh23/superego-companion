"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Brain, EyeOff, Sparkles, Timer } from "lucide-react";

import { AppShell, BrandMark } from "@/components/app-shell";
import { DisclaimerBanner } from "@/components/disclaimer-banner";
import { useAuth } from "@/features/auth/use-auth";
import { pingBackend } from "@/lib/api";
import { authConfigured, getSupabase } from "@/lib/supabase";

/**
 * Đăng nhập — BẮT BUỘC từ 07/09/2026. Đây là cửa vào duy nhất của app.
 *
 * Trước đây đăng nhập là tuỳ chọn và phiên ẩn danh chat được bình thường. Đổi
 * vì dự án bắt đầu lưu nguyên văn hội thoại phục vụ nghiên cứu: dữ liệu không
 * có chủ thì không xoá theo yêu cầu được và không gắn được cơ sở đồng ý nào.
 *
 * "Vào thử ngay" KHÔNG phải quay lại chế độ cũ — nó tạo một TÀI KHOẢN ẨN DANH
 * thật của Supabase (UUID, không email). Người dùng vẫn không khai gì, nhưng
 * dữ liệu của họ có chủ và họ đòi xoá được.
 *
 * Bố cục hai cột: cột trái nói RÕ đăng nhập để làm gì và không làm gì, cột phải
 * là biểu mẫu. Học sinh đang do dự có nên để bot nhớ mình hay không thì phần
 * giải thích đó quan trọng ngang cái ô nhập email, không nên nhét thành một
 * đoạn chữ nhỏ phía trên form.
 */
export default function LoginPage() {
  const router = useRouter();
  const { user, loading, signInAnonymous } = useAuth();
  const [mode, setMode] = useState<"in" | "up">("in");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  // AuthGate nhét ?next=… khi đá người chưa đăng nhập về đây. Đọc từ
  // window thay vì useSearchParams() để khỏi phải bọc Suspense.
  const dichDen = () => {
    if (typeof window === "undefined") return "/chat";
    const next = new URLSearchParams(window.location.search).get("next");
    return next && next.startsWith("/") ? next : "/chat";
  };

  // Đã có phiên rồi mà còn ở trang này (bấm back, mở lại tab) → đi tiếp luôn.
  useEffect(() => {
    if (!loading && user) router.replace(dichDen());
  }, [loading, user, router]);

  // Vừa mở trang đăng nhập là đánh thức backend luôn — người dùng còn đọc/gõ
  // email thì Render đã kịp dậy trước khi họ bấm vào trò chuyện.
  useEffect(() => {
    pingBackend();
  }, []);

  const vaoThuNgay = async () => {
    if (busy) return;
    setBusy(true);
    setMsg(null);
    const err = await signInAnonymous();
    setBusy(false);
    if (err) {
      setMsg(err);
      return;
    }
    router.push(dichDen());
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    const sb = getSupabase();
    if (!sb || busy) return;
    setBusy(true);
    setMsg(null);
    const { error } =
      mode === "in"
        ? await sb.auth.signInWithPassword({ email, password })
        : await sb.auth.signUp({ email, password });
    setBusy(false);
    if (error) {
      setMsg(error.message);
      return;
    }
    if (mode === "up") {
      setMsg("Đã tạo tài khoản. Kiểm tra email để xác nhận rồi đăng nhập nhé.");
      setMode("in");
      return;
    }
    router.push(dichDen());
  };

  return (
    <AppShell>
      <div className="flex min-h-0 flex-1">
        <SidePanel />

        <div className="scroll-thin flex flex-1 flex-col overflow-y-auto">
          <div className="flex shrink-0 items-center justify-between px-4 py-3 sm:px-6">
            <div className="flex items-center gap-2.5 lg:invisible">
              <BrandMark
                className="size-8"
                onClick={pingBackend}
                title="Đánh thức máy chủ cho phản hồi nhanh hơn"
              />
              <span className="text-[15px] font-semibold tracking-tight">Đồng hành</span>
            </div>

          </div>

          <div className="flex flex-1 items-center justify-center px-5 pb-10">
            <div className="w-full max-w-sm">
              {authConfigured ? (
                <>
                  <h1 className="text-[22px] font-semibold tracking-tight">
                    {mode === "in" ? "Đăng nhập" : "Tạo tài khoản"}
                  </h1>
                  <p className="mt-1 text-[13px] leading-relaxed text-[var(--muted)]">
                    Chỉ cần email và mật khẩu. Không hỏi tên thật, không hỏi trường lớp.
                  </p>

                  {/* Chuyển giữa đăng nhập / tạo mới — đặt ngay trên form để
                      người vào nhầm nhánh không phải kéo xuống cuối tìm. */}
                  <div className="mt-4 grid grid-cols-2 gap-1 rounded-2xl bg-[var(--surface-2)] p-1">
                    {(
                      [
                        ["in", "Đăng nhập"],
                        ["up", "Tạo tài khoản"],
                      ] as const
                    ).map(([value, label]) => (
                      <button
                        key={value}
                        type="button"
                        onClick={() => {
                          setMode(value);
                          setMsg(null);
                        }}
                        aria-pressed={mode === value}
                        className={`rounded-xl px-3 py-2 text-[13px] font-medium transition-colors ${
                          mode === value
                            ? "bg-[var(--surface)] text-[var(--text)] shadow-[var(--shadow-card)]"
                            : "text-[var(--muted)] hover:text-[var(--text)]"
                        }`}
                      >
                        {label}
                      </button>
                    ))}
                  </div>

                  <form onSubmit={submit} className="mt-4 flex flex-col gap-3">
                    <label className="flex flex-col gap-1.5">
                      <span className="text-[13px] font-medium">Email</span>
                      <input
                        type="email"
                        required
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        autoComplete="email"
                        placeholder="ban@email.com"
                        className="rounded-2xl border border-[var(--border-strong)] bg-[var(--surface)] px-3.5 py-2.5 text-[15px] outline-none transition-colors placeholder:text-[var(--muted)] focus:border-[var(--accent)]"
                      />
                    </label>

                    <label className="flex flex-col gap-1.5">
                      <span className="text-[13px] font-medium">Mật khẩu</span>
                      <input
                        type="password"
                        required
                        minLength={6}
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        autoComplete={mode === "in" ? "current-password" : "new-password"}
                        placeholder="Ít nhất 6 ký tự"
                        className="rounded-2xl border border-[var(--border-strong)] bg-[var(--surface)] px-3.5 py-2.5 text-[15px] outline-none transition-colors placeholder:text-[var(--muted)] focus:border-[var(--accent)]"
                      />
                    </label>

                    {msg && (
                      <p
                        role="status"
                        className="rounded-xl bg-[var(--rose-bg)] px-3 py-2 text-[13px] leading-snug text-[var(--rose-ink)]"
                      >
                        {msg}
                      </p>
                    )}

                    <button
                      type="submit"
                      disabled={busy}
                      className="mt-1 rounded-2xl bg-[var(--ink)] px-4 py-3 text-[15px] font-medium text-white transition-colors hover:bg-[var(--ink-hover)] disabled:opacity-50"
                    >
                      {busy ? "Đang xử lý…" : mode === "in" ? "Đăng nhập" : "Tạo tài khoản"}
                    </button>
                  </form>
                </>
              ) : (
                <>
                  <h1 className="text-[22px] font-semibold tracking-tight">Chưa bật đăng nhập</h1>
                  <p className="mt-2 text-[13px] leading-relaxed text-[var(--muted)]">
                    Bản chạy này chưa cấu hình Supabase (thiếu{" "}
                    <code className="rounded bg-[var(--surface-2)] px-1">NEXT_PUBLIC_SUPABASE_URL</code>{" "}
                    /{" "}
                    <code className="rounded bg-[var(--surface-2)] px-1">
                      NEXT_PUBLIC_SUPABASE_ANON_KEY
                    </code>
                    ). Mọi tính năng trò chuyện vẫn chạy bình thường ở chế độ ẩn danh.
                  </p>
                </>
              )}

              {authConfigured && (
                <>
                  <div className="my-5 flex items-center gap-3">
                    <span className="h-px flex-1 bg-[var(--border)]" />
                    <span className="text-[11px] text-[var(--muted)]">hoặc</span>
                    <span className="h-px flex-1 bg-[var(--border)]" />
                  </div>

                  <button
                    type="button"
                    onClick={vaoThuNgay}
                    disabled={busy}
                    className="flex w-full items-center justify-center gap-2 rounded-2xl border border-[var(--accent)]/40 bg-[var(--accent-soft)] px-4 py-3 text-[15px] font-medium text-[var(--accent-ink)] transition-colors hover:border-[var(--accent)]/70 disabled:opacity-50"
                  >
                    <Sparkles className="size-4" aria-hidden />
                    Vào thử ngay, không cần email
                  </button>
                  <p className="mt-2 text-center text-[12px] leading-relaxed text-[var(--muted)]">
                    Tạo một tài khoản tạm không gắn danh tính. Lịch sử chỉ nằm trên
                    máy này; muốn giữ lại thì thêm email sau, không mất gì cả.
                  </p>
                </>
              )}

              <DisclaimerBanner variant="attached" />
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}

/** Cột trái: đăng nhập đổi lấy cái gì, và cái gì thì không đổi. */
function SidePanel() {
  return (
    <aside className="relative hidden w-[44%] max-w-lg shrink-0 flex-col justify-between overflow-hidden border-r border-[var(--border)] bg-[linear-gradient(160deg,var(--accent-soft),#f6f2ff_55%,#ffffff)] p-9 lg:flex">
      <div className="flex items-center gap-2.5">
        <BrandMark className="size-8" />
        <span className="text-[15px] font-semibold tracking-tight">Đồng hành</span>
      </div>

      <div>
        <div className="orb mb-6 size-20 rounded-full" aria-hidden />
        <h2 className="text-[22px] leading-snug font-semibold tracking-tight">
          Đăng nhập là tuỳ chọn.
          <br />
          Không đăng nhập vẫn dùng được hết.
        </h2>
        <p className="mt-2 max-w-sm text-[13px] leading-relaxed text-[var(--muted)]">
          Tài khoản chỉ mở thêm một thứ: để mình nhớ được những gì bạn đã kể ở các lần trước — và
          bạn phải tự bật thì mới có.
        </p>

        <ul className="mt-6 flex flex-col gap-3">
          <Bullet icon={Brain} title="Bạn bật thì mới nhớ">
            Mặc định là tắt. Bật rồi tắt lại lúc nào cũng được, ngay trong cài đặt.
          </Bullet>
          <Bullet icon={EyeOff} title="Không lưu đoạn chat">
            Chỉ giữ chủ đề bạn hay nhắc và vài câu bạn tự viết. Xem và xoá được từng câu.
          </Bullet>
          <Bullet icon={Timer} title="Tự mờ dần">
            Chủ đề không được nhắc lại khoảng hai tháng rưỡi sẽ tự biến mất.
          </Bullet>
        </ul>
      </div>

      <p className="text-[11px] leading-relaxed text-[var(--muted)]">
        Cần giúp ngay bây giờ?{" "}
        <a href="tel:0832000202" className="font-medium text-[var(--rose-ink)] hover:underline">
          Hotline sơ cứu tâm lý 0832000202
        </a>
      </p>
    </aside>
  );
}

function Bullet({
  icon: Icon,
  title,
  children,
}: {
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <li className="flex gap-3">
      <span className="mt-0.5 grid size-8 shrink-0 place-items-center rounded-xl border border-[var(--accent)]/25 bg-[var(--surface)] text-[var(--accent)]">
        <Icon className="size-4" />
      </span>
      <span className="text-[13px] leading-relaxed">
        <span className="block font-medium">{title}</span>
        <span className="text-[var(--muted)]">{children}</span>
      </span>
    </li>
  );
}
