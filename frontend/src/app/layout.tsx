import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Trợ lý tâm lý giáo dục",
  description:
    "Trợ lý đồng hành về cảm xúc cho học sinh THPT — nhận diện xu hướng tự phê phán quá mức. Sản phẩm demo học thuật.",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#e8e3f4",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="vi">
      <body>{children}</body>
    </html>
  );
}
