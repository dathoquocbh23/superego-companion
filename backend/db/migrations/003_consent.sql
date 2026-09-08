-- ============================================================================
-- 003_consent.sql — GHI NHẬN ĐỒNG Ý trước khi bật bộ nhớ dài hạn
-- Dán vào Supabase SQL Editor → Run. Chạy SAU 002_memory.sql.
--
-- Vì sao cần: docx/12 §7 liệt kê nghĩa vụ theo Nghị định 13/2023/NĐ-CP. Dữ
-- liệu sức khoẻ tâm thần là dữ liệu nhạy cảm; chủ thể dưới 16 tuổi cần đồng ý
-- của cha mẹ/người giám hộ. Đối tượng của sản phẩm là học sinh THPT (15–18) —
-- tức là CÓ nhóm dưới 16.
--
-- ⚠️ Ràng buộc nằm ở DB, không chỉ ở UI. Popup có thể bị bỏ qua bằng cách gọi
--    thẳng PostgREST; CHECK constraint thì không.
-- ============================================================================

alter table public.app_users
  add column if not exists consent_version    text,
  add column if not exists consent_at         timestamptz,
  add column if not exists duoi_16            boolean,
  add column if not exists guardian_consent   boolean not null default false,
  add column if not exists guardian_consent_at timestamptz;

comment on column public.app_users.duoi_16 is
  'Người dùng tự khai dưới 16 tuổi. NULL = chưa hỏi.';
comment on column public.app_users.guardian_consent is
  'Đã xác nhận có đồng ý của cha mẹ/người giám hộ. Bắt buộc khi duoi_16 = true.';

-- ── Ràng buộc: KHÔNG bật được bộ nhớ nếu chưa đủ đồng ý ────────────────
--     - phải có consent_at (đã đọc và bấm đồng ý)
--     - phải đã trả lời câu hỏi tuổi
--     - dưới 16 thì phải có thêm đồng ý của người giám hộ
alter table public.app_users
  drop constraint if exists app_users_memory_can_dong_y;

alter table public.app_users
  add constraint app_users_memory_can_dong_y check (
    memory_enabled = false
    or (
      consent_at is not null
      and duoi_16 is not null
      and (duoi_16 = false or guardian_consent = true)
    )
  );

-- ── RPC bật bộ nhớ kèm đồng ý — một giao dịch ─────────────────────────
--     Bật cờ và ghi đồng ý phải đi cùng nhau. Tách ra hai lệnh PATCH thì có
--     khoảnh khắc cờ đã bật mà đồng ý chưa ghi (hoặc ngược lại) — đúng thứ
--     mà sau này không ai chứng minh được là đã xin phép hay chưa.
create or replace function public.bat_bo_nho(
  p_duoi_16          boolean,
  p_guardian_consent boolean,
  p_consent_version  text
)
returns void
language plpgsql
security definer
set search_path = public
as $$
begin
  if auth.uid() is null then
    raise exception 'chua dang nhap';
  end if;
  if p_duoi_16 and not p_guardian_consent then
    raise exception 'duoi 16 tuoi can dong y cua cha me / nguoi giam ho';
  end if;

  update public.app_users
     set duoi_16             = p_duoi_16,
         guardian_consent    = p_guardian_consent,
         guardian_consent_at = case when p_guardian_consent then now() else null end,
         consent_version     = p_consent_version,
         consent_at          = now(),
         memory_enabled      = true
   where id = auth.uid();
end $$;

revoke all on function public.bat_bo_nho(boolean, boolean, text) from public;
grant execute on function public.bat_bo_nho(boolean, boolean, text) to authenticated;

-- ── RPC tắt bộ nhớ (giữ dữ liệu đã có) ────────────────────────────────
--     Khác quen_toi_di(): tắt là NGỪNG GHI TIẾP, xoá là XOÁ HẾT. Gộp hai thứ
--     đó vào một nút thì người ta không dám bấm cái nào.
create or replace function public.tat_bo_nho()
returns void
language plpgsql
security definer
set search_path = public
as $$
begin
  update public.app_users set memory_enabled = false where id = auth.uid();
end $$;

revoke all on function public.tat_bo_nho() from public;
grant execute on function public.tat_bo_nho() to authenticated;
