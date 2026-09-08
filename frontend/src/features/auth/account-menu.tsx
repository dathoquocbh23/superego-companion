"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Brain, ChevronRight, LogIn, LogOut, Settings, Trash2, X } from "lucide-react";

import { MemoryConsentDialog } from "./memory-consent-dialog";
import { useAuth } from "./use-auth";

/**
 * Chân sidebar: một hàng avatar duy nhất, bấm vào mở bảng cài đặt.
 *
 * Trước đây mọi công tắc (bộ nhớ, quên tôi đi, xoá lịch sử) nằm phơi hết ở chân
 * sidebar — chiếm chỗ và làm nút xoá đỏ chót đập vào mắt suốt buổi trò chuyện.
 * Gom vào một bảng: hàng ngày chỉ thấy avatar, cần đổi gì thì mở ra. Riêng lời
 * hứa "lịch sử chỉ nằm trên máy này" vẫn phải đọc được ngay trong bảng đó chứ
 * không giấu thêm một lớp nữa (docx/00 §4, docx/12 §7).
 */
export function AccountMenu({
  onClearAll,
  hasHistory,
}: {
  onClearAll: () => void;
  hasHistory: boolean;
}) {
  const [open, setOpen] = useState(false);
  const { configured, user, prefs, loading } = useAuth();

  const name = user?.email ? user.email.split("@")[0] : "Khách";
  // Tài khoản ẩn danh CÓ chủ (UUID thật) nhưng chưa gắn email — nếu mất máy
  // này là mất luôn đường quay lại. Nói thẳng ra, đừng để họ tưởng đã an toàn.
  const sub = loading
    ? "Đang tải…"
    : user?.isAnonymous
      ? "Tài khoản tạm · thêm email để giữ lịch sử"
      : user
        ? prefs?.memoryEnabled
          ? "Trí nhớ đang bật"
          : "Trí nhớ đang tắt"
        : configured
          ? "Chưa đăng nhập"
          : "Đang dùng ẩn danh";

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        aria-haspopup="dialog"
        className="flex w-full items-center gap-2.5 rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-2 text-left transition-colors hover:bg-[var(--surface-2)]"
      >
        <Avatar email={user?.email ?? null} />
        <span className="min-w-0 flex-1">
          <span className="block truncate text-[13px] font-medium">{name}</span>
          <span className="block truncate text-[11px] text-[var(--muted)]">{sub}</span>
        </span>
        <Settings className="size-4 shrink-0 text-[var(--muted)]" aria-hidden />
      </button>

      <SettingsDialog
        open={open}
        onClose={() => setOpen(false)}
        onClearAll={onClearAll}
        hasHistory={hasHistory}
      />
    </>
  );
}

/**
 * Avatar nhân vật: mặt cười tối giản trên nền dải tím. Đã đăng nhập thì thay
 * bằng chữ cái đầu của email để phân biệt được tài khoản.
 */
function Avatar({ email }: { email: string | null }) {
  return (
    <span
      aria-hidden
      className="grid size-9 shrink-0 place-items-center overflow-hidden rounded-full bg-[linear-gradient(135deg,var(--accent-2),var(--accent))] text-[13px] font-semibold text-white shadow-[0_4px_12px_-6px_rgb(124_92_255/0.9)]"
    >
      {email ? (
        email.slice(0, 1).toUpperCase()
      ) : (
        <svg viewBox="0 0 36 36" className="size-full" fill="none">
          <circle cx="18" cy="14" r="6.5" fill="white" fillOpacity="0.95" />
          <path
            d="M5.5 33c1.6-6.6 6.6-10 12.5-10s10.9 3.4 12.5 10"
            fill="white"
            fillOpacity="0.95"
          />
          <circle cx="15.6" cy="13.6" r="1" fill="#5b46c9" />
          <circle cx="20.4" cy="13.6" r="1" fill="#5b46c9" />
          <path
            d="M15.4 16.6c1.5 1.2 3.7 1.2 5.2 0"
            stroke="#5b46c9"
            strokeWidth="1.1"
            strokeLinecap="round"
          />
        </svg>
      )}
    </span>
  );
}

