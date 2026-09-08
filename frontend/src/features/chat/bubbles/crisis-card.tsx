"use client";

import { Fragment } from "react";
import { PhoneCall } from "lucide-react";

import type { Card } from "@/lib/types";

/**
 * 🔴 CRISIS_CARD — hardcoded (docx/07 §4.2, docx/04 §7).
 * Nội dung `markdown` đến từ backend dạng văn bản TĨNH (data/crisis_card.md).
 * Component này KHÔNG nhận nội dung do LLM sinh.
 *
 * Luật: không thu gọn / không đóng được · KHÔNG quick replies ·
 * số điện thoại là <a href="tel:"> · màu khác hẳn bubble thường.
 */
export function CrisisCard({ card }: { card: Card }) {
  const phone = card.phone ?? "0832000202";
  return (
    <div
      role="alert"
      className="w-full rounded-xl border-2 border-[var(--rose)] bg-[var(--rose-bg)] p-5 text-[15px] leading-relaxed"
    >
      <div className="flex items-center gap-2 text-[var(--rose-ink)]">
        <PhoneCall className="size-6 shrink-0" aria-hidden />
        <span className="font-semibold">Hotline sơ cứu tâm lý</span>
      </div>

      <a
        href={`tel:${phone}`}
        className="mt-2 mb-3 block text-3xl font-bold tracking-wide text-[var(--rose-ink)] underline decoration-2 underline-offset-4"
      >
        {phone}
      </a>

      <div className="space-y-2 text-[var(--text)]">{renderMarkdown(card.markdown ?? "")}</div>
    </div>
  );
}

/** Renderer tối giản cho văn bản CỐ ĐỊNH của crisis_card.md — không phải markdown tổng quát. */
function renderMarkdown(md: string) {
  const blocks: React.ReactNode[] = [];
  let list: string[] = [];

  const flushList = (key: string) => {
    if (!list.length) return;
    blocks.push(
      <ul key={key} className="ml-5 list-disc space-y-0.5 text-sm">
        {list.map((li, i) => (
          <li key={i}>{inline(li)}</li>
        ))}
      </ul>,
    );
    list = [];
  };

  md.split("\n").forEach((raw, idx) => {
    const line = raw.trimEnd();
    if (line.startsWith("- ")) {
      list.push(line.slice(2));
      return;
    }
    flushList(`ul-${idx}`);
    if (line === "---") {
      blocks.push(<hr key={`hr-${idx}`} className="my-2 border-[var(--rose)]/30" />);
    } else if (line.trim() === "") {
      // spacing handled by space-y on the parent
    } else if (/^\*[^*].*\*$/.test(line.trim())) {
      blocks.push(
        <p key={`h-${idx}`} className="mt-1 text-xs font-semibold text-[var(--muted)]">
          {line.replace(/^\*|\*$/g, "")}
        </p>,
      );
    } else {
      blocks.push(
        <p key={`p-${idx}`} className="text-sm">
          {inline(line)}
        </p>,
      );
    }
  });
  flushList("ul-end");
  return blocks;
}

function inline(text: string) {
  return text.split(/(\*\*[^*]+\*\*)/g).map((seg, i) =>
    seg.startsWith("**") && seg.endsWith("**") ? (
      <strong key={i}>{seg.slice(2, -2)}</strong>
    ) : (
      <Fragment key={i}>{seg}</Fragment>
    ),
  );
}
