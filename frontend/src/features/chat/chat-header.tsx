"use client";

import { useState } from "react";
import { Download, LifeBuoy, Phone, X } from "lucide-react";

import { SidebarToggle } from "./session-sidebar";

/**
 * Thanh trên cùng của phòng chat: nhãn trợ lý bên trái, tác vụ bên phải.
 *
 * Nút hotline luôn hiện — không đợi CRISIS_CARD mới xuất hiện thì lúc cần
 * người ta mới phải đi tìm. `showSupport` (đã từng gặp khủng hoảng trong phiên)
 * chỉ làm nút nổi bật hơn và mở sẵn bảng liên hệ.
 */
export function ChatHeader({
  showSupport,
  onOpenSidebar,
  onExpandSidebar,
  sidebarCollapsed,
  onExport,
  canExport,
}: {
  showSupport: boolean;
  onOpenSidebar: () => void;
  onExpandSidebar?: () => void;
  sidebarCollapsed?: boolean;
  onExport?: () => void;
  canExport?: boolean;
}) {
  const [open, setOpen] = useState(false);

  return (
    <header className="relative flex shrink-0 items-center justify-between gap-2 px-3 py-3 sm:px-5">
      <div className="flex min-w-0 items-center gap-1.5">
        <SidebarToggle
          onOpenDrawer={onOpenSidebar}
          onExpand={onExpandSidebar}
          collapsed={sidebarCollapsed}
        />
      </div>

      <div className="flex items-center gap-1.5 sm:gap-2">
        {onExport && (
          <button
            type="button"
            onClick={onExport}
            disabled={!canExport}
            className="hidden items-center gap-1.5 rounded-full border border-[var(--border-strong)] bg-[var(--surface)] px-3.5 py-2 text-[13px] font-medium text-[var(--text)] transition-colors hover:bg-[var(--surface-2)] disabled:opacity-40 sm:flex"
          >
            <Download className="size-4" aria-hidden />
            Tải hội thoại
          </button>
        )}

        <button
          type="button"
          onClick={() => setOpen((v) => !v)}
          aria-expanded={open}
          className={`flex items-center gap-1.5 rounded-full px-3.5 py-2 text-[13px] font-medium transition-colors ${
            showSupport
              ? "bg-[var(--rose)] text-white hover:bg-[var(--rose-ink)]"
              : "bg-[var(--ink)] text-white hover:bg-[var(--ink-hover)]"
          }`}
        >
          <LifeBuoy className="size-4" aria-hidden />
          Nguồn hỗ trợ
        </button>
      </div>

      {open && (
        <div className="absolute top-full right-3 z-20 mt-1 w-[19rem] rounded-2xl border border-[var(--rose)]/30 bg-[var(--surface)] p-4 text-sm shadow-[var(--shadow-shell)] sm:right-5">
          <div className="flex items-start justify-between gap-2">
            <p className="font-semibold text-[var(--rose-ink)]">Hotline sơ cứu tâm lý</p>
            <button
              type="button"
              onClick={() => setOpen(false)}
              aria-label="Đóng"
              className="grid size-6 place-items-center rounded-lg text-[var(--muted)] hover:bg-black/5"
            >
              <X className="size-3.5" />
            </button>
          </div>
          <a
            href="tel:0832000202"
            className="mt-1 flex items-center gap-1.5 text-xl font-bold text-[var(--rose-ink)]"
          >
            <Phone className="size-4" /> 0832000202
          </a>
          <p className="mt-2 text-xs leading-relaxed text-[var(--muted)]">
            Hoặc tìm đến cơ sở tâm lý / bệnh viện tại TP.HCM để được thăm khám và chia sẻ nhiều hơn.
          </p>
        </div>
      )}
    </header>
  );
}
