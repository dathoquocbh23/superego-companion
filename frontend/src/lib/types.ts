import { z } from "zod";

// ── Loại message & dispatch (docx/07 §3) ──────────────────────────────────
export const messageTypeSchema = z.enum([
  "USER",
  "REFLECT",
  "INSIGHT_CARD",
  "KNOWLEDGE_CARD",
  "COPING_CARD",
  "BRIDGE_CARD",
  "CRISIS_CARD",
]);
export type MessageType = z.infer<typeof messageTypeSchema>;

/**
 * Payload thẻ — giữ lỏng (mọi trường .nullish()) vì backend gửi shape khác nhau
 * theo từng loại card (xem app/pipeline/runner.py):
 *   CRISIS_CARD   { markdown, phone }
 *   INSIGHT_CARD  { lines[], closing }
 *   COPING/KNOWLEDGE { lead, title, body, action?, source }
 *   BRIDGE_CARD   { lead, title, body, source }
 */
export const cardSchema = z
  .object({
    type: z.string(),
    markdown: z.string().nullish(),
    phone: z.string().nullish(),
    lines: z.array(z.string()).nullish(),
    closing: z.string().nullish(),
    lead: z.string().nullish(),
    title: z.string().nullish(),
    body: z.string().nullish(),
    action: z.string().nullish(),
    source: z.string().nullish(),
  })
  .passthrough();
export type Card = z.infer<typeof cardSchema>;

export const chatMessageSchema = z.object({
  id: z.string(),
  role: z.enum(["user", "assistant"]),
  messageType: messageTypeSchema,
  content: z.string(),
  card: cardSchema.nullish(),
  quickReplies: z.array(z.string()).nullish(),
  createdAt: z.number(),
});
export type ChatMessage = z.infer<typeof chatMessageSchema>;

// ── SSE events (docx/06 §2.4) ────────────────────────────────────────────
export type SseEvent =
  | { event: "meta"; data: { gate: string; message_type: string } }
  | { event: "token"; data: { t: string } }
  | { event: "card"; data: Card }
  | { event: "footer"; data: { quickReplies: string[]; turn_id: number; crisis?: boolean } }
  | { event: "done"; data: Record<string, never> };

// ── Assessment (docx/06 §2.2–§2.3) ──────────────────────────────────────
export const assessmentSpecSchema = z.object({
  scale: z.array(z.object({ value: z.number(), label: z.string() })),
  items: z.array(z.object({ id: z.number(), node_id: z.string(), text: z.string() })),
  disclaimer: z.string(),
});
export type AssessmentSpec = z.infer<typeof assessmentSpecSchema>;

export const assessmentResultSchema = z.object({
  total: z.number(),
  average: z.number(),
  band: z.enum(["THAP", "NHE", "DANG_CHU_Y", "CAO"]),
  band_label: z.string(),
  headline: z.string(),
  result_text: z.string(),
  next_actions: z.array(z.object({ label: z.string(), href: z.string() })),
  disclaimer: z.string(),
});
export type AssessmentResult = z.infer<typeof assessmentResultSchema>;
