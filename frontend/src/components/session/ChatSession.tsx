import { FeedbackList } from "@/components/feedback/FeedbackList";
import { Card } from "@/components/ui/card";
import { useFeedback } from "@/hooks/useFeedback";
import { useMessageStream } from "@/hooks/useMessageStream";
import { useRateLimit } from "@/hooks/useRateLimit";
import { useSession } from "@/hooks/useSession";
import { AgentStatus, SessionStatus } from "@/types/models";
import { useCallback, useEffect, useMemo } from "react";
import { AgentThinking } from "./AgentThinking";
import { ConnectionStatus } from "./ConnectionStatus";
import { MessageInput } from "./MessageInput";
import { MessageList } from "./MessageList";
import { RateLimitIndicator } from "./RateLimitIndicator";
import { SessionStatus as SessionStatusComponent } from "./SessionStatus";

interface ChatSessionProps {
  wsUrl: string;
  sessionId?: string;
  onSessionUpdate?: (sessionId: string) => void;
}

export function ChatSession({ wsUrl, sessionId, onSessionUpdate }: ChatSessionProps) {
  const { session, channelStatus, agentStatus, wsStatus, actions } = useSession({
    wsUrl,
    sessionId,
  });

  const { mergeStreamWithMessage, isStreaming: checkIsStreaming } = useMessageStream();

  const rateLimit = useRateLimit({ limit: 30, warningThreshold: 0.2 });

  const feedback = useFeedback({
    sessionId: session?.id || null,
    onSubmit: (requestId, response) => {
      actions.submitFeedbackResponse(
        requestId,
        response.content || "",
        response.content === "approved"
      );
    },
  });

  // Track session creation
  useEffect(() => {
    if (session?.id && onSessionUpdate) {
      onSessionUpdate(session.id);
    }
  }, [session?.id, onSessionUpdate]);

  // Handle WebSocket messages for streaming
  useEffect(() => {
    // This would be integrated with the WebSocket message handler
    // For now, it's a placeholder for the streaming logic
  }, []);

  const handleSendMessage = useCallback(
    (content: string) => {
      const sent = actions.sendMessage(content);
      if (sent) {
        rateLimit.trackRequest();
      }
    },
    [actions, rateLimit]
  );

  const handleReconnect = useCallback(() => {
    // Reconnect logic is handled by useSession's WebSocket hook
    // This is just for UI feedback
  }, []);

  const handleSubmitApproval = useCallback(
    (requestId: string, approved: boolean) => {
      const request = session?.feedbackRequests.find((r) => r.id === requestId);
      if (request) {
        feedback.submitApproval(request, approved);
      }
    },
    [session?.feedbackRequests, feedback]
  );

  const handleSubmitInput = useCallback(
    (requestId: string, content: string) => {
      const request = session?.feedbackRequests.find((r) => r.id === requestId);
      if (request) {
        feedback.submitInput(request, content);
      }
    },
    [session?.feedbackRequests, feedback]
  );

  // Merge streaming content with messages
  const messagesWithStreaming = useMemo(() => {
    if (!session?.messages) return [];
    return session.messages.map(mergeStreamWithMessage);
  }, [session?.messages, mergeStreamWithMessage]);

  // Get streaming message IDs
  const streamingMessageIds = useMemo(() => {
    const ids = new Set<string>();
    session?.messages?.forEach((msg) => {
      if (checkIsStreaming(msg.id)) {
        ids.add(msg.id);
      }
    });
    return ids;
  }, [session?.messages, checkIsStreaming]);

  const isInputDisabled =
    !session ||
    session.status !== SessionStatus.ACTIVE ||
    wsStatus !== "active" ||
    rateLimit.isLimited;

  const showAgentThinking =
    agentStatus === AgentStatus.THINKING && streamingMessageIds.size === 0;

  const isPaused = session?.status === SessionStatus.PAUSED;
  const hasPendingFeedback =
    feedback.getPendingRequests(session?.feedbackRequests || []).length > 0;

  return (
    <Card className="flex flex-col h-full">
      {/* Connection Status */}
      <ConnectionStatus status={channelStatus.websocket} onReconnect={handleReconnect} />

      {/* Rate Limit Indicator */}
      <RateLimitIndicator rateLimit={rateLimit} />

      {/* Session Status */}
      {session && (
        <SessionStatusComponent
          sessionStatus={session.status}
          agentStatus={agentStatus}
          feedbackRequests={session.feedbackRequests}
        />
      )}

      {/* Feedback Section - Show when paused */}
      {isPaused && hasPendingFeedback && (
        <div className="px-4 py-3 border-b">
          <FeedbackList
            requests={session?.feedbackRequests || []}
            onSubmitApproval={handleSubmitApproval}
            onSubmitInput={handleSubmitInput}
            loading={feedback.loading}
            errors={feedback.errors}
            getPendingRequests={feedback.getPendingRequests}
            getCompletedRequests={feedback.getCompletedRequests}
            getTimeRemaining={feedback.getTimeRemaining}
            isExpiringSoon={feedback.isExpiringSoon}
          />
        </div>
      )}

      {/* Message List */}
      <div className="flex-1 overflow-hidden">
        <MessageList
          messages={messagesWithStreaming}
          streamingMessageIds={streamingMessageIds}
          className="h-full"
        />
        {showAgentThinking && <AgentThinking />}
      </div>

      {/* Message Input */}
      <MessageInput
        onSendMessage={handleSendMessage}
        disabled={isInputDisabled}
        placeholder={
          rateLimit.isLimited ? "Rate limit reached. Please wait..." : "Type a message..."
        }
      />
    </Card>
  );
}
