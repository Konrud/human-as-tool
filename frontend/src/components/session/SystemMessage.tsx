import { cn } from "@/lib/utils";
import type { Message } from "@/types/models";
import { AlertCircle, Info } from "lucide-react";

interface SystemMessageProps {
  message: Message;
}

export function SystemMessage({ message }: SystemMessageProps) {
  const formatTime = (date: Date) => {
    return new Date(date).toLocaleTimeString("en-US", {
      hour: "numeric",
      minute: "2-digit",
    });
  };

  // Determine if this is an error or info message
  const isError =
    message.content.toLowerCase().includes("error") ||
    message.content.toLowerCase().includes("failed");

  return (
    <div className="flex items-center justify-center my-4">
      <div className="flex items-center gap-2 bg-muted/50 rounded-lg px-4 py-2 max-w-[90%]">
        {isError ? (
          <AlertCircle className="h-4 w-4 text-destructive flex-shrink-0" />
        ) : (
          <Info className="h-4 w-4 text-muted-foreground flex-shrink-0" />
        )}
        <div className="flex flex-col gap-1">
          <p
            className={cn(
              "text-xs text-center",
              isError ? "text-destructive" : "text-muted-foreground"
            )}
          >
            {message.content}
          </p>
          <span className="text-[10px] text-muted-foreground/70 text-center">
            {formatTime(message.timestamp)}
          </span>
        </div>
      </div>
    </div>
  );
}
