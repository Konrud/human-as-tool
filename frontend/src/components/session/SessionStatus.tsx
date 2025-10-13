import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { cn } from "@/lib/utils";
import { AgentStatus, SessionStatus as SessionStatusEnum } from "@/types/models";
import { AlertCircle, CheckCircle, Clock, Pause } from "lucide-react";

interface SessionStatusProps {
  sessionStatus: SessionStatusEnum;
  agentStatus: AgentStatus;
  className?: string;
}

export function SessionStatus({ sessionStatus, agentStatus, className }: SessionStatusProps) {
  const getStatusConfig = () => {
    // Session-level status takes precedence
    if (sessionStatus === SessionStatusEnum.PAUSED) {
      return {
        icon: <Pause className="h-4 w-4" />,
        title: "Session Paused",
        description: "Waiting for feedback or approval to continue",
        variant: "default" as const,
      };
    }

    if (sessionStatus === SessionStatusEnum.ENDED) {
      return {
        icon: <CheckCircle className="h-4 w-4" />,
        title: "Session Ended",
        description: "This conversation has been closed",
        variant: "default" as const,
      };
    }

    // Agent-level status
    switch (agentStatus) {
      case AgentStatus.THINKING:
        return {
          icon: <Clock className="h-4 w-4 animate-spin" />,
          title: "Agent Thinking",
          description: "Processing your request...",
          variant: "default" as const,
        };
      case AgentStatus.RESPONDING:
        return {
          icon: <Clock className="h-4 w-4" />,
          title: "Agent Responding",
          description: "Generating response...",
          variant: "default" as const,
        };
      case AgentStatus.ERROR:
        return {
          icon: <AlertCircle className="h-4 w-4" />,
          title: "Agent Error",
          description: "Something went wrong. Please try again.",
          variant: "destructive" as const,
        };
      case AgentStatus.IDLE:
      default:
        return null;
    }
  };

  const config = getStatusConfig();

  if (!config) {
    return null;
  }

  return (
    <Alert variant={config.variant} className={cn("mx-4 mt-4", className)}>
      {config.icon}
      <AlertTitle>{config.title}</AlertTitle>
      <AlertDescription>{config.description}</AlertDescription>
    </Alert>
  );
}
