"use client";

import { HeartCrack, MessageCircleHeart, Wind } from "lucide-react";

import { useAuth } from "@/features/auth/use-auth";

/**
 * Màn hình chào — hiện khi phiên chưa có lượt nào của người dùng.
 * Ba thẻ gợi ý gửi đúng nguyên văn câu ghi trên thẻ, không phải prompt ẩn: người
 * dùng thấy trước mình sắp "nói" gì.
 */
const SUGGESTIONS = [
  {
    icon: MessageCircleHeart,
    title: "Chuyện đang nặng lòng",
    prompt: "Mình vừa gặp một chuyện và không biết bắt đầu kể từ đâu.",
  },
  {
    icon: HeartCrack,
    title: "Tự trách bản thân",
    prompt: "Chuyện gì hỏng mình cũng thấy là tại mình.",
  },
  {
    icon: Wind,
    title: "Căng thẳng trước kỳ thi",
    prompt: "Mình lo kỳ thi đến mức không tập trung học nổi.",
  },
];

export function ChatWelcome({
  onPick,
  children,
}: {
  onPick: (text: string) => void;
  children: React.ReactNode;
}) {
  const { user } = useAuth();
  const name = user?.email ? user.email.split("@")[0] : null;

  return (
    <div className="scroll-thin flex-1 overflow-y-auto">
      <div className="mx-auto flex min-h-full w-full max-w-2xl flex-col justify-center px-4 py-8">
        <div className="animate-rise flex flex-col items-center text-center">
          <div className="orb mb-5 size-24 rounded-full sm:size-28" aria-hidden />
          <p className="text-gradient text-2xl font-semibold sm:text-[28px]">
            {name ? `Chào ${name},` : "Chào bạn,"}
          </p>
          <h1 className="mt-0.5 text-2xl font-semibold tracking-tight sm:text-[30px]">
            hôm nay trong lòng bạn thế nào?
          </h1>
          <p className="mt-3 max-w-md text-[13px] leading-relaxed text-[var(--muted)]">
            Đây là nơi bạn nói ra điều khó nói mà không bị phán xét. Không ai chấm điểm bạn ở đây cả.
          </p>
        </div>

        <div className="mt-7">{children}</div>

        <div className="mt-4 grid gap-2.5 sm:grid-cols-3">
          {SUGGESTIONS.map(({ icon: Icon, title, prompt }) => (
            <button
              key={title}
              type="button"
              onClick={() => onPick(prompt)}
              className="flex flex-col gap-2 rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-3.5 text-left transition-colors hover:border-[var(--accent)]/40 hover:bg-[var(--accent-soft)]"
            >
              <Icon className="size-4 text-[var(--accent)]" aria-hidden />
              <span className="text-[13px] font-semibold">{title}</span>
              <span className="text-[12px] leading-snug text-[var(--muted)]">{prompt}</span>
            </button>
          ))}
        </div>

        <p className="mt-6 text-center text-[11px] text-[var(--muted)]">
          Cần giúp ngay bây giờ?{" "}
          <a href="tel:0832000202" className="font-medium text-[var(--rose-ink)] hover:underline">
            Gọi hotline sơ cứu tâm lý 0832000202
          </a>
        </p>
      </div>
    </div>
  );
}