function SettingsDialog({
  open,
  onClose,
  onClearAll,
  hasHistory,
}: {
  open: boolean;
  onClose: () => void;
  onClearAll: () => void;
  hasHistory: boolean;
}) {
  const { configured, user, prefs, loading, enableMemory, disableMemory, forgetMe, signOut } =
    useAuth();
  const [askConsent, setAskConsent] = useState(false);
  const [confirmForget, setConfirmForget] = useState(false);
  const [confirmClear, setConfirmClear] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    if (!open) {
      setConfirmForget(false);
      setConfirmClear(false);
      setErr(null);
      return;
    }
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  const memoryOn = prefs?.memoryEnabled ?? false;

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center sm:items-center">
      <button type="button" aria-label="Đóng" onClick={onClose} className="absolute inset-0 bg-black/40" />

      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="settings-title"
        className="relative max-h-[90dvh] w-full max-w-md overflow-y-auto rounded-t-3xl bg-[var(--surface)] p-5 shadow-[var(--shadow-shell)] sm:rounded-3xl"
      >
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-2.5">
            <Avatar email={user?.email ?? null} />
            <div>
              <h2 id="settings-title" className="text-base font-semibold">
                Cài đặt
              </h2>
              <p className="text-[12px] text-[var(--muted)]">
                {user?.email ?? "Đang dùng ẩn danh"}
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Đóng"
            className="grid size-8 shrink-0 place-items-center rounded-lg text-[var(--muted)] hover:bg-black/5"
          >
            <X className="size-4" />
          </button>
        </div>

        {/* ── Tài khoản ─────────────────────────────────────────────── */}
        {configured && !loading && (
          <Section title="Tài khoản">
            {user ? (
              <button
                type="button"
                onClick={() => {
                  void signOut();
                  onClose();
                }}
                className="flex w-full items-center gap-2 rounded-xl px-2.5 py-2 text-left text-[13px] transition-colors hover:bg-black/5"
              >
                <LogOut className="size-4 shrink-0 text-[var(--muted)]" aria-hidden />
                Đăng xuất
              </button>
            ) : (
              <Link
                href="/login"
                onClick={onClose}
                className="flex items-center gap-2 rounded-xl px-2.5 py-2 text-[13px] font-medium text-[var(--accent-ink)] transition-colors hover:bg-[var(--accent-soft)]"
              >
                <LogIn className="size-4 shrink-0" aria-hidden />
                Đăng nhập để bot nhớ bạn ở lần sau
                <ChevronRight className="ml-auto size-3.5" aria-hidden />
              </Link>
            )}
          </Section>
        )}

        {/* ── Trí nhớ dài hạn ───────────────────────────────────────── */}
        {configured && !loading && user && (
          <Section title="Trí nhớ dài hạn">
            {/* Bật thì phải qua popup đồng ý; tắt thì bấm phát tắt luôn — rào
                cản chỉ đặt ở chiều BẬT, chiều tắt càng dễ càng tốt. */}
            <label className="flex cursor-pointer items-start gap-2.5 rounded-xl px-2.5 py-2 transition-colors hover:bg-black/5">
              <input
                type="checkbox"
                checked={memoryOn}
                onChange={(e) => {
                  setErr(null);
                  if (e.target.checked) setAskConsent(true);
                  else void disableMemory();
                }}
                className="mt-0.5 size-3.5 shrink-0 accent-[var(--accent)]"
              />
              <span className="text-[13px] leading-snug">
                <span className="flex items-center gap-1.5 font-medium">
                  <Brain className="size-3.5" aria-hidden />
                  Nhớ mình giữa các lần trò chuyện
                </span>
                <span className="mt-0.5 block text-[11px] text-[var(--muted)]">
                  Chỉ giữ chủ đề và vài câu bạn tự viết. Tắt lúc nào cũng được.
                </span>
              </span>
            </label>

            {err && <p className="px-2.5 text-[11px] leading-snug text-[var(--rose-ink)]">{err}</p>}

            {memoryOn && (
              <Link
                href="/memory"
                onClick={onClose}
                className="flex items-center gap-2 rounded-xl px-2.5 py-2 text-[13px] text-[var(--accent-ink)] transition-colors hover:bg-[var(--accent-soft)]"
              >
                Xem bot đang nhớ gì về mình
                <ChevronRight className="ml-auto size-3.5" aria-hidden />
              </Link>
            )}

            <button
              type="button"
              onClick={() => {
                if (!confirmForget) {
                  setConfirmForget(true);
                  return;
                }
                void forgetMe();
                setConfirmForget(false);
              }}
              className="flex w-full items-center gap-2 rounded-xl px-2.5 py-2 text-left text-[13px] text-[var(--rose-ink)] transition-colors hover:bg-[var(--rose-bg)]"
            >
              <Trash2 className="size-4 shrink-0" aria-hidden />
              {confirmForget ? "Chắc chắn xoá sạch mọi thứ?" : "Quên tôi đi"}
            </button>
          </Section>
        )}

        {/* ── Lịch sử trên máy ──────────────────────────────────────── */}
        <Section title="Lịch sử trò chuyện">
          <p className="px-2.5 text-[12px] leading-relaxed text-[var(--muted)]">
            Lịch sử chỉ lưu trên máy này, không gửi lên máy chủ. Dùng máy chung thì nhớ xoá sau khi
            trò chuyện xong.
          </p>
          {hasHistory && (
            <button
              type="button"
              onClick={() => {
                if (!confirmClear) {
                  setConfirmClear(true);
                  return;
                }
                onClearAll();
                setConfirmClear(false);
                onClose();
              }}
              className="mt-1 flex w-full items-center gap-2 rounded-xl px-2.5 py-2 text-left text-[13px] text-[var(--rose-ink)] transition-colors hover:bg-[var(--rose-bg)]"
            >
              <Trash2 className="size-4 shrink-0" aria-hidden />
              {confirmClear ? "Chắc chắn xoá tất cả lịch sử?" : "Xoá tất cả lịch sử"}
            </button>
          )}
        </Section>

        <MemoryConsentDialog
          open={askConsent}
          onCancel={() => setAskConsent(false)}
          onAccept={async (duoi16, guardian) => {
            const msg = await enableMemory(duoi16, guardian);
            setAskConsent(false);
            if (msg) setErr(msg);
          }}
        />
      </div>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="mt-4 border-t border-[var(--border)] pt-3">
      <h3 className="px-2.5 pb-1 text-[11px] font-semibold tracking-wide text-[var(--muted)] uppercase">
        {title}
      </h3>
      <div className="flex flex-col gap-0.5">{children}</div>
    </section>
  );
}
