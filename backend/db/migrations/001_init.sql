-- ============================================================================
-- 001_init.sql — schema nền cho chatbot NCKH
-- Dán vào Supabase SQL Editor → Run. Chạy lại nhiều lần không sao.
-- Chạy file này TRƯỚC 002_memory.sql.
--
-- ⚠️ ĐỌC TRƯỚC KHI CHẠY — bảng `messages` lưu NGUYÊN VĂN lời người dùng.
--    Trái với 2 quyết định đã ghi trong dự án:
--      - app/telemetry/log.py: "KHÔNG BAO GIỜ ghi user_message, verbatim,
--        response_text, session_id gốc, PII"
--      - docx/03 §8: không lưu overlay ra file/DB ở giai đoạn demo
--    Nếu chỉ cần số liệu cho bài báo: chạy riêng phần D (turn_logs) là đủ.
--    Nếu chỉ cần sidebar: localStorage hiện tại đã đủ, không cần bảng nào.
-- ============================================================================

create extension if not exists "pgcrypto";

-- ── A. Phiên hội thoại ──────────────────────────────────────────────────
create table if not exists public.conversations (
  id          uuid primary key default gen_random_uuid(),
  session_id  uuid not null unique,          -- session_id từ POST /api/session
  user_id     uuid references auth.users(id) on delete cascade,  -- null = phiên ẩn danh
  title       text not null default 'Cuộc trò chuyện mới',
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);
create index if not exists conversations_user_idx
  on public.conversations (user_id, updated_at desc);

-- ── B. Tin nhắn ─────────────────────────────────────────────────────────
create table if not exists public.messages (
  id              bigint generated always as identity primary key,
  conversation_id uuid not null references public.conversations(id) on delete cascade,
  turn_id         int,
  role            text not null check (role in ('user', 'assistant')),
  message_type    text not null check (message_type in
                    ('USER', 'REFLECT', 'INSIGHT_CARD', 'KNOWLEDGE_CARD',
                     'COPING_CARD', 'BRIDGE_CARD', 'CRISIS_CARD')),
  content         text not null default '',
  card            jsonb,
  quick_replies   text[],
  created_at      timestamptz not null default now()
);
create index if not exists messages_conversation_idx
  on public.messages (conversation_id, id);

-- ── C. Kết quả thang đo Likert (10 mục) ────────────────────────────────
create table if not exists public.assessment_results (
  id          bigint generated always as identity primary key,
  session_id  uuid not null,
  user_id     uuid references auth.users(id) on delete cascade,
  total       int  not null,
  average     numeric(4, 2) not null,
  band        text not null check (band in ('THAP', 'NHE', 'DANG_CHU_Y', 'CAO')),
  answers     jsonb not null,               -- {"1": 3, "2": 5, ...}
  created_at  timestamptz not null default now()
);
create index if not exists assessment_session_idx
  on public.assessment_results (session_id);
create index if not exists assessment_user_idx
  on public.assessment_results (user_id, created_at desc);

-- ── D. Telemetry mỗi lượt — KHÔNG PII, KHÔNG user_id ───────────────────
--     Khớp 1-1 với build_record() trong app/telemetry/log.py.
--     Cố tình KHÔNG có user_id: đây là số liệu nghiên cứu, phải không truy
--     ngược được về cá nhân. session_hash = sha256(session_id)[:6].
create table if not exists public.turn_logs (
  id                   bigint generated always as identity primary key,
  session_hash         text not null,
  turn_id              int  not null,
  ts                   timestamptz not null default now(),

  safety_tier          int,
  safety_matched       text[],

  input_len            int,
  input_is_chip        boolean,
  chip_type            text,

  extracted            jsonb,                -- [{node_id, confidence}]
  extract_failed       boolean,
  extract_hallucinated text[],

  overlay_size         int,
  overlay_by_source    jsonb,
  active_cycles        text[],

  gate                 text,
  gate_reason          text,
  target_nodes         text[],
  policy_edge_used     text,

  message_type         text,
  response_len         int,
  response_sentences   int,
  postcheck_flags      text[],
  chip_provenance      jsonb,

  latency_ms           jsonb,
  tokens               jsonb,
  flags                text[]
);
create index if not exists turn_logs_session_idx
  on public.turn_logs (session_hash, turn_id);
create index if not exists turn_logs_gate_idx
  on public.turn_logs (gate, ts);

-- ── E. updated_at tự động ──────────────────────────────────────────────
create or replace function public.touch_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end $$;

drop trigger if exists conversations_touch on public.conversations;
create trigger conversations_touch
  before update on public.conversations
  for each row execute function public.touch_updated_at();

-- ── F. RLS ─────────────────────────────────────────────────────────────
--     Có đăng nhập rồi nên viết được policy thật theo auth.uid().
--     Phiên ẩn danh (user_id is null) KHÔNG ai đọc được bằng anon key —
--     chỉ backend dùng service_role (bypass RLS) mới vào được.
--     => TUYỆT ĐỐI không đặt SUPABASE_SERVICE_ROLE_KEY vào NEXT_PUBLIC_*.
alter table public.conversations      enable row level security;
alter table public.messages           enable row level security;
alter table public.assessment_results enable row level security;
alter table public.turn_logs          enable row level security;

drop policy if exists conversations_own on public.conversations;
create policy conversations_own on public.conversations
  for all to authenticated
  using (user_id = auth.uid())
  with check (user_id = auth.uid());

drop policy if exists messages_own on public.messages;
create policy messages_own on public.messages
  for all to authenticated
  using (exists (
    select 1 from public.conversations c
    where c.id = messages.conversation_id and c.user_id = auth.uid()
  ))
  with check (exists (
    select 1 from public.conversations c
    where c.id = messages.conversation_id and c.user_id = auth.uid()
  ));

drop policy if exists assessment_own on public.assessment_results;
create policy assessment_own on public.assessment_results
  for all to authenticated
  using (user_id = auth.uid())
  with check (user_id = auth.uid());

-- turn_logs: KHÔNG policy nào. Chỉ service_role ghi/đọc được.
-- Số liệu nghiên cứu không thuộc về một tài khoản cụ thể.

-- ── G. Xoá dữ liệu quá hạn (chạy tay hoặc gắn pg_cron) ─────────────────
-- delete from public.conversations
--   where user_id is null and updated_at < now() - interval '30 days';
