import { z } from "zod";

export const AgentStatusSchema = z.enum(["idle", "thinking", "responding", "error"]);

export const AgentStateMetadataSchema = z.object({
  processingTime: z.number().int().min(0).optional(),
  errorDetails: z.string().optional(),
  retryCount: z.number().int().min(0).optional(),
});

export const AgentStateSchema = z
  .object({
    status: AgentStatusSchema,
    sessionId: z.string().uuid(),
    lastUpdate: z.coerce.date(),
    context: z.record(z.string(), z.unknown()).optional(),
    metadata: AgentStateMetadataSchema,
  })
  .refine(
    (state) => {
      // Validation: Cannot have idle status with pending actions in context
      if (state.status === "idle" && state.context?.pendingActions) {
        const pendingActions = state.context.pendingActions as unknown[];
        return !Array.isArray(pendingActions) || pendingActions.length === 0;
      }
      return true;
    },
    { message: "Idle agent cannot have pending actions" }
  );

export type AgentStatus = z.infer<typeof AgentStatusSchema>;
export type AgentState = z.infer<typeof AgentStateSchema>;
export type AgentStateMetadata = z.infer<typeof AgentStateMetadataSchema>;
