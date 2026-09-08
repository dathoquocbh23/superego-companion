-- ============================================================================
-- 005_anon_auth.sql — HỖ TRỢ TÀI KHOẢN ẨN DANH
-- Dán vào Supabase SQL Editor → Run. Chạy SAU 004_verbatim.sql.
--
-- ⚠️ TRƯỚC KHI CHẠY FILE NÀY, BẬT TRONG DASHBOARD:
--       Authentication → Providers → Anonymous sign-ins → Enable
--    Không bật thì nút "Vào thử ngay" ở trang đăng nhập trả lỗi
--    `anonymous_provider_disabled` (frontend có bắt và báo cho người dùng).
--
-- BỐI CẢNH — ĐỔI LUẬT 07/09/2026:
--   Trước: đăng nhập là TUỲ CHỌN; phiên không đăng nhập có user_id = NULL.
--   Sau:   đăng nhập BẮT BUỘC. "Ẩn danh" giờ nghĩa là TÀI KHOẢN ẨN DANH của
--          Supabase — hàng thật trong auth.users, có UUID, chưa gắn email.
--
--   Vì sao: dự án bắt đầu lưu nguyên văn hội thoại (bảng messages) phục vụ
--   nghiên cứu. Dữ liệu user_id = NULL thì không xoá theo yêu cầu được, không
--   áp RLS được, và không gắn được cơ sở đồng ý nào. Tài khoản ẩn danh giữ
--   nguyên trải nghiệm "không phải khai gì" mà vẫn cho dữ liệu một người chủ.
--
--   Người dùng nâng cấp lên tài khoản email sau (auth.updateUser) thì GIỮ
--   NGUYÊN UUID — toàn bộ user_memory, conversations, messages đi theo, không
--   cần di trú gì.
-- ============================================================================

-- ── A. display_name không được vỡ khi email là NULL ───────────────────────
--     Bản cũ: coalesce(meta->>'display_name', split_part(new.email,'@',1)).
--     Với tài khoản ẩn danh, new.email là NULL → split_part(NULL,…) ra NULL →
--     display_name NULL. Không lỗi, nhưng mọi chỗ hiển thị tên phải tự đoán.
create or replace function public.handle_new_user()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  insert into public.app_users (id, display_name)
  values (
    new.id,
    coalesce(
      new.raw_user_meta_data ->> 'display_name',
      nullif(split_part(coalesce(new.email, ''), '@', 1), ''),
      'Bạn'                      -- tài khoản ẩn danh: chưa có gì để gọi tên
    )
  )
  on conflict (id) do nothing;
  return new;
end $$;

-- Trigger đã tạo ở 002_memory.sql; create or replace function là đủ.

-- ── B. Vá hồ sơ đã lỡ tạo với display_name rỗng ──────────────────────────
update public.app_users set display_name = 'Bạn'
 where display_name is null or btrim(display_name) = '';

-- ── C. Dọn tài khoản ẩn danh bỏ hoang ────────────────────────────────────
--     Tài khoản ẩn danh sinh ra mỗi lần có người bấm "Vào thử ngay" trên một
--     máy mới. Không dọn thì auth.users phình mãi bằng những hàng không ai
--     quay lại. Supabase KHÔNG tự dọn.
--
--     Chạy tay định kỳ, hoặc gắn pg_cron. Cố ý để dạng comment: xoá người dùng
--     là việc không nên tự chạy lần đầu mà không đọc.
--
--     Điều kiện: ẩn danh, tạo > 30 ngày, và KHÔNG có hội thoại nào.
--     on delete cascade sẽ kéo theo app_users / user_memory / conversations.
--
-- delete from auth.users u
--  where u.is_anonymous
--    and u.created_at < now() - interval '30 days'
--    and not exists (select 1 from public.conversations c where c.user_id = u.id);

-- ── D. Cửa sổ lưu trữ transcript (tuỳ bạn bật) ───────────────────────────
--     Đã bàn 07/09/2026: dự án chọn ghi transcript cho MỌI phiên. Đây là cái
--     van đi kèm — giữ dữ liệu nghiên cứu trong một khoảng có hạn thay vì mãi
--     mãi. Chưa bật; bật hay không là quyết định của chủ đề tài.
--
-- delete from public.conversations
--  where updated_at < now() - interval '180 days';
