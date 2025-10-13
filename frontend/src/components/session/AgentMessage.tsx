import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import type { Message } from "@/types/models";
import { Bot, Loader2 } from "lucide-react";

interface AgentMessageProps {
  message: Message;
  isStreaming?: boolean;
}

export function AgentMessage({ message, isStreaming = false }: AgentMessageProps) {
  const formatTime = (date: Date) => {
    return new Date(date).toLocaleTimeString("en-US", {
      hour: "numeric",
      minute: "2-digit",
    });
  };

  return (
    <div className="flex items-start gap-2 group">
      <Avatar className="h-8 w-8 flex-shrink-0">
        <AvatarFallback className="bg-secondary text-secondary-foreground">
          <Bot className="h-4 w-4" />
        </AvatarFallback>
      </Avatar>
      <div className="flex flex-col items-start max-w-[80%] md:max-w-[70%]">
        <div className="bg-secondary text-secondary-foreground rounded-2xl rounded-tl-sm px-4 py-2 min-h-[44px] flex items-center">
          <p className="text-sm whitespace-pre-wrap break-words">
            {message.content}
            {isStreaming && (
              <span className="inline-flex items-center ml-1">
                <span className="animate-pulse">▋</span>
              </span>
            )}
          </p>
        </div>
        <div className="flex items-center gap-2 mt-1 px-2 text-xs text-muted-foreground">
          <span>{formatTime(message.timestamp)}</span>
          {isStreaming && (
            <span className="flex items-center gap-1">
              <Loader2 className="h-3 w-3 animate-spin" />
              <span>typing...</span>
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
