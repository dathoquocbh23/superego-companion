"use client";

import { useEffect } from "react";

import { BrandMark } from "@/components/app-shell";
import { pingBackend } from "@/lib/api";

/**
 * Logo "Góc Hiểu Mình" bấm được. Vừa mount đã gửi một ping đánh thức backend (Render
 * free tier ngủ sau ~15 phút, mất ~50s để dậy), và bấm vào dấu + thì ping thêm
 * lần nữa — hữu ích khi người dùng ngồi ở trang chủ / trang đăng nhập một lúc
 * rồi mới vào trò chuyện.
 */
export function BrandPing({ className }: { className?: string }) {
  useEffect(() => {
    pingBackend();
  }, []);

  return (
    <BrandMark
      className={className}
      onClick={pingBackend}
      title="Đánh thức máy chủ cho phản hồi nhanh hơn"
    />
  );
}
