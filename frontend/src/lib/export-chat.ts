import type { ChatMessage } from "./types";

/**
 * Tải hội thoại về máy dạng .txt. Chạy hoàn toàn ở client — không có bản sao
 * nào đi qua server, đúng cam kết "lịch sử chỉ nằm trên máy này".
 */
export function exportChat(title: string, messages: ChatMessage[]): void {
  const body = messages
    .filter((m) => m.content.trim())
    .map((m) => `${m.role === "user" ? "Bạn" : "Trợ lý"}: ${m.content.trim()}`)
    .join("\n\n");

  const header = [
    title,
    new Date().toLocaleString("vi-VN"),
    "Sản phẩm demo học thuật — không thay thế tư vấn tâm lý.",
    "",
  ].join("\n");

  const url = URL.createObjectURL(new Blob([`${header}\n${body}\n`], { type: "text/plain;charset=utf-8" }));
  const a = document.createElement("a");
  a.href = url;
  a.download = `hoi-thoai-${new Date().toISOString().slice(0, 10)}.txt`;
  a.click();
  URL.revokeObjectURL(url);
}
