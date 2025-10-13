import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { Send } from "lucide-react";
import { KeyboardEvent, useEffect, useRef, useState } from "react";

interface MessageInputProps {
  onSendMessage: (content: string) => void;
  disabled?: boolean;
  placeholder?: string;
  maxLength?: number;
}

export function MessageInput({
  onSendMessage,
  disabled = false,
  placeholder = "Type a message...",
  maxLength = 2000,
}: MessageInputProps) {
  const [message, setMessage] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = () => {
    const trimmed = message.trim();
    if (trimmed && !disabled) {
      onSendMessage(trimmed);
      setMessage("");
      // Reset textarea height
      if (textareaRef.current) {
        textareaRef.current.style.height = "auto";
      }
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(
        textareaRef.current.scrollHeight,
        120
      )}px`;
    }
  }, [message]);

  const remainingChars = maxLength - message.length;
  const showCharCount = remainingChars < 100 || message.length > maxLength * 0.8;

  return (
    <div className="border-t bg-background p-4">
      <div className="flex items-end gap-2">
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={disabled}
            maxLength={maxLength}
            rows={1}
            className={cn(
              "flex w-full rounded-md border border-input bg-background px-3 py-2",
              "text-sm ring-offset-background",
              "placeholder:text-muted-foreground",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
              "disabled:cursor-not-allowed disabled:opacity-50",
              "resize-none overflow-hidden min-h-[44px] max-h-[120px]"
            )}
          />
          {showCharCount && (
            <span
              className={cn(
                "absolute bottom-2 right-2 text-xs",
                remainingChars < 0 ? "text-destructive" : "text-muted-foreground"
              )}
            >
              {remainingChars}
            </span>
          )}
        </div>
        <Button
          onClick={handleSend}
          disabled={disabled || !message.trim() || message.length > maxLength}
          size="icon"
          className="min-h-[44px] min-w-[44px] flex-shrink-0"
        >
          <Send className="h-4 w-4" />
        </Button>
      </div>
      <p className="text-xs text-muted-foreground mt-2">
        Press <kbd className="px-1 py-0.5 bg-muted rounded">Enter</kbd> to send,{" "}
        <kbd className="px-1 py-0.5 bg-muted rounded">Shift + Enter</kbd> for new line
      </p>
    </div>
  );
}
