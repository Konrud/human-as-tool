import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { useAuth } from "@/hooks/useAuth";
import type { Message } from "@/types/models";
import { MessageStatus } from "@/types/models";
import { Check, CheckCheck, Clock, XCircle } from "lucide-react";

interface UserMessageProps {
  message: Message;
}

export function UserMessage({ message }: UserMessageProps) {
  const { user } = useAuth();

  const getStatusIcon = () => {
    switch (message.status) {
      case MessageStatus.SENT:
        return <Clock className="h-3 w-3" />;
      case MessageStatus.DELIVERED:
        return <Check className="h-3 w-3" />;
      case MessageStatus.READ:
        return <CheckCheck className="h-3 w-3" />;
      case MessageStatus.FAILED:
        return <XCircle className="h-3 w-3 text-destructive" />;
      default:
        return null;
    }
  };

  const formatTime = (date: Date) => {
    return new Date(date).toLocaleTimeString("en-US", {
      hour: "numeric",
      minute: "2-digit",
    });
  };

  return (
    <div className="flex items-start justify-end gap-2 group">
      <div className="flex flex-col items-end max-w-[80%] md:max-w-[70%]">
        <div className="bg-primary text-primary-foreground rounded-2xl rounded-tr-sm px-4 py-2 min-h-[44px] flex items-center">
          <p className="text-sm whitespace-pre-wrap break-words">{message.content}</p>
        </div>
        <div className="flex items-center gap-1 mt-1 px-2 text-xs text-muted-foreground">
          <span>{formatTime(message.timestamp)}</span>
          {getStatusIcon()}
        </div>
      </div>
      <Avatar className="h-8 w-8 flex-shrink-0">
        <AvatarFallback className="bg-primary text-primary-foreground text-xs">
          {user?.name?.[0]?.toUpperCase() || "U"}
        </AvatarFallback>
      </Avatar>
    </div>
  );
}
