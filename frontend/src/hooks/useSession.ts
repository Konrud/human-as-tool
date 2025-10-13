import { useCallback, useState } from "react";
import { useWebSocket } from "./useWebSocket";
import { AgentStatus, ChannelStatus, ChannelType, SessionStatus } from "../types/models";
import type { ChatSession } from "../types/models";

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
    },
  };
}
