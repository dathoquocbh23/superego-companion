"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { AlertTriangle } from "lucide-react";

import { PageShell } from "@/components/app-shell";
import { DisclaimerBanner } from "@/components/disclaimer-banner";
import { ensureSession, getAssessment, submitAssessment } from "@/lib/api";
import { LikertForm } from "@/features/assessment/likert-form";
import { ResultCard } from "@/features/assessment/result-card";
import type { AssessmentResult, AssessmentSpec } from "@/lib/types";

/**
 * Bài Likert giờ là NỘI DUNG của chủ đề "Nhận diện trong đời sống học sinh"
 * (docx/13 §3): cả 10 câu đều mang source_doc của đúng tài liệu đó. `?topic=`
 * đi theo suốt luồng để lúc quay về chat, đoạn nói chuyện vẫn nằm trong đúng
 * mảng tài liệu ấy thay vì rơi về chế độ không chủ đề.
 */
function AssessmentInner() {
  const router = useRouter();
  const topic = useSearchParams().get("topic");
  const [spec, setSpec] = useState<AssessmentSpec | null>(null);
  const [result, setResult] = useState<AssessmentResult | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getAssessment()
      .then(setSpec)
      .catch(() => setError("Không tải được bài đánh giá. Backend đang chạy chứ?"));
  }, []);

  const handleSubmit = async (answers: Record<string, number>) => {
    setSubmitting(true);
    setError(null);
    try {
      const sessionId = await ensureSession();
      setResult(await submitAssessment(sessionId, answers));
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch {
      setError("Có lỗi khi chấm điểm. Bạn thử lại giúp mình nhé.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <PageShell title="Bài tự đánh giá">
      <main className="mx-auto w-full max-w-xl px-5 py-6">
        <p className="text-sm leading-relaxed text-[var(--muted)]">
          10 câu, khoảng 2 phút. Đây không phải bài kiểm tra và không có điểm đúng/sai.
        </p>

        {error && (
          <p className="mt-3 rounded-lg bg-[var(--rose-bg)] px-3 py-2 text-sm text-[var(--rose-ink)]">{error}</p>
        )}

        {result ? (
          <div className="mt-4">
            <ResultCard result={result} topic={topic} />
          </div>
        ) : spec ? (
          <>
            {/* Disclaimer hiện TRƯỚC khi làm (docx/07 §2.2) */}
            <div className="mt-3 flex items-start gap-2 rounded-lg bg-[var(--amber-bg)] px-3 py-2 text-[var(--amber-ink)]">
              <AlertTriangle className="mt-0.5 size-4 shrink-0" aria-hidden />
              <p className="text-xs leading-snug">{spec.disclaimer}</p>
            </div>
            <div className="mt-4">
              <LikertForm
                spec={spec}
                submitting={submitting}
                onSubmit={handleSubmit}
                onSkip={() => router.push(topic ? `/chat?topic=${encodeURIComponent(topic)}` : "/chat")}
              />
            </div>
          </>
        ) : (
          !error && <p className="mt-4 text-sm text-[var(--muted)]">Đang tải…</p>
        )}

        <div className="mt-6">
          <DisclaimerBanner variant="attached" />
        </div>
      </main>
    </PageShell>
  );
}

export default function AssessmentPage() {
  // useSearchParams() bắt buộc nằm trong Suspense ở App Router.
  return (
    <Suspense fallback={<p className="p-6 text-sm text-[var(--muted)]">Đang tải…</p>}>
      <AssessmentInner />
    </Suspense>
  );
}
