-- ============================================================================
-- 002_memory.sql — đăng nhập + BỘ NHỚ DÀI HẠN THEO GRAPH
-- Dán vào Supabase SQL Editor → Run. Chạy SAU 001_init.sql.
--
-- Ý TƯỞNG CỐT LÕI: không đẻ ra cấu trúc nhớ mới.
--   Dự án đã có sẵn một graph — data/domain_graph.yaml (24 evidence node +
--   cạnh triggers/produces/impairs/reinforces). Cái thay đổi theo từng người
--   chỉ là TRỌNG SỐ trên graph đó. Nên:
--       ontology (node + cạnh)  = YAML, tĩnh, chung cho mọi người
--       bộ nhớ của một học sinh = trọng số trên node + cạnh, nằm ở đây
--   `Overlay` hiện tại chính là bộ nhớ này ở phạm vi MỘT phiên. Bảng dưới đây
--   là đúng nó, nhưng phạm vi MỘT NGƯỜI và sống qua nhiều phiên.
--
-- ⚠️ KHÔNG LƯU NGUYÊN VĂN. Bộ nhớ chỉ ghi "node nào, mạnh bao nhiêu, gặp mấy
--    lần, lần cuối khi nào" — không ghi câu học sinh đã nói. Giữ đúng luật
--    trong app/telemetry/log.py mà vẫn đủ để phiên sau hiểu người ta hơn.
-- ============================================================================

-- ── A. Hồ sơ + ĐỒNG Ý ghi nhớ ──────────────────────────────────────────
--     id chính là auth.users.id (không sinh id riêng để khỏi đồng bộ 2 nơi —
--     cùng cách app-duong-sau khoá bảng nhan_vien).
create table if not exists public.app_users (
  id              uuid primary key references auth.users(id) on delete cascade,
  display_name    text,
  -- Bộ nhớ dài hạn là OPT-IN. Mặc định TẮT.
  -- Lý do: đối tượng là học sinh THPT, nội dung là sức khoẻ tâm thần. Nhớ
  -- xuyên phiên phải là lựa chọn có ý thức, không phải mặc định im lặng.
  memory_enabled  boolean not null default false,
  memory_opt_in_at timestamptz,
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now()
);

-- ── B. BỘ NHỚ — TRỌNG SỐ NODE ──────────────────────────────────────────
--     Mỗi dòng = một node trong domain_graph.yaml, ở mức "người này".
create table if not exists public.user_memory (
  user_id      uuid not null references auth.users(id) on delete cascade,
  node_id      text not null,               -- khớp id trong domain_graph.yaml
  confidence   numeric(3, 2) not null check (confidence >= 0 and confidence <= 1),
  observations int  not null default 1,     -- số phiên/lượt đã thấy node này
  first_seen   timestamptz not null default now(),
  last_seen    timestamptz not null default now(),
  primary key (user_id, node_id)
);
create index if not exists user_memory_recent_idx
  on public.user_memory (user_id, last_seen desc);

-- ── C. BỘ NHỚ — TRỌNG SỐ CẠNH (phần "graph" thật sự) ───────────────────
--     Đếm số lần hai node cùng sáng trong một phiên của CHÍNH người này.
--     Ontology nói "về lý thuyết a-lo-lang dẫn tới i-kho-tap-trung";
--     bảng này nói "với bạn A, hai cái đó đi cùng nhau 7 lần" — đó mới là
--     mẫu hình riêng, và là thứ khiến phiên sau hiểu đúng người chứ không
--     đọc thuộc lý thuyết.
create table if not exists public.user_memory_edges (
  user_id     uuid not null references auth.users(id) on delete cascade,
  from_node   text not null,
  to_node     text not null,
  weight      int  not null default 1,
  last_seen   timestamptz not null default now(),
  primary key (user_id, from_node, to_node),
  check (from_node < to_node)               -- cặp không hướng, chuẩn hoá thứ tự
);

-- ── D. Nhật ký quan sát (append-only) ──────────────────────────────────
--     Để trả lời được câu "vì sao bot nhớ điều này về mình?" — thiếu cái này
--     thì bộ nhớ là hộp đen, học sinh không có cách nào phản bác.
create table if not exists public.user_memory_events (
  id           bigint generated always as identity primary key,
  user_id      uuid not null references auth.users(id) on delete cascade,
  session_hash text,                        -- KHÔNG phải session_id gốc
  node_id      text not null,
  confidence   numeric(3, 2) not null,
  source       text not null check (source in
                 ('LIKERT', 'SELF_REPORT', 'INFERRED', 'CONFIRMED')),
  turn_id      int,
  created_at   timestamptz not null default now()
);
create index if not exists memory_events_user_idx
  on public.user_memory_events (user_id, created_at desc);

