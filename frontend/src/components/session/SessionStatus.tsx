import { ChannelIcon, getChannelLabel } from "@/components/channel/ChannelIcon";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { FeedbackRequest } from "@/types/models";
import {
  AgentStatus,
  ChannelType,
  FeedbackStatus,
  SessionStatus as SessionStatusEnum,
} from "@/types/models";
import { AlertCircle, CheckCircle, Clock, Pause } from "lucide-react";

interface SessionStatusProps {
  sessionStatus: SessionStatusEnum;
  agentStatus: AgentStatus;
  feedbackRequests?: FeedbackRequest[];
  currentChannel?: ChannelType;
  className?: string;
}

export function SessionStatus({
  sessionStatus,
  agentStatus,
  feedbackRequests = [],
  currentChannel = ChannelType.WEBSOCKET,
  className,
}: SessionStatusProps) {
  // Count pending feedback requests
  const pendingCount = feedbackRequests.filter(
    (req) => req.status === FeedbackStatus.PENDING
  ).length;

  // Check if any feedback is expiring soon (less than 2 hours)
  const hasUrgentFeedback = feedbackRequests.some((req) => {
    if (req.status !== FeedbackStatus.PENDING) return false;
    const now = new Date().getTime();
    const expiry = new Date(req.expiresAt).getTime();
    const remaining = expiry - now;
    return remaining < 2 * 60 * 60 * 1000; // 2 hours
  });

  const getStatusConfig = () => {
    // Session-level status takes precedence
    if (sessionStatus === SessionStatusEnum.PAUSED) {
      return {
        icon: <Pause className="h-4 w-4" />,
        title: "Session Paused",
        description:
          pendingCount > 0
            ? `Awaiting ${pendingCount} feedback ${
                pendingCount === 1 ? "response" : "responses"
              } to continue`
            : "Waiting for feedback or approval to continue",
        variant: hasUrgentFeedback ? ("destructive" as const) : ("default" as const),
        badge:
          pendingCount > 0 ? (
            <Badge
              variant={hasUrgentFeedback ? "destructive" : "default"}
              className={cn(hasUrgentFeedback && "animate-pulse")}
            >
              {pendingCount} pending
            </Badge>
          ) : null,
      };
    }

    if (sessionStatus === SessionStatusEnum.ENDED) {
      return {
        icon: <CheckCircle className="h-4 w-4" />,
        title: "Session Ended",
        description: "This conversation has been closed",
        variant: "default" as const,
        badge: null,
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
          badge: null,
        };
      case AgentStatus.RESPONDING:
        return {
          icon: <Clock className="h-4 w-4" />,
          title: "Agent Responding",
          description: "Generating response...",
          variant: "default" as const,
          badge: null,
        };
      case AgentStatus.ERROR:
        return {
          icon: <AlertCircle className="h-4 w-4" />,
          title: "Agent Error",
          description: "Something went wrong. Please try again.",
          variant: "destructive" as const,
          badge: null,
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

  // Add channel info for non-WebSocket channels
  const channelInfo =
    currentChannel !== ChannelType.WEBSOCKET ? (
      <div className="flex items-center gap-1 text-xs text-muted-foreground mt-1">
        <span>via</span>
        <ChannelIcon channel={currentChannel} size={12} />
        <span className="font-medium">{getChannelLabel(currentChannel)}</span>
      </div>
    ) : null;

  return (
    <Alert variant={config.variant} className={cn("mx-4 mt-4", className)}>
      <div className="flex items-start justify-between w-full gap-2">
        <div className="flex items-start gap-2 flex-1">
          {config.icon}
          <div className="flex-1">
            <AlertTitle>{config.title}</AlertTitle>
            <AlertDescription>
              {config.description}
              {channelInfo}
            </AlertDescription>
          </div>
        </div>
        {config.badge && <div className="flex-shrink-0">{config.badge}</div>}
      </div>
    </Alert>
  );
}
