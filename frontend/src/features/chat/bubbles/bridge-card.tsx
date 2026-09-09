import { HeartHandshake } from "lucide-react";

import type { Card, ChatMessage } from "@/lib/types";
import { QuickReplies } from "./quick-replies";

/**
 * BRIDGE_CARD (docx/07 §3, docx/11 lượt 6).
 * Kịch bản mở lời là NGUYÊN VĂN tài liệu — bot chỉ tự viết 1–2 câu dẫn (`lead`).
 * Không doạ, không hứa hẹn.
 */
export function BridgeCard({
  card,
  message,
  onReply,
  disabled,
}: {
  card: Card;
  message: ChatMessage;
  onReply: (t: string) => void;
  disabled: boolean;
}) {
  return (
    <div className="max-w-[90%]">
      {card.lead && <p className="mb-2 text-[15px] leading-relaxed">{card.lead}</p>}
      <div className="rounded-xl border border-emerald-300 bg-emerald-50 p-4">
        <div className="mb-2 flex items-center gap-1.5 text-[10px] font-semibold tracking-wider text-emerald-700 uppercase">
          <HeartHandshake className="size-4" aria-hidden />
          {card.title || "Nếu bạn muốn nói với người thật"}
        </div>
        {card.body && (
          <p className="text-[15px] leading-relaxed whitespace-pre-wrap text-emerald-950">{card.body}</p>
        )}
        {/* `card.source` KHÔNG hiện — cùng lý do với coping-card.tsx.
            Sửa 09/09/2026: bản đầu cố ý giữ dòng nguồn ở riêng thẻ này ("thẻ
            hotline / phòng tham vấn thì ghi nguồn làm tăng độ tin"). Lập luận
            đó hỏng từ khi chip TÌM HIỂU của chủ đề "Khi nào nên tìm hỗ trợ"
            cũng đẩy thẻ này ra: học sinh bấm "Nói với thầy cô thì nói thế
            nào?" và nhận về một cái tên file .docx.
            Trường vẫn đi trong payload và vẫn ghi vào transcript. */}
      </div>
      {!disabled && <QuickReplies replies={message.quickReplies ?? []} onReply={onReply} disabled={disabled} />}
    </div>
  );
}
