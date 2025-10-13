import { ScrollArea } from "@/components/ui/scroll-area";
import type { Message } from "@/types/models";
import { MessageType } from "@/types/models";
import { useEffect, useRef } from "react";
import { AgentMessage } from "./AgentMessage";
import { SystemMessage } from "./SystemMessage";
import { UserMessage } from "./UserMessage";

interface MessageListProps {
  messages: Message[];
  streamingMessageIds?: Set<string>;
  className?: string;
}

export function MessageList({ messages, streamingMessageIds, className }: MessageListProps) {
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages.length]);

  // Also scroll when streaming updates
  useEffect(() => {
    if (streamingMessageIds && streamingMessageIds.size > 0 && bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [streamingMessageIds]);

  const renderMessage = (message: Message) => {
    const isStreaming = streamingMessageIds?.has(message.id) ?? false;

    switch (message.type) {
      case MessageType.USER:
        return <UserMessage key={message.id} message={message} />;
      case MessageType.AGENT:
        return <AgentMessage key={message.id} message={message} isStreaming={isStreaming} />;
      case MessageType.SYSTEM:
        return <SystemMessage key={message.id} message={message} />;
      default:
        return null;
    }
  };

  return (
    <ScrollArea className={className} ref={scrollAreaRef}>
      <div className="flex flex-col gap-4 p-4">
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
            <p>No messages yet. Start a conversation!</p>
          </div>
        ) : (
          <>
            {messages.map(renderMessage)}
            <div ref={bottomRef} />
          </>
        )}
      </div>
    </ScrollArea>
  );
}
