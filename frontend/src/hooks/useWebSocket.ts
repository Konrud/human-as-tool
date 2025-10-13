import { useCallback, useEffect, useRef, useState } from "react";
import { ChannelStatus } from "../types/models";

interface WebSocketMessage {
  type: string;
  payload: unknown;
}

interface UseWebSocketOptions {
  url: string;
  onMessage?: (data: WebSocketMessage) => void;
  onStatusChange?: (status: ChannelStatus) => void;
  reconnectInterval?: number;
  maxRetries?: number;
}

interface WebSocketState {
  status: ChannelStatus;
  error: Error | null;
  retryCount: number;
}

export function useWebSocket({
  url,
  onMessage,
  onStatusChange,
  reconnectInterval = 5000,
  maxRetries = 5,
}: UseWebSocketOptions) {
  const ws = useRef<WebSocket | null>(null);
  const [state, setState] = useState<WebSocketState>({
    status: ChannelStatus.INACTIVE,
    error: null,
    retryCount: 0,
  });

  const connect = useCallback(() => {
    try {
      ws.current = new WebSocket(url);

      ws.current.onopen = () => {
        setState((prev) => ({
          ...prev,
          status: ChannelStatus.ACTIVE,
          error: null,
          retryCount: 0,
        }));
        onStatusChange?.(ChannelStatus.ACTIVE);
      };

      ws.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as WebSocketMessage;
          onMessage?.(data);
        } catch (error) {
          console.error("Failed to parse WebSocket message:", error);
        }
      };

      ws.current.onerror = () => {
        const error = new Error("WebSocket error occurred");
        setState((prev) => ({
          ...prev,
          status: ChannelStatus.ERROR,
          error,
        }));
        onStatusChange?.(ChannelStatus.ERROR);
      };

      ws.current.onclose = () => {
        setState((prev) => {
          const newState = {
            ...prev,
            status: ChannelStatus.INACTIVE,
          };

          if (prev.retryCount < maxRetries) {
            newState.status = ChannelStatus.RECONNECTING;
            setTimeout(connect, reconnectInterval);
            newState.retryCount = prev.retryCount + 1;
          }

          onStatusChange?.(newState.status);
          return newState;
        });
      };
    } catch (error) {
      const err = error instanceof Error ? error : new Error("Failed to connect to WebSocket");
      setState((prev) => ({
        ...prev,
        status: ChannelStatus.ERROR,
        error: err,
      }));
      onStatusChange?.(ChannelStatus.ERROR);
    }
  }, [url, onMessage, onStatusChange, reconnectInterval, maxRetries]);

  const disconnect = useCallback(() => {
    if (ws.current) {
      ws.current.close();
      ws.current = null;
    }
  }, []);

  const send = useCallback((data: WebSocketMessage) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(data));
      return true;
    }
    return false;
  }, []);

  useEffect(() => {
    connect();
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    status: state.status,
    error: state.error,
    send,
    disconnect,
    reconnect: connect,
  };
}
