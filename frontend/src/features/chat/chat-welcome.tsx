"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight } from "lucide-react";

import { useAuth } from "@/features/auth/use-auth";
import { fetchTopics } from "@/lib/api";
import type { Topic } from "@/lib/types";

/**
 * Màn hình chào — hiện khi phiên chưa có lượt nào của người dùng.
 *
 * ĐỔI 09/09/2026 (docx/13, docx/07 §2.3b): 3 thẻ gợi ý cảm xúc → MENU 4 CHỦ ĐỀ,
 * map 1:1 với 4 folder tài liệu nghiên cứu. Câu chữ nạp từ `GET /api/topics`,
 * KHÔNG hardcode ở đây — tiêu đề trên thẻ và nội dung bấm vào phải cùng nguồn.
 *
 * ⚠️ BA THỨ KHÔNG ĐƯỢC BỎ khi sửa file này. App tham chiếu "Góc Hiểu Mình"
 * thiếu cả ba, copy layout của nó mà không chừa chỗ là mất luôn:
 *
 *   1. Ô NHẬP TỰ DO (`children`) — luồng sản phẩm là lý thuyết → HỌC SINH KỂ
 *      CHUYỆN MÌNH → phân tích. Bỏ ô nhập là cắt đứt bước giữa, và học sinh
 *      đang khó khăn mất luôn đường nói.
 *   2. DÒNG HOTLINE ở cuối.
 *   3. Banner disclaimer (đi kèm composer, `variant="attached"`).
 *
 * Chủ đề chưa trích xong nội dung không nằm trong danh sách trả về — backend
 * lọc theo `enabled`. Thà giấu một ô còn hơn bày ra để bấm vào rồi bot bịa.
 */
export function ChatWelcome({
  onPickTopic,
  children,
}: {
  onPickTopic: (topic: Topic) => void;
  children: React.ReactNode;
}) {
  const { user } = useAuth();
  const router = useRouter();
  const name = user?.email ? user.email.split("@")[0] : null;

  const [topics, setTopics] = useState<Topic[]>([]);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    fetchTopics()
      .then(setTopics)
      .catch(() => setFailed(true));
  }, []);

  const pick = (t: Topic) => {
    // Chủ đề "Nhận diện" mở bằng bài Likert 10 câu chứ không bằng một lượt
    // chat: cả 10 câu đều thuộc đúng tài liệu của chủ đề đó (docx/13 §3).
    if (t.opens_assessment) {
      router.push(`/assessment?topic=${encodeURIComponent(t.id)}`);
      return;
    }
    onPickTopic(t);
  };

  return (
    <div className="scroll-thin flex-1 overflow-y-auto">
      <div className="mx-auto flex min-h-full w-full max-w-3xl flex-col justify-center px-4 py-8">
        <div className="animate-rise flex flex-col items-center text-center">
          <div className="orb mb-5 size-24 rounded-full sm:size-28" aria-hidden />
          <p className="text-gradient text-2xl font-semibold sm:text-[28px]">
            {name ? `Chào ${name},` : "Chào bạn,"}
          </p>
          <h1 className="mt-0.5 text-2xl font-semibold tracking-tight sm:text-[30px]">
            hôm nay bạn muốn bắt đầu từ đâu?
          </h1>
          <p className="mt-3 max-w-md text-[13px] leading-relaxed text-[var(--muted)]">
            Chọn một chủ đề để tìm hiểu, hoặc kể luôn chuyện của bạn. Không ai chấm điểm bạn ở đây cả.
          </p>
        </div>

        {topics.length > 0 && (
          <div className="mt-7 grid gap-2.5 sm:grid-cols-2">
            {topics.map((t) => (
              <button
                key={t.id}
                type="button"
                onClick={() => pick(t)}
                className="group flex flex-col gap-1.5 rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-4 text-left transition-colors hover:border-[var(--accent)]/40 hover:bg-[var(--accent-soft)]"
              >
                <span className="text-[15px] font-semibold">{t.title}</span>
                <span className="text-[12px] leading-snug text-[var(--muted)]">{t.subtitle}</span>
                <span className="mt-0.5 flex items-center gap-1 text-[12px] font-medium text-[var(--accent-ink)] opacity-0 transition-opacity group-hover:opacity-100">
                  {t.opens_assessment ? "Làm thử 10 câu" : "Tìm hiểu"}
                  <ArrowRight className="size-3" aria-hidden />
                </span>
              </button>
            ))}
          </div>
        )}

        {/* Ô nhập KHÔNG phụ thuộc việc nạp chủ đề: /api/topics hỏng thì màn này
            vẫn phải dùng được. Đây là đường vào chính, thẻ chỉ là lối phụ. */}
        <div className="mt-4">{children}</div>

        {failed && (
          <p className="mt-2 text-center text-[11px] text-[var(--muted)]">
            Chưa tải được danh sách chủ đề — bạn cứ nhắn thẳng cho mình cũng được.
          </p>
        )}

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
