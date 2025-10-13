import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Bot } from "lucide-react";

export function AgentThinking() {
  return (
    <div className="flex items-start gap-2 px-4 py-2">
      <Avatar className="h-8 w-8 flex-shrink-0">
        <AvatarFallback className="bg-secondary text-secondary-foreground">
          <Bot className="h-4 w-4" />
        </AvatarFallback>
      </Avatar>
      <div className="bg-secondary rounded-2xl rounded-tl-sm px-4 py-3 flex items-center gap-2">
        <div className="flex gap-1">
          <span className="w-2 h-2 bg-secondary-foreground/60 rounded-full animate-bounce [animation-delay:-0.3s]"></span>
          <span className="w-2 h-2 bg-secondary-foreground/60 rounded-full animate-bounce [animation-delay:-0.15s]"></span>
          <span className="w-2 h-2 bg-secondary-foreground/60 rounded-full animate-bounce"></span>
        </div>
      </div>
    </div>
  );
}
