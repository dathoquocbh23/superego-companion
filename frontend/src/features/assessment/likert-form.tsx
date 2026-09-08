"use client";

import { useMemo, useState } from "react";

import type { AssessmentSpec } from "@/lib/types";

/** 10 câu, radio 5 mức, cuộn dọc. Nút "Bỏ qua, vào chat luôn" ở mọi thời điểm. */
export function LikertForm({
  spec,
  submitting,
  onSubmit,
  onSkip,
}: {
  spec: AssessmentSpec;
  submitting: boolean;
  onSubmit: (answers: Record<string, number>) => void;
  onSkip: () => void;
}) {
  const [answers, setAnswers] = useState<Record<string, number>>({});
  const answered = Object.keys(answers).length;
  const complete = answered === spec.items.length;
  const progress = useMemo(() => Math.round((answered / spec.items.length) * 100), [answered, spec.items.length]);

  return (
    <div>
      <div className="sticky top-0 z-10 -mx-5 mb-4 border-b border-[var(--border)] bg-[var(--bg)] px-5 py-2">
        <div className="h-1.5 overflow-hidden rounded-full bg-[var(--border)]">
          <div className="h-full bg-[var(--accent)] transition-[width]" style={{ width: `${progress}%` }} />
        </div>
        <div className="mt-1.5 flex items-center justify-between text-xs text-[var(--muted)]">
          <span>
            {answered}/{spec.items.length} câu
          </span>
          <button type="button" onClick={onSkip} className="underline underline-offset-2">
            Bỏ qua, vào chat luôn
          </button>
        </div>
      </div>

      <ol className="space-y-5">
        {spec.items.map((item) => (
          <li key={item.id} className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-4">
            <p className="text-[15px] leading-relaxed">
              {item.id}. {item.text}
            </p>
            <div className="mt-3 grid grid-cols-5 gap-1.5">
              {spec.scale.map((s) => {
                const selected = answers[String(item.id)] === s.value;
                return (
                  <button
                    key={s.value}
                    type="button"
                    aria-pressed={selected}
                    onClick={() => setAnswers((prev) => ({ ...prev, [String(item.id)]: s.value }))}
                    className={
                      "min-h-[44px] rounded-lg border px-1 py-1.5 text-center text-[11px] leading-tight transition-colors " +
                      (selected
                        ? "border-[var(--accent)] bg-[var(--accent)] text-white"
                        : "border-[var(--border)] bg-[var(--bg)] hover:bg-black/5")
                    }
                  >
                    <span className="block text-sm font-semibold">{s.value}</span>
                    {s.label}
                  </button>
                );
              })}
            </div>
          </li>
        ))}
      </ol>

      <button
        type="button"
        disabled={!complete || submitting}
        onClick={() => onSubmit(answers)}
        className="mt-6 w-full rounded-2xl bg-[var(--accent)] py-3 text-[15px] font-semibold text-white transition-opacity disabled:opacity-40"
      >
        {submitting ? "Đang chấm…" : complete ? "Xem kết quả" : `Còn ${spec.items.length - answered} câu`}
      </button>
    </div>
  );
}
