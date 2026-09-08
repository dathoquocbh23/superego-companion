"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Brain } from "lucide-react";

import { PageShell } from "@/components/app-shell";
import { DisclaimerBanner } from "@/components/disclaimer-banner";
import { useAuth } from "@/features/auth/use-auth";
import { API_BASE } from "@/lib/api";
import { getSupabase } from "@/lib/supabase";

/**
 * "Bot đang nhớ gì về mình" — quyền xem dữ liệu về chính mình (docx/12 §7,
 * NĐ 13/2023). Thiếu màn này thì bộ nhớ là hộp đen, học sinh không có cách nào
 * biết mà phản bác.
 *
 * Đọc THẲNG từ Supabase bằng anon key: RLS (`user_id = auth.uid()`) mới là thứ
 * bảo đảm chỉ thấy hàng của mình. Đi vòng qua backend bằng service_role thì
 * phải tự viết lại đúng phép kiểm đó bằng tay — thêm một chỗ để sai.
 * Backend chỉ cấp nhãn tiếng Việt của node (/api/graph/labels).
 */
type NodeLabel = { label: string; nhom: string };
type MemRow = {
  node_id: string;
  confidence: number;
  observations: number;
  last_seen: string;
  verbatim: string | null;
};
type EdgeRow = { from_node: string; to_node: string; weight: number };

