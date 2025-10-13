import { Card } from "@/components/ui/card";
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

  const {
    startStream,
    addChunk,
    completeStream,
    mergeStreamWithMessage,
    isStreaming: checkIsStreaming,
  } = useMessageStream();

  const rateLimit = useRateLimit({ limit: 30, warningThreshold: 0.2 });

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

  return (
    <Card className="flex flex-col h-full">
      {/* Connection Status */}
      <ConnectionStatus status={channelStatus.websocket} onReconnect={handleReconnect} />

      {/* Rate Limit Indicator */}
      <RateLimitIndicator rateLimit={rateLimit} />

      {/* Session Status */}
      {session && (
        <SessionStatusComponent sessionStatus={session.status} agentStatus={agentStatus} />
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
