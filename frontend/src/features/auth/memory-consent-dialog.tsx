"use client";

import { useEffect, useRef, useState } from "react";
import { Brain, X } from "lucide-react";

/**
 * Đổi chuỗi này khi nội dung đồng ý thay đổi — bản cũ sẽ cần XIN LẠI.
 *
 * v1 → v2 (07/09/2026): bộ nhớ bắt đầu lưu NGUYÊN VĂN câu người dùng viết.
 * Ai đồng ý ở v1 đã đồng ý cho một thứ khác hẳn (chỉ lưu chủ đề), nên đồng ý
 * đó KHÔNG còn giá trị — `use-auth.ts` coi như chưa bật cho tới khi hỏi lại.
 */
export const CONSENT_VERSION = "2026-09-07.v2";

/**
 * Popup xin đồng ý trước khi bật bộ nhớ dài hạn.
 *
 * Không phải thủ tục cho có. Nghị định 13/2023/NĐ-CP xếp dữ liệu sức khoẻ tâm
 * thần vào nhóm NHẠY CẢM, và chủ thể dưới 16 tuổi cần đồng ý của cha mẹ/người
 * giám hộ — đối tượng của sản phẩm là học sinh THPT nên chắc chắn có nhóm đó.
 * Xem docx/12 §7.
 *
 * Ràng buộc thật nằm ở DB (CHECK constraint + RPC `bat_bo_nho` trong
 * 003_consent.sql). Popup này là mặt người dùng của cùng một luật, không phải
 * lớp bảo vệ duy nhất.
 */
