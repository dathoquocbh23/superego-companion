import Link from "next/link";
import { ArrowRight, ClipboardList, MessageCircleHeart, Phone } from "lucide-react";

import { AppShell } from "@/components/app-shell";
import { BrandPing } from "@/components/brand-ping";
import { AuthGate } from "@/features/auth/auth-gate";
import { DisclaimerBanner } from "@/components/disclaimer-banner";

export default function HomePage() {
  return (
    <AuthGate>
    <AppShell>
      <header className="flex shrink-0 items-center justify-between px-4 py-3 sm:px-6">
        <div className="flex items-center gap-2.5">
          <BrandPing className="size-8" />
          <span className="text-[15px] font-semibold tracking-tight">Đồng hành</span>
        </div>
        <Link
          href="/chat"
          className="flex items-center gap-1.5 rounded-full bg-[var(--ink)] px-4 py-2 text-[13px] font-medium text-white transition-colors hover:bg-[var(--ink-hover)]"
        >
          Vào trò chuyện
          <ArrowRight className="size-3.5" aria-hidden />
        </Link>
      </header>

      <main className="scroll-thin flex-1 overflow-y-auto">
        <div className="mx-auto flex min-h-full w-full max-w-2xl flex-col justify-center px-5 py-10">
          <div className="animate-rise flex flex-col items-center text-center">
            <div className="orb mb-6 size-28 rounded-full" aria-hidden />
            <p className="text-gradient text-2xl font-semibold sm:text-[28px]">
              Đôi khi điều khó nhất không phải chuyện đã xảy ra —
            </p>
            <h1 className="mt-1 text-2xl leading-snug font-semibold tracking-tight sm:text-[30px]">
              mà là cách mình nói với chính mình sau đó.
            </h1>
          </div>

          <div className="mt-9 grid gap-3 sm:grid-cols-2">
            <Link
              href="/chat"
              className="group flex flex-col gap-2 rounded-3xl border border-[var(--accent)]/30 bg-[var(--accent-soft)] p-5 transition-colors hover:border-[var(--accent)]/60"
            >
              <MessageCircleHeart className="size-6 text-[var(--accent)]" aria-hidden />
              <span className="text-lg font-semibold">Trò chuyện ngay</span>
              <span className="text-sm leading-relaxed text-[var(--muted)]">
                Nói ra điều đang làm bạn nặng lòng.
              </span>
              <span className="mt-1 flex items-center gap-1 text-[13px] font-medium text-[var(--accent-ink)]">
                Bắt đầu
                <ArrowRight className="size-3.5 transition-transform group-hover:translate-x-0.5" aria-hidden />
              </span>
            </Link>

            <Link
              href="/assessment"
              className="group flex flex-col gap-2 rounded-3xl border border-[var(--border)] bg-[var(--surface)] p-5 shadow-[var(--shadow-card)] transition-colors hover:bg-[var(--surface-2)]"
            >
              <ClipboardList className="size-6 text-[var(--muted)]" aria-hidden />
              <span className="text-lg font-semibold">Thử bài tự đánh giá</span>
              <span className="text-sm leading-relaxed text-[var(--muted)]">
                10 câu, khoảng 2 phút. Không phải bài kiểm tra.
              </span>
              <span className="mt-1 flex items-center gap-1 text-[13px] font-medium text-[var(--text)]">
                Làm thử
                <ArrowRight className="size-3.5 transition-transform group-hover:translate-x-0.5" aria-hidden />
              </span>
            </Link>
          </div>

          <div className="mt-4 rounded-3xl border border-[var(--rose)]/25 bg-[var(--rose-bg)] p-5">
            <p className="text-sm text-[var(--rose-ink)]">Nếu bạn đang trong tình trạng khẩn cấp:</p>
            <a
              href="tel:0832000202"
              className="mt-1 flex items-center gap-2 text-xl font-bold text-[var(--rose-ink)]"
            >
              <Phone className="size-5" aria-hidden /> Hotline sơ cứu tâm lý 0832000202
            </a>
          </div>

          <div className="mt-4">
            <DisclaimerBanner variant="attached" />
          </div>
        </div>
      </main>
    </AppShell>
    </AuthGate>
  );
}
