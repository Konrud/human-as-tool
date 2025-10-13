import { z } from "zod";

export const MessageTypeSchema = z.enum(["user", "agent", "system"]);

export const MessageStatusSchema = z.enum(["sent", "delivered", "read", "failed"]);

export const MessageMetadataSchema = z.object({
  streamingComplete: z.boolean().optional(),
  errorCount: z.number().int().min(0).optional(),
  retryTimestamp: z.coerce.date().optional(),
});

export const MessageSchema = z.object({
  id: z.string().uuid(),
  sessionId: z.string().uuid(),
  content: z.string().min(1, "Message content cannot be empty"),
  type: MessageTypeSchema,
  timestamp: z.coerce
    .date()
    .refine((date) => date <= new Date(), "Timestamp cannot be in the future"),
  status: MessageStatusSchema,
  channel: z.enum(["websocket", "email", "slack"]),
  metadata: MessageMetadataSchema.optional(),
});

export type MessageType = z.infer<typeof MessageTypeSchema>;
export type MessageStatus = z.infer<typeof MessageStatusSchema>;
export type Message = z.infer<typeof MessageSchema>;
export type MessageMetadata = z.infer<typeof MessageMetadataSchema>;