export function MemoryConsentDialog({
  open,
  onCancel,
  onAccept,
}: {
  open: boolean;
  onCancel: () => void;
  onAccept: (duoi16: boolean, guardianConsent: boolean) => void;
}) {
  const [duoi16, setDuoi16] = useState<boolean | null>(null);
  const [guardian, setGuardian] = useState(false);
  const [busy, setBusy] = useState(false);
  const closeRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!open) {
      setDuoi16(null);
      setGuardian(false);
      setBusy(false);
      return;
    }
    closeRef.current?.focus();
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onCancel();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onCancel]);

  if (!open) return null;

  // Dưới 16 mà chưa xác nhận có người lớn đồng ý thì KHÔNG cho bật.
  const duocBat = duoi16 !== null && (duoi16 === false || guardian);

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center sm:items-center">
      <button
        type="button"
        aria-label="Đóng"
        onClick={onCancel}
        className="absolute inset-0 bg-black/40"
      />

      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="consent-title"
        className="relative max-h-[90dvh] w-full max-w-lg overflow-y-auto rounded-t-2xl bg-[var(--surface)] p-5 shadow-xl sm:rounded-2xl"
      >
        <div className="flex items-start justify-between gap-3">
          <h2 id="consent-title" className="flex items-center gap-2 text-base font-semibold">
            <Brain className="size-4 text-[var(--accent)]" aria-hidden />
            Cho phép mình nhớ bạn giữa các lần trò chuyện?
          </h2>
          <button
            ref={closeRef}
            type="button"
            onClick={onCancel}
            aria-label="Đóng"
            className="grid size-8 shrink-0 place-items-center rounded-lg text-[var(--muted)] hover:bg-black/5"
          >
            <X className="size-4" />
          </button>
        </div>

        <div className="mt-4 flex flex-col gap-3 text-[13px] leading-relaxed">
          <div className="rounded-xl border border-[var(--border)] bg-[var(--bg)] p-3">
            <p className="font-medium">Mình sẽ nhớ</p>
            <ul className="mt-1 list-disc pl-4 text-[var(--muted)]">
              <li>Những chủ đề bạn hay nhắc tới, và mức độ hay nhắc</li>
              <li>Các chủ đề nào thường đi cùng nhau ở bạn</li>
              <li>
                <strong className="text-[var(--text)]">
                  Một số câu bạn viết, giữ nguyên chữ
                </strong>{" "}
                — để lần sau mình nhớ đúng chuyện đã xảy ra, ví dụ “thi được 6.5”.
                Mỗi chủ đề giữ một câu, tối đa 200 ký tự.
              </li>
            </ul>
          </div>

          <div className="rounded-xl border border-[var(--border)] bg-[var(--bg)] p-3">
            <p className="font-medium">Mình KHÔNG lưu</p>
            <ul className="mt-1 list-disc pl-4 text-[var(--muted)]">
              <li>Toàn bộ đoạn chat — chỉ vài câu lẻ, không phải cả cuộc trò chuyện</li>
              <li>
                Những câu bạn <em>tự chê mình</em>. Mình không giữ lại và không
                bao giờ đọc lại cho bạn nghe — bạn của hôm nay không phải bạn
                của hôm đó.
              </li>
            </ul>
          </div>

          <p className="text-[var(--muted)]">
            Trí nhớ này <strong className="font-medium text-[var(--text)]">mờ dần theo thời gian</strong> — chủ đề
            không được nhắc lại khoảng hai tháng rưỡi sẽ tự biến mất.
          </p>

          <p className="text-[var(--muted)]">
            Bạn xem được chính xác từng câu mình đang giữ ở trang “Mình đang nhớ
            gì về bạn”, và xoá riêng phần câu chữ mà vẫn giữ chủ đề, hoặc xoá
            sạch mọi thứ.
          </p>

          {/* Tuổi — bắt buộc theo NĐ 13/2023 */}
          <fieldset className="rounded-xl border border-[var(--amber-ink)]/30 bg-[var(--amber-bg)] p-3">
            <legend className="px-1 text-[12px] font-medium text-[var(--amber-ink)]">
              Bạn bao nhiêu tuổi?
            </legend>
            <div className="mt-1 flex flex-col gap-1.5">
              <label className="flex cursor-pointer items-center gap-2">
                <input
                  type="radio"
                  name="tuoi"
                  checked={duoi16 === false}
                  onChange={() => setDuoi16(false)}
                  className="size-3.5 accent-[var(--accent)]"
                />
                <span>Từ 16 tuổi trở lên</span>
              </label>
              <label className="flex cursor-pointer items-center gap-2">
                <input
                  type="radio"
                  name="tuoi"
                  checked={duoi16 === true}
                  onChange={() => setDuoi16(true)}
                  className="size-3.5 accent-[var(--accent)]"
                />
                <span>Dưới 16 tuổi</span>
              </label>
            </div>

            {duoi16 === true && (
              <label className="mt-2.5 flex cursor-pointer items-start gap-2 border-t border-[var(--amber-ink)]/20 pt-2.5">
                <input
                  type="checkbox"
                  checked={guardian}
                  onChange={(e) => setGuardian(e.target.checked)}
                  className="mt-0.5 size-3.5 shrink-0 accent-[var(--accent)]"
                />
                <span className="text-[var(--amber-ink)]">
                  Mình đã hỏi và cha mẹ / người giám hộ đồng ý cho mình bật tính
                  năng này.
                </span>
              </label>
            )}
          </fieldset>
        </div>

        <div className="mt-4 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
          <button
            type="button"
            onClick={onCancel}
            className="rounded-xl border border-[var(--border)] px-4 py-2 text-sm hover:bg-black/5"
          >
            Không, cảm ơn
          </button>
          <button
            type="button"
            disabled={!duocBat || busy}
            onClick={() => {
              setBusy(true);
              onAccept(duoi16 === true, guardian);
            }}
            className="rounded-xl bg-[var(--accent)] px-4 py-2 text-sm font-medium text-white disabled:opacity-40"
          >
            {busy ? "Đang bật…" : "Đồng ý, bật trí nhớ"}
          </button>
        </div>

        <p className="mt-3 text-[11px] leading-snug text-[var(--muted)]">
          Không bật thì mọi thứ vẫn dùng bình thường — mỗi lần trò chuyện là một
          lần mới, không có gì được lưu lại.
        </p>
      </div>
    </div>
  );
}