export default function MemoryPage() {
  const { configured, user, prefs, loading, forgetQuotes } = useAuth();
  const [labels, setLabels] = useState<Record<string, NodeLabel>>({});
  const [nodes, setNodes] = useState<MemRow[]>([]);
  const [edges, setEdges] = useState<EdgeRow[]>([]);
  const [ready, setReady] = useState(false);
  const [xoaXong, setXoaXong] = useState(false);

  useEffect(() => {
    fetch(`${API_BASE}/api/graph/labels`)
      .then((r) => r.json())
      .then(setLabels)
      .catch(() => setLabels({}));
  }, []);

  useEffect(() => {
    const sb = getSupabase();
    if (!sb || !user) return;
    let alive = true;
    (async () => {
      const [n, e] = await Promise.all([
        sb.from("user_memory").select("node_id,confidence,observations,last_seen,verbatim")
          .order("confidence", { ascending: false }),
        sb.from("user_memory_edges").select("from_node,to_node,weight")
          .order("weight", { ascending: false }).limit(12),
      ]);
      if (!alive) return;
      setNodes((n.data as MemRow[]) ?? []);
      setEdges((e.data as EdgeRow[]) ?? []);
      setReady(true);
    })();
    return () => {
      alive = false;
    };
  }, [user]);

  const ten = (id: string) => labels[id]?.label ?? id;

  if (!configured) return <Khung><P>Chưa cấu hình đăng nhập.</P></Khung>;
  if (loading) return <Khung><P>Đang tải…</P></Khung>;
  if (!user)
    return (
      <Khung>
        <P>
          Bạn cần <Link href="/login" className="text-[var(--accent-ink)] underline">đăng nhập</Link>{" "}
          để xem phần này.
        </P>
      </Khung>
    );

  return (
    <Khung>
      <h1 className="flex items-center gap-2 text-lg font-semibold">
        <Brain className="size-4 text-[var(--accent)]" aria-hidden />
        Mình đang nhớ gì về bạn
      </h1>

      <p className="mt-1.5 text-[13px] leading-relaxed text-[var(--muted)]">
        Đây là toàn bộ những gì được lưu lại — không có gì khác. Mỗi chủ đề
        kèm đúng một câu bạn từng viết, để lần sau mình nhớ đúng chuyện đã xảy
        ra. Không có lịch sử đoạn chat. Mọi thứ mờ dần theo thời gian.
      </p>

      {!prefs?.memoryEnabled && (
        <p className="mt-3 rounded-xl border border-[var(--amber-ink)]/30 bg-[var(--amber-bg)] p-3 text-[13px] text-[var(--amber-ink)]">
          Trí nhớ đang <strong>tắt</strong>. Những gì bên dưới là phần đã ghi từ
          trước, và sẽ không có gì được ghi thêm.
        </p>
      )}

      {!ready ? (
        <P className="mt-5">Đang đọc…</P>
      ) : nodes.length === 0 ? (
        <P className="mt-5">
          Chưa có gì cả. Trò chuyện thêm vài lần rồi quay lại đây nhé.
        </P>
      ) : (
        <>
          <section className="mt-5">
            <h2 className="text-[13px] font-semibold">Chủ đề bạn hay nhắc tới</h2>
            <ul className="mt-2 flex flex-col gap-1.5">
              {nodes.map((n) => (
                <li
                  key={n.node_id}
                  className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-2.5"
                >
                  <div className="flex items-baseline justify-between gap-3">
                    <span className="text-[14px]">{ten(n.node_id)}</span>
                    <span className="shrink-0 text-[11px] text-[var(--muted)]">
                      {n.observations} lần · {khiNao(n.last_seen)}
                    </span>
                  </div>
                  {n.verbatim && (
                    <p className="mt-1 text-[13px] text-[var(--muted)] italic">
                      &ldquo;{n.verbatim}&rdquo;
                    </p>
                  )}
                  <div
                    className="mt-1.5 h-1 w-full overflow-hidden rounded-full bg-[var(--border)]"
                    role="img"
                    aria-label={`Mức độ ${Math.round(Number(n.confidence) * 100)}%`}
                  >
                    <div
                      className="h-full rounded-full bg-[var(--accent)]"
                      style={{ width: `${Math.round(Number(n.confidence) * 100)}%` }}
                    />
                  </div>
                </li>
              ))}
            </ul>
          </section>

          {edges.length > 0 && (
            <section className="mt-5">
              <h2 className="text-[13px] font-semibold">Những điều thường đi cùng nhau</h2>
              <ul className="mt-2 flex flex-col gap-1">
                {edges.map((e) => (
                  <li
                    key={`${e.from_node}-${e.to_node}`}
                    className="flex items-baseline justify-between gap-3 rounded-lg px-2.5 py-1.5 text-[13px] odd:bg-[var(--surface)]"
                  >
                    <span>
                      {ten(e.from_node)} <span className="text-[var(--muted)]">↔</span>{" "}
                      {ten(e.to_node)}
                    </span>
                    <span className="shrink-0 text-[11px] text-[var(--muted)]">
                      {e.weight} lần
                    </span>
                  </li>
                ))}
              </ul>
            </section>
          )}
        </>
      )}

      <div className="mt-6 flex flex-col gap-2 border-t border-[var(--border)] pt-4">
        <p className="text-[12px] leading-relaxed text-[var(--muted)]">
          Xoá là mất hẳn, không khôi phục được. Có hai mức:
        </p>
        {nodes.some((n) => n.verbatim) && !xoaXong && (
          <button
            type="button"
            onClick={async () => {
              await forgetQuotes();
              setNodes((prev) => prev.map((n) => ({ ...n, verbatim: null })));
              setXoaXong(true);
            }}
            className="self-start rounded-xl border border-[var(--border)] px-3 py-1.5 text-[13px] hover:bg-black/5"
          >
            Xoá những câu mình đã viết, giữ lại chủ đề
          </button>
        )}
        {xoaXong && (
          <p className="text-[12px] text-[var(--muted)]">Đã xoá phần câu chữ.</p>
        )}
        <p className="text-[12px] leading-relaxed text-[var(--muted)]">
          Muốn xoá sạch mọi thứ thì bấm <strong>“Quên tôi đi”</strong> ở chân
          thanh bên trái màn hình trò chuyện.
        </p>
      </div>
    </Khung>
  );
}

/** "hôm nay" / "3 ngày trước" / "12/09" */
function khiNao(iso: string): string {
  const d = new Date(iso);
  const ngay = Math.floor((Date.now() - d.getTime()) / 86_400_000);
  if (ngay <= 0) return "hôm nay";
  if (ngay === 1) return "hôm qua";
  if (ngay < 30) return `${ngay} ngày trước`;
  return `${String(d.getDate()).padStart(2, "0")}/${String(d.getMonth() + 1).padStart(2, "0")}`;
}

function Khung({ children }: { children: React.ReactNode }) {
  return (
    <PageShell title="Bộ nhớ của mình">
      <main className="mx-auto w-full max-w-lg px-5 py-6">
        {children}
        <div className="mt-6">
          <DisclaimerBanner variant="attached" />
        </div>
      </main>
    </PageShell>
  );
}

function P({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <p className={`text-[13px] text-[var(--muted)] ${className}`}>{children}</p>;
}
