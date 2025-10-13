import { z } from "zod";

export const FeedbackTypeSchema = z.enum(["approval", "input"]);

export const FeedbackStatusSchema = z.enum(["pending", "approved", "rejected", "expired"]);

export const FeedbackRequestMetadataSchema = z.object({
  priority: z.number().int().min(1).max(3),
  attemptsCount: z.number().int().min(0),
  lastAttempt: z.coerce.date(),
});

export const FeedbackRequestSchema = z
  .object({
    id: z.string().uuid(),
    sessionId: z.string().uuid(),
    type: FeedbackTypeSchema,
    status: FeedbackStatusSchema,
    prompt: z.string().min(1, "Feedback prompt cannot be empty"),
    createdAt: z.coerce.date(),
    expiresAt: z.coerce.date(),
    channels: z
      .array(z.enum(["websocket", "email", "slack"]))
      .min(1, "Must have at least one channel"),
    responses: z.array(z.any()), // Will be refined with FeedbackResponseSchema
    metadata: FeedbackRequestMetadataSchema,
  })
  .refine(
    (data) => {
      // Validate that expiresAt is 48 hours from createdAt
      const hoursDiff =
        (data.expiresAt.getTime() - data.createdAt.getTime()) / (1000 * 60 * 60);
      return Math.abs(hoursDiff - 48) < 1; // Allow 1 hour tolerance
    },
    { message: "ExpiresAt must be 48 hours from creation" }
  );

export const FeedbackResponseSchema = z.object({
  id: z.string().uuid(),
  requestId: z.string().uuid(),
  content: z.string().min(1, "Feedback response content cannot be empty"),
  timestamp: z.coerce.date(),
  channel: z.enum(["websocket", "email", "slack"]),
});

export type FeedbackType = z.infer<typeof FeedbackTypeSchema>;
export type FeedbackStatus = z.infer<typeof FeedbackStatusSchema>;
export type FeedbackRequest = z.infer<typeof FeedbackRequestSchema>;
export type FeedbackResponse = z.infer<typeof FeedbackResponseSchema>;
export type FeedbackRequestMetadata = z.infer<typeof FeedbackRequestMetadataSchema>;
