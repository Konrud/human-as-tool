import { useCallback, useState } from "react";
import type { ChatSession } from "../types/models";
import {
  AgentStatus,
  ChannelStatus,
  ChannelType,
  FeedbackStatus,
  SessionStatus,
} from "../types/models";
import { useWebSocket } from "./useWebSocket";

interface UseSessionOptions {
  wsUrl: string;
  sessionId?: string;
}

interface SessionState {
  session: ChatSession | null;
  channelStatus: Record<ChannelType, ChannelStatus>;
  agentStatus: AgentStatus;
  error: Error | null;
}

export function useSession({ wsUrl, sessionId }: UseSessionOptions) {
  const [state, setState] = useState<SessionState>({
    session: null,
    channelStatus: {
      [ChannelType.WEBSOCKET]: ChannelStatus.INACTIVE,
      [ChannelType.EMAIL]: ChannelStatus.INACTIVE,
      [ChannelType.SLACK]: ChannelStatus.INACTIVE,
    },
    agentStatus: AgentStatus.IDLE,
    error: null,
  });

  // Handle WebSocket status changes
  const handleChannelStatusChange = useCallback((status: ChannelStatus) => {
    setState((prev) => ({
      ...prev,
      channelStatus: {
        ...prev.channelStatus,
        [ChannelType.WEBSOCKET]: status,
      },
    }));
  }, []);

  // Handle WebSocket messages
  const handleMessage = useCallback((data: { type: string; payload: unknown }) => {
    switch (data.type) {
      case "session_update":
        setState((prev) => ({
          ...prev,
          session: data.payload as ChatSession,
        }));
        break;
      case "agent_status":
        setState((prev) => ({
          ...prev,
          agentStatus: data.payload as AgentStatus,
        }));
        break;
      case "feedback_request":
        // New feedback request received - update session
        setState((prev) => {
          if (!prev.session) return prev;
          return {
            ...prev,
            session: {
              ...prev.session,
              feedbackRequests: [...prev.session.feedbackRequests, data.payload as any],
              status: SessionStatus.PAUSED,
            },
          };
        });
        break;
      case "feedback_response":
        // Feedback response submitted - update request status
        setState((prev) => {
          if (!prev.session) return prev;
          const response = data.payload as any;
          const newStatus =
            response.content === "approved"
              ? FeedbackStatus.APPROVED
              : FeedbackStatus.REJECTED;
          return {
            ...prev,
            session: {
              ...prev.session,
              feedbackRequests: prev.session.feedbackRequests.map((req) =>
                req.id === response.requestId
                  ? {
                      ...req,
                      status: newStatus,
                      responses: [...req.responses, response],
                    }
                  : req
              ),
            },
          };
        });
        break;
      case "session_resumed":
        // Session resumed after feedback
        setState((prev) => {
          if (!prev.session) return prev;
          return {
            ...prev,
            session: {
              ...prev.session,
              status: SessionStatus.ACTIVE,
            },
            agentStatus: AgentStatus.IDLE,
          };
        });
        break;
      case "channel_status_update":
        // Channel status changed
        setState((prev) => {
          const payload = data.payload as { channel: ChannelType; status: ChannelStatus };
          return {
            ...prev,
            channelStatus: {
              ...prev.channelStatus,
              [payload.channel]: payload.status,
            },
          };
        });
        break;
      case "channel_fallback":
        // Channel fallback occurred
        setState((prev) => {
          const payload = data.payload as {
            previousChannel: ChannelType;
            currentChannel: ChannelType;
            reason: string;
          };
          if (!prev.session) return prev;
          return {
            ...prev,
            session: {
              ...prev.session,
              preferredChannel: payload.currentChannel,
            },
          };
        });
        break;
      case "channel_reconnect_attempt":
        // Channel reconnection attempt
        setState((prev) => {
          const payload = data.payload as { channel: ChannelType; attempt: number };
          return {
            ...prev,
            channelStatus: {
              ...prev.channelStatus,
              [payload.channel]: ChannelStatus.RECONNECTING,
            },
          };
        });
        break;
      case "channel_reconnect_success":
        // Channel reconnection succeeded
        setState((prev) => {
          const payload = data.payload as { channel: ChannelType };
          return {
            ...prev,
            channelStatus: {
              ...prev.channelStatus,
              [payload.channel]: ChannelStatus.ACTIVE,
            },
          };
        });
        break;
      case "channel_reconnect_failed":
        // Channel reconnection failed
        setState((prev) => {
          const payload = data.payload as { channel: ChannelType };
          return {
            ...prev,
            channelStatus: {
              ...prev.channelStatus,
              [payload.channel]: ChannelStatus.ERROR,
            },
          };
        });
        break;
      case "stream_start":
        // Streaming start event (optional)
        break;
      case "stream_chunk":
        // Streaming chunk event - would be handled by parent component
        break;
      case "stream_complete":
        // Streaming complete event - would be handled by parent component
        break;
      case "error":
        setState((prev) => ({
          ...prev,
          error: new Error(String(data.payload)),
        }));
        break;
      default:
        console.warn("Unknown message type:", data.type);
    }
  }, []);

  // Initialize WebSocket connection
  const { send, status: wsStatus } = useWebSocket({
    url: `${wsUrl}${sessionId ? `/${sessionId}` : ""}`,
    onMessage: handleMessage,
    onStatusChange: handleChannelStatusChange,
  });

  // Session management functions
  const startSession = useCallback(() => {
    send({
      type: "start_session",
      payload: { timestamp: new Date().toISOString() },
    });
  }, [send]);

  const endSession = useCallback(() => {
    if (state.session?.id) {
      send({
        type: "end_session",
        payload: { sessionId: state.session.id },
      });
    }
  }, [send, state.session?.id]);

  const pauseSession = useCallback(() => {
    if (state.session?.id) {
      send({
        type: "pause_session",
        payload: { sessionId: state.session.id },
      });
    }
  }, [send, state.session?.id]);

  const resumeSession = useCallback(() => {
    if (state.session?.id) {
      send({
        type: "resume_session",
        payload: { sessionId: state.session.id },
      });
    }
  }, [send, state.session?.id]);

  const sendMessage = useCallback(
    (content: string) => {
      if (state.session?.id && state.session.status === SessionStatus.ACTIVE) {
        send({
          type: "send_message",
          payload: {
            sessionId: state.session.id,
            content,
            timestamp: new Date().toISOString(),
          },
        });
        return true;
      }
      return false;
    },
    [send, state.session?.id, state.session?.status]
  );

  const submitFeedbackResponse = useCallback(
    (requestId: string, content: string, approved?: boolean) => {
      if (state.session?.id) {
        send({
          type: "feedback_response",
          payload: {
            requestId,
            content,
            approved,
            sessionId: state.session.id,
            timestamp: new Date().toISOString(),
          },
        });
      }
    },
    [send, state.session?.id]
  );

  const changePreferredChannel = useCallback(
    (channel: ChannelType) => {
      if (state.session?.id) {
        send({
          type: "change_preferred_channel",
          payload: {
            sessionId: state.session.id,
            channel,
            timestamp: new Date().toISOString(),
          },
        });
        // Optimistically update local state
        setState((prev) => {
          if (!prev.session) return prev;
          return {
            ...prev,
            session: {
              ...prev.session,
              preferredChannel: channel,
            },
          };
        });
      }
    },
    [send, state.session?.id]
  );

  return {
    session: state.session,
    channelStatus: state.channelStatus,
    agentStatus: state.agentStatus,
    error: state.error,
    wsStatus,
    actions: {
      startSession,
      endSession,
      pauseSession,
      resumeSession,
      sendMessage,
      submitFeedbackResponse,
      changePreferredChannel,
    },
  };
}