-- ── E. updated_at ──────────────────────────────────────────────────────
drop trigger if exists app_users_touch on public.app_users;
create trigger app_users_touch
  before update on public.app_users
  for each row execute function public.touch_updated_at();

-- ── F. Tạo hồ sơ tự động khi có tài khoản mới ─────────────────────────
create or replace function public.handle_new_user()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  insert into public.app_users (id, display_name)
  values (new.id, coalesce(new.raw_user_meta_data ->> 'display_name', split_part(new.email, '@', 1)))
  on conflict (id) do nothing;
  return new;
end $$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

-- ── G. RLS — học sinh chỉ thấy bộ nhớ của chính mình ──────────────────
alter table public.app_users          enable row level security;
alter table public.user_memory        enable row level security;
alter table public.user_memory_edges  enable row level security;
alter table public.user_memory_events enable row level security;

drop policy if exists app_users_own on public.app_users;
create policy app_users_own on public.app_users
  for all to authenticated
  using (id = auth.uid()) with check (id = auth.uid());

drop policy if exists user_memory_own on public.user_memory;
create policy user_memory_own on public.user_memory
  for all to authenticated
  using (user_id = auth.uid()) with check (user_id = auth.uid());

drop policy if exists user_memory_edges_own on public.user_memory_edges;
create policy user_memory_edges_own on public.user_memory_edges
  for all to authenticated
  using (user_id = auth.uid()) with check (user_id = auth.uid());

-- events: học sinh ĐỌC được (quyền xem bot nhớ gì), nhưng KHÔNG sửa/xoá
-- từng dòng — nhật ký mà tự sửa được thì không còn là nhật ký.
-- Muốn xoá thì xoá cả bộ nhớ qua hàm quen_toi_di() bên dưới.
drop policy if exists memory_events_read_own on public.user_memory_events;
create policy memory_events_read_own on public.user_memory_events
  for select to authenticated using (user_id = auth.uid());

-- ── H. "Quên tôi đi" — xoá toàn bộ bộ nhớ dài hạn ─────────────────────
--     Bắt buộc phải có. Bộ nhớ về sức khoẻ tâm thần mà không xoá được thì
--     không được phép bật ngay từ đầu.
create or replace function public.quen_toi_di()
returns void language plpgsql security definer set search_path = public as $$
begin
  delete from public.user_memory_events where user_id = auth.uid();
  delete from public.user_memory_edges  where user_id = auth.uid();
  delete from public.user_memory        where user_id = auth.uid();
  update public.app_users
     set memory_enabled = false, memory_opt_in_at = null
   where id = auth.uid();
end $$;

revoke all on function public.quen_toi_di() from public;
grant execute on function public.quen_toi_di() to authenticated;

-- ── I. RPC ghi nhớ một lượt ────────────────────────────────────────────
--     Gộp 3 việc vào MỘT giao dịch: cập nhật trọng số node, tăng trọng số
--     cạnh cho mọi cặp node cùng sáng, và ghi nhật ký. Làm bằng 3 lời gọi
--     REST riêng thì nửa chừng lỗi là bộ nhớ lệch — cạnh có mà node không.
--
--     p_nodes: [{"node_id": "...", "confidence": 0.75, "source": "SELF_REPORT"}, ...]
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
  -- Chỉ ghi khi người dùng đã BẬT bộ nhớ. Kiểm ở đây chứ không ở tầng Python:
  -- tắt bộ nhớ mà vẫn ghi được thì cái công tắc kia là trang trí.
  if not exists (
    select 1 from public.app_users
     where id = p_user_id and memory_enabled
  ) then
    return;
  end if;

  -- 1) Trọng số node — trung bình trượt, nghiêng về quan sát cũ cho đỡ giật.
  insert into public.user_memory as m (user_id, node_id, confidence, observations)
  select p_user_id,
         n ->> 'node_id',
         least(1.0, greatest(0.0, (n ->> 'confidence')::numeric)),
         1
    from jsonb_array_elements(p_nodes) n
  on conflict (user_id, node_id) do update
     set confidence   = round(0.6 * m.confidence + 0.4 * excluded.confidence, 2),
         observations = m.observations + 1,
         last_seen    = now();

  -- 2) Trọng số cạnh — mọi cặp node cùng sáng trong lượt này.
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

  -- 3) Nhật ký.
  insert into public.user_memory_events
        (user_id, session_hash, node_id, confidence, source, turn_id)
  select p_user_id, p_session_hash, n ->> 'node_id',
         least(1.0, greatest(0.0, (n ->> 'confidence')::numeric)),
         coalesce(n ->> 'source', 'INFERRED'), p_turn_id
    from jsonb_array_elements(p_nodes) n;
end $$;

revoke all on function public.ghi_nho_luot(uuid, text, int, jsonb) from public;
grant execute on function public.ghi_nho_luot(uuid, text, int, jsonb) to service_role;
