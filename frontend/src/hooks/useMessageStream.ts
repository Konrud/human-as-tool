import type { Message } from "@/types/models";
import { useCallback, useState } from "react";

interface StreamingMessage {
  id: string;
  content: string;
  isComplete: boolean;
}

export function useMessageStream() {
  const [streamingMessages, setStreamingMessages] = useState<Map<string, StreamingMessage>>(
    new Map()
  );

  // Start a new streaming message
  const startStream = useCallback((messageId: string) => {
    setStreamingMessages((prev) => {
      const newMap = new Map(prev);
      newMap.set(messageId, {
        id: messageId,
        content: "",
        isComplete: false,
      });
      return newMap;
    });
  }, []);

  // Add chunk to streaming message
  const addChunk = useCallback((messageId: string, chunk: string) => {
    setStreamingMessages((prev) => {
      const newMap = new Map(prev);
      const existing = newMap.get(messageId);
      if (existing) {
        newMap.set(messageId, {
          ...existing,
          content: existing.content + chunk,
        });
      }
      return newMap;
    });
  }, []);

  // Complete a streaming message
  const completeStream = useCallback((messageId: string) => {
    setStreamingMessages((prev) => {
      const newMap = new Map(prev);
      const existing = newMap.get(messageId);
      if (existing) {
        newMap.set(messageId, {
          ...existing,
          isComplete: true,
        });
      }
      return newMap;
    });
  }, []);

  // Clear a streaming message
  const clearStream = useCallback((messageId: string) => {
    setStreamingMessages((prev) => {
      const newMap = new Map(prev);
      newMap.delete(messageId);
      return newMap;
    });
  }, []);

  // Get streaming content for a message
  const getStreamContent = useCallback(
    (messageId: string): string | null => {
      const stream = streamingMessages.get(messageId);
      return stream ? stream.content : null;
    },
    [streamingMessages]
  );

  // Check if message is streaming
  const isStreaming = useCallback(
    (messageId: string): boolean => {
      const stream = streamingMessages.get(messageId);
      return stream ? !stream.isComplete : false;
    },
    [streamingMessages]
  );

  // Merge streaming content with message
  const mergeStreamWithMessage = useCallback(
    (message: Message): Message => {
      const streamContent = getStreamContent(message.id);
      if (streamContent !== null) {
        return {
          ...message,
          content: streamContent,
          metadata: {
            ...message.metadata,
            streamingComplete: !isStreaming(message.id),
          },
        };
      }
      return message;
    },
    [getStreamContent, isStreaming]
  );

  return {
    startStream,
    addChunk,
    completeStream,
    clearStream,
    getStreamContent,
    isStreaming,
    mergeStreamWithMessage,
  };
}
