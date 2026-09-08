"use client";

import { useCallback, useEffect, useState } from "react";

import { clearCachedSession } from "@/lib/api";
import { authConfigured, getSupabase } from "@/lib/supabase";
import { CONSENT_VERSION } from "./memory-consent-dialog";

export type AuthUser = {
  id: string;
  email: string | null;
  /**
   * Tài khoản ẩn danh của Supabase — CÓ hàng thật trong auth.users, có UUID,
   * chỉ là chưa gắn email. Khác hẳn "không đăng nhập": ở đây dữ liệu VẪN có
   * chủ, nên RLS chạy được và quen_toi_di() xoá được. Nâng cấp lên tài khoản
   * email sau vẫn giữ nguyên UUID này và toàn bộ lịch sử.
   */
  isAnonymous: boolean;
};

/** Hồ sơ trong bảng app_users — cờ bật/tắt bộ nhớ dài hạn. */
export type MemoryPrefs = {
  memoryEnabled: boolean;
  /** Đã bật, nhưng đồng ý thuộc bản CŨ → phải xin lại trước khi coi là bật. */
  staleConsent: boolean;
};

/**
 * Trạng thái đăng nhập + công tắc bộ nhớ dài hạn.
 *
 * Chưa cấu hình Supabase → `configured=false`, mọi thứ khác null. Trang chat
 * phải chạy được bình thường trong trạng thái đó (docx/12 §1).
 */
export function useAuth() {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [prefs, setPrefs] = useState<MemoryPrefs | null>(null);
  const [loading, setLoading] = useState(authConfigured);

  useEffect(() => {
    const sb = getSupabase();
    if (!sb) {
      setLoading(false);
      return;
    }
    sb.auth.getSession().then(({ data }) => {
      const u = data.session?.user;
      setUser(u ? { id: u.id, email: u.email ?? null, isAnonymous: Boolean(u.is_anonymous) } : null);
      setLoading(false);
    });
    const { data: sub } = sb.auth.onAuthStateChange((_e, session) => {
      const u = session?.user;
      setUser(u ? { id: u.id, email: u.email ?? null, isAnonymous: Boolean(u.is_anonymous) } : null);
      if (!u) setPrefs(null);
      // Phiên backend được cấp THEO token. Đổi danh tính mà giữ session_id cũ
      // thì overlay vẫn mang user_id cũ (hoặc null) — transcript ghi nhầm chủ.
      clearCachedSession();
    });
    return () => sub.subscription.unsubscribe();
  }, []);

  // Đọc cờ memory_enabled. RLS lo phần "chỉ thấy hàng của mình".
  useEffect(() => {
    const sb = getSupabase();
    if (!sb || !user) return;
    let alive = true;
    sb.from("app_users")
      .select("memory_enabled, consent_version")
      .eq("id", user.id)
      .maybeSingle()
      .then(({ data }) => {
        if (!alive) return;
        // Đồng ý bản cũ KHÔNG bao trùm cách xử lý dữ liệu mới (v2 lưu nguyên
        // văn). Coi như chưa bật cho tới khi hỏi lại — đây là yêu cầu pháp lý,
        // không phải lựa chọn UX.
        const bat = Boolean(data?.memory_enabled);
        const cu = bat && data?.consent_version !== CONSENT_VERSION;
        setPrefs({ memoryEnabled: bat && !cu, staleConsent: cu });
      });
    return () => {
      alive = false;
    };
  }, [user]);

  /**
   * Bật bộ nhớ — đi qua RPC `bat_bo_nho`, KHÔNG update thẳng `memory_enabled`.
   * Bật cờ và ghi đồng ý phải nằm trong một giao dịch, nếu không sẽ có lúc cờ
   * đã bật mà chưa có bằng chứng đã xin phép (003_consent.sql §RPC).
   * DB còn có CHECK constraint chặn, nên gọi tắt cũng không qua được.
   */
  const enableMemory = useCallback(
    async (duoi16: boolean, guardianConsent: boolean): Promise<string | null> => {
      const sb = getSupabase();
      if (!sb || !user) return "Chưa đăng nhập";
      const { error } = await sb.rpc("bat_bo_nho", {
        p_duoi_16: duoi16,
        p_guardian_consent: guardianConsent,
        p_consent_version: CONSENT_VERSION,
      });
      if (error) return error.message;
      setPrefs({ memoryEnabled: true, staleConsent: false });
      return null;
    },
    [user],
  );

  /** Tắt = ngừng ghi tiếp, GIỮ dữ liệu đã có. Khác hẳn forgetMe(). */
  const disableMemory = useCallback(async () => {
    const sb = getSupabase();
    if (!sb || !user) return;
    setPrefs({ memoryEnabled: false, staleConsent: false });
    await sb.rpc("tat_bo_nho");
  }, [user]);

  /** Xoá sạch bộ nhớ dài hạn — RPC quen_toi_di() trong 002_memory.sql. */
  const forgetMe = useCallback(async () => {
    const sb = getSupabase();
    if (!sb || !user) return;
    await sb.rpc("quen_toi_di");
    setPrefs({ memoryEnabled: false, staleConsent: false });
  }, [user]);

  /** Xoá RIÊNG câu chữ, giữ lại chủ đề — RPC xoa_nguyen_van() (004_verbatim.sql). */
  const forgetQuotes = useCallback(async () => {
    const sb = getSupabase();
    if (!sb || !user) return;
    await sb.rpc("xoa_nguyen_van");
  }, [user]);

  /**
   * "Vào thử ngay" — tạo tài khoản ẩn danh thật (UUID, không email).
   *
   * Cần bật Anonymous sign-ins trong dashboard Supabase (Auth > Providers).
   * Chưa bật thì Supabase trả lỗi `anonymous_provider_disabled`; trả về chuỗi
   * lỗi để trang đăng nhập nói cho người dùng biết thay vì treo im lặng.
   */
  const signInAnonymous = useCallback(async (): Promise<string | null> => {
    const sb = getSupabase();
    if (!sb) return "Chưa cấu hình Supabase";
    const { error } = await sb.auth.signInAnonymously();
    if (!error) return null;
    if (error.message.toLowerCase().includes("anonymous")) {
      return "Chế độ dùng thử chưa được bật trên máy chủ. Bạn đăng nhập bằng email giúp mình nhé.";
    }
    return error.message;
  }, []);

  const signOut = useCallback(async () => {
    await getSupabase()?.auth.signOut();
    clearCachedSession();
  }, []);

  return {
    configured: authConfigured,
    user,
    prefs,
    loading,
    signInAnonymous,
    enableMemory,
    disableMemory,
    forgetMe,
    forgetQuotes,
    signOut,
  };
}
