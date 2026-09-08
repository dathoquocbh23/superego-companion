-- ============================================================================
-- 004_verbatim.sql — BỘ NHỚ NHỚ ĐƯỢC CẢ CÂU CHỮ
-- Dán vào Supabase SQL Editor → Run. Chạy SAU 003_consent.sql.
--
-- ⚠️ ĐÂY LÀ THAY ĐỔI VỀ RIÊNG TƯ, KHÔNG PHẢI THAY ĐỔI KỸ THUẬT.
--    Trước file này, bộ nhớ chỉ có trọng số node — "hay nhắc tới chuyện điểm
--    số", không có "6.5". Sau file này, nguyên văn câu học sinh viết được lưu
--    lại để bot nhớ được chi tiết thật. Xem docx/12 §2 (đã viết lại).
--
--    Bù lại bằng 4 hàng rào, tất cả đều nằm ở DB chứ không chỉ ở tầng Python:
--      1. CHỈ lưu verbatim của nguồn NGƯỜI DÙNG TỰ NÓI
--         (SELF_REPORT / LIKERT / CONFIRMED). INFERRED — câu LLM tự suy ra —
--         KHÔNG BAO GIỜ được lưu như thể học sinh đã nói vậy.
--      2. Giới hạn 200 ký tự / câu. Bộ nhớ là mẩu trích, không phải transcript.
--      3. Xoá riêng được câu chữ mà vẫn giữ chủ đề — `xoa_nguyen_van()`.
--      4. Hiện nguyên văn trên trang /memory để học sinh thấy đúng cái đang giữ.
-- ============================================================================

alter table public.user_memory
  add column if not exists verbatim    text,
  add column if not exists verbatim_at timestamptz;

alter table public.user_memory_events
  add column if not exists verbatim text;

comment on column public.user_memory.verbatim is
  'Nguyên văn GẦN NHẤT của học sinh cho node này. NULL nếu chưa có hoặc đã xoá riêng.';

-- Bộ nhớ là mẩu trích chứ không phải transcript. Cắt ở DB để tầng nào gọi vào
-- cũng bị cắt như nhau.
alter table public.user_memory
  drop constraint if exists user_memory_verbatim_ngan;
alter table public.user_memory
  add constraint user_memory_verbatim_ngan
  check (verbatim is null or char_length(verbatim) <= 200);

-- ── ghi_nho_luot: nhận thêm verbatim ──────────────────────────────────
--    p_nodes: [{"node_id", "confidence", "source", "verbatim"}]
create or replace function public.ghi_nho_luot(
  p_user_id      uuid,
  p_session_hash text,
  p_turn_id      int,
  p_nodes        jsonb
)
returns void
language plpgsql
security definer
set search_path = public
as $$
declare
  v_ids text[];
begin
  if not exists (
    select 1 from public.app_users
     where id = p_user_id and memory_enabled
  ) then
    return;
  end if;

  -- 1) Trọng số node + nguyên văn.
  --    HÀNG RÀO 1: chỉ nguồn người dùng tự nói mới được giữ câu chữ.
  --    HÀNG RÀO 2: cắt 200 ký tự.
  --    Verbatim rỗng thì GIỮ câu cũ (coalesce) — lượt sau không nhắc lại thì
  --    không có nghĩa là câu cũ sai.
  insert into public.user_memory as m
        (user_id, node_id, confidence, observations, verbatim, verbatim_at)
  select p_user_id,
         n ->> 'node_id',
         least(1.0, greatest(0.0, (n ->> 'confidence')::numeric)),
         1,
         nullif(left(case
           when n ->> 'source' in ('SELF_REPORT', 'LIKERT', 'CONFIRMED')
           then coalesce(n ->> 'verbatim', '') else '' end, 200), ''),
         case when n ->> 'source' in ('SELF_REPORT', 'LIKERT', 'CONFIRMED')
              and coalesce(n ->> 'verbatim', '') <> '' then now() end
    from jsonb_array_elements(p_nodes) n
  on conflict (user_id, node_id) do update
     set confidence   = round(0.6 * m.confidence + 0.4 * excluded.confidence, 2),
         observations = m.observations + 1,
         last_seen    = now(),
         verbatim     = coalesce(excluded.verbatim, m.verbatim),
         verbatim_at  = coalesce(excluded.verbatim_at, m.verbatim_at);

  -- 2) Trọng số cạnh.
  select array_agg(distinct n ->> 'node_id' order by n ->> 'node_id')
    into v_ids
    from jsonb_array_elements(p_nodes) n;

  if array_length(v_ids, 1) >= 2 then
    insert into public.user_memory_edges as e (user_id, from_node, to_node)
    select p_user_id, a, b
      from unnest(v_ids) a, unnest(v_ids) b
     where a < b
    on conflict (user_id, from_node, to_node) do update
       set weight = e.weight + 1, last_seen = now();
  end if;

  -- 3) Nhật ký — cùng hàng rào nguồn.
  insert into public.user_memory_events
        (user_id, session_hash, node_id, confidence, source, turn_id, verbatim)
  select p_user_id, p_session_hash, n ->> 'node_id',
         least(1.0, greatest(0.0, (n ->> 'confidence')::numeric)),
         coalesce(n ->> 'source', 'INFERRED'), p_turn_id,
         nullif(left(case
           when n ->> 'source' in ('SELF_REPORT', 'LIKERT', 'CONFIRMED')
           then coalesce(n ->> 'verbatim', '') else '' end, 200), '')
    from jsonb_array_elements(p_nodes) n;
end $$;

revoke all on function public.ghi_nho_luot(uuid, text, int, jsonb) from public;
grant execute on function public.ghi_nho_luot(uuid, text, int, jsonb) to service_role;

-- ── HÀNG RÀO 3: xoá riêng câu chữ, GIỮ chủ đề ─────────────────────────
--    Tách khỏi quen_toi_di() có chủ ý. "Đừng nhắc lại lời tôi nói nữa" và
--    "quên sạch tôi đi" là hai mong muốn khác nhau; gộp một nút thì người ta
--    phải chọn tất-hoặc-không và thường sẽ không chọn gì.
create or replace function public.xoa_nguyen_van()
returns void
language plpgsql
security definer
set search_path = public
as $$
begin
  update public.user_memory
     set verbatim = null, verbatim_at = null
   where user_id = auth.uid();
  update public.user_memory_events
     set verbatim = null
   where user_id = auth.uid();
end $$;

revoke all on function public.xoa_nguyen_van() from public;
grant execute on function public.xoa_nguyen_van() to authenticated;
