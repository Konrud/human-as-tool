import { z } from "zod";

export const SessionStatusSchema = z.enum(["active", "paused", "ended"]);

export const ChatSessionMetadataSchema = z.object({
  userAgent: z.string(),
  ipAddress: z
    .string()
    .regex(
      /^(\d{1,3}\.){3}\d{1,3}$|^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$/,
      "Invalid IP address format"
    ),
  lastActive: z.coerce.date(),
});

export const ChatSessionSchema = z.object({
  id: z.string().uuid(),
  userId: z.string().uuid(),
  status: SessionStatusSchema,
  createdAt: z.coerce.date(),
  updatedAt: z.coerce.date(),
  preferredChannel: z.enum(["websocket", "email", "slack"]),
  messages: z.array(z.any()), // Will be refined with MessageSchema
  feedbackRequests: z.array(z.any()), // Will be refined with FeedbackRequestSchema
  metadata: ChatSessionMetadataSchema,
});

export type SessionStatus = z.infer<typeof SessionStatusSchema>;
export type ChatSession = z.infer<typeof ChatSessionSchema>;
export type ChatSessionMetadata = z.infer<typeof ChatSessionMetadataSchema>;
