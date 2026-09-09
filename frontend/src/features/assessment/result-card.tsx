"use client";

import { useRouter } from "next/navigation";
import { AlertTriangle, ArrowRight } from "lucide-react";

import type { AssessmentResult } from "@/lib/types";

const BAND_FILL: Record<AssessmentResult["band"], number> = {
  THAP: 20,
  NHE: 45,
  DANG_CHU_Y: 70,
  CAO: 92,
};

/**
 * Màn hình kết quả — LUÔN có nút vào chat (docx/07 §2.2).
 * Không bao giờ là điểm dừng, đặc biệt với band CAO.
 */
export function ResultCard({
  result,
  topic = null,
}: {
  result: AssessmentResult;
  topic?: string | null;
}) {
  const router = useRouter();
  const primary = result.next_actions[0] ?? { label: "Nói chuyện về kết quả này", href: "/chat?from=assessment" };
  // Mang chủ đề về theo (docx/13 §5.7). href từ backend đã có sẵn query nên nối
  // bằng "&"; không có thì Next vẫn hiểu, nhưng dựng bằng URLSearchParams cho
  // chắc thay vì đoán dấu phân cách.
  const href = topic
    ? `${primary.href}${primary.href.includes("?") ? "&" : "?"}topic=${encodeURIComponent(topic)}`
    : primary.href;

  return (
    <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5">
      <p className="text-sm text-[var(--muted)]">Điểm trung bình</p>
      <p className="text-3xl font-bold">{result.average.toFixed(1).replace(".", ",")}</p>

      <div className="mt-3 h-2.5 overflow-hidden rounded-full bg-[var(--border)]">
        <div className="h-full bg-[var(--accent)]" style={{ width: `${BAND_FILL[result.band]}%` }} />
      </div>
      <p className="mt-1.5 text-[15px] font-semibold">{result.band_label}</p>
      <p className="text-sm text-[var(--muted)]">{result.headline}</p>

      <p className="mt-4 text-[15px] leading-relaxed whitespace-pre-wrap">{result.result_text}</p>

      <div className="mt-4 flex items-start gap-2 rounded-lg bg-[var(--amber-bg)] px-3 py-2 text-[var(--amber-ink)]">
        <AlertTriangle className="mt-0.5 size-4 shrink-0" aria-hidden />
        <p className="text-xs leading-snug">{result.disclaimer}</p>
      </div>

      <button
        type="button"
        onClick={() => router.push(href)}
        className="mt-5 flex w-full items-center justify-center gap-2 rounded-2xl bg-[var(--accent)] py-3 text-[15px] font-semibold text-white"
      >
        {primary.label}
        <ArrowRight className="size-4" />
      </button>
    </div>
  );
}
