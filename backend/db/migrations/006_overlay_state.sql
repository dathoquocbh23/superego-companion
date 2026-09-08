-- ============================================================================
-- 006_overlay_state.sql — OVERLAY TRÊN SUPABASE (thay Redis khi cần)
-- Dán vào Supabase SQL Editor → Run. Chạy SAU 005_anon_auth.sql.
--
-- BỐI CẢNH — chuẩn bị deploy Render free tier:
--   Overlay (bằng chứng + lịch sử một phiên, app/overlay/model.py) trước giờ
--   sống trên Redis, TTL 24h. Free tier Render không có Redis cục bộ; không
--   trỏ REDIS_URL sang một dịch vụ ngoài thì code tự rơi về RAM trong tiến
--   trình — ÂM THẦM, không lỗi hiển thị — và mỗi lần container khởi động lại
--   (deploy mới, hoặc rảnh rồi tự ngủ/thức) mọi phiên đang nói dở QUÊN SẠCH.
--
--   Thay vì bắt người dùng đăng ký thêm một dịch vụ Redis ngoài, dùng luôn
--   Supabase đã có sẵn. Đổi lấy: overlay get()/save() giờ là HTTP round-trip
--   thay vì Redis TCP — chậm hơn vài chục đến ~100ms/lượt. Chấp nhận được vì
--   lời gọi LLM đã chiếm 1.5-2s mỗi lượt; xem app/overlay/supabase_store.py.
--
--   Bật bằng OVERLAY_BACKEND=supabase (mặc định vẫn "redis" — không phá vỡ
--   cấu hình đang chạy cục bộ).
--
-- ⚠️ KHÔNG có ràng buộc TTL ở DB. Bảng KHÔNG tự xoá dòng theo thời gian như
--    Redis `EX` — hết hạn được kiểm ở TẦNG CLIENT (so `updated_at` với
--    OVERLAY_TTL_SECONDS lúc đọc). Dòng cũ vẫn nằm lại trên bảng; dọn định kỳ
--    ở mục C bên dưới.
-- ============================================================================

create table if not exists public.overlay_state (
  session_id  text primary key,
  data        jsonb not null,
  updated_at  timestamptz not null default now()
);

-- ── A. updated_at tự động khi UPDATE (upsert qua on_conflict là UPDATE) ────
--     touch_updated_at() đã tạo ở 001_init.sql — dùng lại, không tạo hàm mới.
drop trigger if exists overlay_state_touch on public.overlay_state;
create trigger overlay_state_touch
  before update on public.overlay_state
  for each row execute function public.touch_updated_at();

-- ── B. RLS — CHỈ service_role đọc/ghi ──────────────────────────────────────
--     Giống turn_logs: không policy nào cho anon/authenticated. Overlay là
--     trạng thái NỘI BỘ của pipeline, không phải thứ người dùng tự đọc qua
--     PostgREST — họ thấy nó gián tiếp qua chính cuộc trò chuyện.
alter table public.overlay_state enable row level security;

-- ── C. Dọn dòng cũ (chạy tay định kỳ, hoặc gắn pg_cron) ────────────────────
--     Cửa sổ 7 ngày — RỘNG HƠN NHIỀU so với TTL 24h thật (OVERLAY_TTL_SECONDS)
--     để còn dư thời gian debug một phiên vừa "hết hạn" mà không vội xoá.
--
-- delete from public.overlay_state
--  where updated_at < now() - interval '7 days';
