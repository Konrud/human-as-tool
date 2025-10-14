import { ChannelStatus, ChannelType } from "@/types/models";
import { useCallback, useState } from "react";

interface UseChannelOptions {
  sessionId?: string;
  send: (data: { type: string; payload: unknown }) => void;
  initialChannelStatus?: Record<ChannelType, ChannelStatus>;
}

interface ChannelFallbackInfo {
  previousChannel: ChannelType;
  currentChannel: ChannelType;
  reason: string;
  timestamp: Date;
}

export function useChannel({
  sessionId,
  send,
  initialChannelStatus = {
    [ChannelType.WEBSOCKET]: ChannelStatus.ACTIVE,
    [ChannelType.EMAIL]: ChannelStatus.INACTIVE,
    [ChannelType.SLACK]: ChannelStatus.INACTIVE,
  },
}: UseChannelOptions) {
  const [channelStatus, setChannelStatus] =
    useState<Record<ChannelType, ChannelStatus>>(initialChannelStatus);
  const [fallbackInfo, setFallbackInfo] = useState<ChannelFallbackInfo | null>(null);
  const [reconnectAttempts, setReconnectAttempts] = useState(0);
  const [maxReconnectAttempts] = useState(5);

  // Define fallback priority order
  const channelPriority: ChannelType[] = [
    ChannelType.WEBSOCKET,
    ChannelType.EMAIL,
    ChannelType.SLACK,
  ];

  // Check if a channel is available
  const isChannelAvailable = useCallback(
    (channel: ChannelType): boolean => {
      return channelStatus[channel] === ChannelStatus.ACTIVE;
    },
    [channelStatus]
  );

  // Get the next fallback channel based on priority
  const getNextFallbackChannel = useCallback(
    (currentChannel: ChannelType): ChannelType | null => {
      const currentIndex = channelPriority.indexOf(currentChannel);
      for (let i = currentIndex + 1; i < channelPriority.length; i++) {
        const nextChannel = channelPriority[i];
        if (isChannelAvailable(nextChannel)) {
          return nextChannel;
        }
      }
      return null;
    },
    [channelPriority, isChannelAvailable]
  );

  // Change preferred channel
  const changePreferredChannel = useCallback(
    (channel: ChannelType) => {
      if (!sessionId) {
        console.warn("Cannot change channel: no session ID");
        return;
      }

      send({
        type: "change_preferred_channel",
        payload: {
          sessionId,
          channel,
          timestamp: new Date().toISOString(),
        },
      });
    },
    [send, sessionId]
  );

  // Update channel status
  const updateChannelStatus = useCallback((channel: ChannelType, status: ChannelStatus) => {
    setChannelStatus((prev) => ({
      ...prev,
      [channel]: status,
    }));
  }, []);

  // Handle channel fallback
  const handleChannelFallback = useCallback(
    (previousChannel: ChannelType, reason: string) => {
      const nextChannel = getNextFallbackChannel(previousChannel);

      if (nextChannel) {
        setFallbackInfo({
          previousChannel,
          currentChannel: nextChannel,
          reason,
          timestamp: new Date(),
        });
        changePreferredChannel(nextChannel);
      } else {
        console.error("No fallback channels available");
        setFallbackInfo({
          previousChannel,
          currentChannel: previousChannel,
          reason: "No fallback channels available",
          timestamp: new Date(),
        });
      }
    },
    [getNextFallbackChannel, changePreferredChannel]
  );

  // Retry a failed channel
  const retryChannel = useCallback(
    (channel: ChannelType) => {
      if (!sessionId) return;

      // Update status to reconnecting
      updateChannelStatus(channel, ChannelStatus.RECONNECTING);
      setReconnectAttempts((prev) => prev + 1);

      send({
        type: "retry_channel",
        payload: {
          sessionId,
          channel,
          attempt: reconnectAttempts + 1,
          timestamp: new Date().toISOString(),
        },
      });
    },
    [send, sessionId, reconnectAttempts, updateChannelStatus]
  );

  // Dismiss fallback notification
  const dismissFallback = useCallback(() => {
    setFallbackInfo(null);
  }, []);

  // Reset reconnect attempts
  const resetReconnectAttempts = useCallback(() => {
    setReconnectAttempts(0);
  }, []);

  return {
    channelStatus,
    fallbackInfo,
    reconnectAttempts,
    maxReconnectAttempts,
    actions: {
      changePreferredChannel,
      updateChannelStatus,
      handleChannelFallback,
      retryChannel,
      dismissFallback,
      resetReconnectAttempts,
      isChannelAvailable,
      getNextFallbackChannel,
    },
  };
}
