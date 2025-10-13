import { z } from "zod";

export const ChannelTypeSchema = z.enum(["websocket", "email", "slack"]);

export const ChannelStatusSchema = z.enum(["active", "inactive", "error", "reconnecting"]);

export const CommunicationChannelMetadataSchema = z.object({
  lastActive: z.coerce.date(),
  errorCount: z.number().int().min(0),
  retryTimestamp: z.coerce.date().optional(),
});

export const CommunicationChannelConfigSchema = z.object({
  priority: z.number().int().min(1).max(3, "Priority must be between 1 and 3"),
  retryLimit: z.number().int().min(0).max(10, "Retry limit cannot exceed 10"),
  timeout: z.number().int().min(0).max(3600000, "Timeout cannot exceed 1 hour (3600000ms)"),
});

export const CommunicationChannelSchema = z.object({
  type: ChannelTypeSchema,
  status: ChannelStatusSchema,
  config: CommunicationChannelConfigSchema,
  metadata: CommunicationChannelMetadataSchema,
});

export type ChannelType = z.infer<typeof ChannelTypeSchema>;
export type ChannelStatus = z.infer<typeof ChannelStatusSchema>;
export type CommunicationChannel = z.infer<typeof CommunicationChannelSchema>;
export type CommunicationChannelConfig = z.infer<typeof CommunicationChannelConfigSchema>;
export type CommunicationChannelMetadata = z.infer<typeof CommunicationChannelMetadataSchema>;
