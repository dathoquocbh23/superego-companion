"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { ClipboardList, Home, PanelLeft, PanelLeftClose, Plus, Search, Trash2, X } from "lucide-react";

import { BrandMark } from "@/components/app-shell";
import { pingBackend } from "@/lib/api";
import { AccountMenu } from "@/features/auth/account-menu";
import { groupConversations, shortWhen, type Conversation } from "@/lib/conversations";

const NAV = [
  { href: "/", label: "Trang chủ", icon: Home },
  { href: "/assessment", label: "Bài tự đánh giá", icon: ClipboardList },
];

/**
 * Sidebar trái — thương hiệu, nút mở phiên mới, ô tìm, điều hướng, lịch sử phiên
 * gom theo ngày, khối tài khoản ở chân.
 * Desktop: cột cố định, thu gọn được. Mobile: drawer trượt, mở từ ChatHeader.
 * Lịch sử nằm trong localStorage của máy → luôn kèm nút xoá (docx/00 §4).
 */
export function SessionSidebar({
  conversations,
  activeId,
  onSelect,
  onNew,
  onDelete,
  onClearAll,
  open,
  onClose,
  busy = false,
  collapsed = false,
  onToggleCollapse,
}: {
  conversations: Conversation[];
  activeId: string | null;
  onSelect: (id: string) => void;
  onNew: () => void;
  onDelete: (id: string) => void;
  onClearAll: () => void;
  open: boolean;
  onClose: () => void;
  busy?: boolean;
  collapsed?: boolean;
  onToggleCollapse?: () => void;
}) {
  const [query, setQuery] = useState("");

  const groups = useMemo(() => {
    const q = query.trim().toLowerCase();
    const list = q ? conversations.filter((c) => c.title.toLowerCase().includes(q)) : conversations;
    return groupConversations(list);
  }, [conversations, query]);

  const panel = (
    <div className="flex h-full w-[264px] shrink-0 flex-col border-r border-[var(--border)] bg-[var(--sidebar)]">
      <div className="flex items-center gap-2 px-4 pt-4 pb-3">
        <BrandMark
          className="size-7"
          onClick={pingBackend}
          title="Đánh thức máy chủ cho phản hồi nhanh hơn"
        />
        <span className="flex-1 truncate text-[15px] font-semibold tracking-tight">Psycheguard</span>
        {onToggleCollapse && (
          <button
            type="button"
            onClick={onToggleCollapse}
            aria-label="Thu gọn thanh bên"
            className="hidden size-7 place-items-center rounded-lg text-[var(--muted)] transition-colors hover:bg-black/5 hover:text-[var(--text)] md:grid"
          >
            <PanelLeftClose className="size-4" />
          </button>
        )}
        <button
          type="button"
          onClick={onClose}
          aria-label="Đóng danh sách"
          className="grid size-8 place-items-center rounded-lg text-[var(--muted)] hover:bg-black/5 md:hidden"
        >
          <X className="size-4" />
        </button>
      </div>

      <div className="px-3">
        <button
          type="button"
          onClick={onNew}
          disabled={busy}
          className="flex w-full items-center justify-center gap-2 rounded-2xl bg-[var(--ink)] px-3 py-3 text-sm font-medium text-white transition-colors hover:bg-[var(--ink-hover)] disabled:opacity-50"
        >
          <Plus className="size-4" aria-hidden />
          Cuộc trò chuyện mới
        </button>

        <div className="mt-2.5 flex items-center gap-2 rounded-2xl border border-[var(--border-strong)] bg-[var(--surface)] px-3 py-2.5 focus-within:border-[var(--accent)]">
          <Search className="size-4 shrink-0 text-[var(--muted)]" aria-hidden />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Tìm trong lịch sử"
            aria-label="Tìm cuộc trò chuyện"
            className="min-w-0 flex-1 bg-transparent text-[13px] outline-none placeholder:text-[var(--muted)]"
          />
          {query && (
            <button
              type="button"
              onClick={() => setQuery("")}
              aria-label="Xoá từ khoá"
              className="grid size-5 place-items-center rounded text-[var(--muted)] hover:bg-black/5"
            >
              <X className="size-3.5" />
            </button>
          )}
        </div>

        <nav aria-label="Điều hướng" className="mt-3 flex flex-col gap-0.5">
          {NAV.map(({ href, label, icon: Icon }) => (
            <Link
              key={href}
              href={href}
              className="flex items-center gap-2.5 rounded-xl px-2.5 py-2 text-[13px] font-medium text-[var(--muted)] transition-colors hover:bg-black/5 hover:text-[var(--text)]"
            >
              <Icon className="size-4" aria-hidden />
              {label}
            </Link>
          ))}
        </nav>
      </div>

      <nav aria-label="Cuộc trò chuyện đã lưu" className="scroll-thin mt-3 flex-1 overflow-y-auto px-3 pb-2">
        {groups.length === 0 ? (
          <p className="px-2 py-3 text-xs leading-relaxed text-[var(--muted)]">
            {query ? "Không có cuộc trò chuyện nào khớp." : "Chưa có cuộc trò chuyện nào được lưu."}
          </p>
        ) : (
          groups.map((group) => (
            <div key={group.label} className="mb-3">
              <p className="px-2.5 pb-1 text-[11px] font-medium text-[var(--muted)]">{group.label}</p>
              <ul className="flex flex-col gap-0.5">
                {group.items.map((c) => {
                  const isActive = c.id === activeId;
                  return (
                    <li key={c.id} className="group relative">
                      <button
                        type="button"
                        onClick={() => onSelect(c.id)}
                        aria-current={isActive ? "true" : undefined}
                        className={`w-full rounded-xl py-2 pr-9 pl-2.5 text-left transition-colors ${
                          isActive
                            ? "bg-[var(--accent-soft)] text-[var(--accent-ink)]"
                            : "text-[var(--text)]/85 hover:bg-black/5"
                        }`}
                      >
                        <span className="block truncate text-[13px] leading-snug">{c.title}</span>
                      </button>
                      <button
                        type="button"
                        onClick={() => onDelete(c.id)}
                        aria-label={`Xoá cuộc trò chuyện: ${c.title}`}
                        title={shortWhen(c.updatedAt)}
                        className="absolute top-1/2 right-1 grid size-7 -translate-y-1/2 place-items-center rounded-lg text-[var(--muted)] opacity-0 transition-opacity group-focus-within:opacity-100 group-hover:opacity-100 hover:bg-[var(--rose-bg)] hover:text-[var(--rose-ink)] focus-visible:opacity-100"
                      >
                        <Trash2 className="size-3.5" />
                      </button>
                    </li>
                  );
                })}
              </ul>
            </div>
          ))
        )}
      </nav>

      <div className="border-t border-[var(--border)] p-3">
        <AccountMenu onClearAll={onClearAll} hasHistory={conversations.length > 0} />
      </div>
    </div>
  );

  return (
    <>
      {!collapsed && <aside className="hidden md:flex">{panel}</aside>}

      {/* drawer mobile */}
      {open && (
        <div className="fixed inset-0 z-30 md:hidden">
          <button
            type="button"
            aria-label="Đóng danh sách"
            onClick={onClose}
            className="absolute inset-0 bg-black/30"
          />
          <aside className="absolute inset-y-0 left-0 flex shadow-xl">{panel}</aside>
        </div>
      )}
    </>
  );
}

/** Nút mở drawer (mobile) hoặc bung lại sidebar đã thu gọn (desktop). */
export function SidebarToggle({
  onOpenDrawer,
  onExpand,
  collapsed,
}: {
  onOpenDrawer: () => void;
  onExpand?: () => void;
  collapsed?: boolean;
}) {
  return (
    <>
      <button
        type="button"
        onClick={onOpenDrawer}
        aria-label="Mở danh sách cuộc trò chuyện"
        className="grid size-8 place-items-center rounded-lg text-[var(--muted)] transition-colors hover:bg-black/5 md:hidden"
      >
        <PanelLeft className="size-4" />
      </button>
      {collapsed && onExpand && (
        <button
          type="button"
          onClick={onExpand}
          aria-label="Mở thanh bên"
          className="hidden size-8 place-items-center rounded-lg text-[var(--muted)] transition-colors hover:bg-black/5 md:grid"
        >
          <PanelLeft className="size-4" />
        </button>
      )}
    </>
  );
}
