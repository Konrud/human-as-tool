import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { FeedbackRequest as FeedbackRequestType } from "@/types/models";
import { FeedbackStatus, FeedbackType } from "@/types/models";
import { AlertCircle, CheckCircle, Clock, XCircle } from "lucide-react";
import { useEffect, useState } from "react";

interface FeedbackRequestProps {
  request: FeedbackRequestType;
  timeRemaining?: number;
  isExpiringSoon?: boolean;
  error?: string;
  className?: string;
}

export function FeedbackRequest({
  request,
  timeRemaining,
  isExpiringSoon,
  error,
  className,
}: FeedbackRequestProps) {
  const [localTimeRemaining, setLocalTimeRemaining] = useState(timeRemaining || 0);

  // Update countdown timer
  useEffect(() => {
    if (request.status !== FeedbackStatus.PENDING) return;

    const interval = setInterval(() => {
      const now = new Date().getTime();
      const expiry = new Date(request.expiresAt).getTime();
      const remaining = Math.max(0, expiry - now);
      setLocalTimeRemaining(remaining);

      if (remaining === 0) {
        clearInterval(interval);
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [request.expiresAt, request.status]);

  const getStatusIcon = () => {
    switch (request.status) {
      case FeedbackStatus.APPROVED:
        return <CheckCircle className="h-4 w-4 text-green-600" />;
      case FeedbackStatus.REJECTED:
        return <XCircle className="h-4 w-4 text-red-600" />;
      case FeedbackStatus.EXPIRED:
        return <AlertCircle className="h-4 w-4 text-orange-600" />;
      case FeedbackStatus.PENDING:
      default:
        return <Clock className="h-4 w-4 text-blue-600" />;
    }
  };

  const getStatusBadge = () => {
    switch (request.status) {
      case FeedbackStatus.APPROVED:
        return (
          <Badge variant="default" className="bg-green-600">
            Approved
          </Badge>
        );
      case FeedbackStatus.REJECTED:
        return <Badge variant="destructive">Rejected</Badge>;
      case FeedbackStatus.EXPIRED:
        return <Badge variant="secondary">Expired</Badge>;
      case FeedbackStatus.PENDING:
      default:
        return (
          <Badge
            variant={isExpiringSoon ? "destructive" : "default"}
            className={cn(isExpiringSoon && "animate-pulse")}
          >
            Pending
          </Badge>
        );
    }
  };

  const formatTimeRemaining = (ms: number): string => {
    const hours = Math.floor(ms / (1000 * 60 * 60));
    const minutes = Math.floor((ms % (1000 * 60 * 60)) / (1000 * 60));
    const seconds = Math.floor((ms % (1000 * 60)) / 1000);

    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    }
    if (minutes > 0) {
      return `${minutes}m ${seconds}s`;
    }
    return `${seconds}s`;
  };

  const getTypeLabel = () => {
    return request.type === FeedbackType.APPROVAL ? "Approval Required" : "Input Required";
  };

  return (
    <Card
      className={cn(
        "transition-all duration-300",
        isExpiringSoon && request.status === FeedbackStatus.PENDING && "border-orange-500",
        className
      )}
    >
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-center gap-2">
            {getStatusIcon()}
            <CardTitle className="text-base sm:text-lg">{getTypeLabel()}</CardTitle>
          </div>
          {getStatusBadge()}
        </div>
        {request.status === FeedbackStatus.PENDING && localTimeRemaining > 0 && (
          <CardDescription className="flex items-center gap-1 text-xs sm:text-sm">
            <Clock className="h-3 w-3" />
            Expires in {formatTimeRemaining(localTimeRemaining)}
          </CardDescription>
        )}
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Request Prompt */}
        <p className="text-sm sm:text-base">{request.prompt}</p>

        {/* Channel Indicators */}
        {request.channels.length > 0 && (
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <span>Sent via:</span>
            {request.channels.map((channel) => (
              <Badge key={channel} variant="outline" className="text-xs">
                {channel}
              </Badge>
            ))}
          </div>
        )}

        {/* Error Display */}
        {error && (
          <div className="flex items-center gap-2 rounded-md bg-destructive/10 p-2 text-sm text-destructive">
            <AlertCircle className="h-4 w-4" />
            <span>{error}</span>
          </div>
        )}

        {/* Response Section - will be handled by FeedbackResponse component */}
        {request.status === FeedbackStatus.PENDING && localTimeRemaining > 0 && (
          <div className="text-xs text-muted-foreground">
            {request.type === FeedbackType.APPROVAL
              ? "Please approve or reject this request"
              : "Please provide your response below"}
          </div>
        )}

        {/* Show responses if any */}
        {request.responses && request.responses.length > 0 && (
          <div className="space-y-2">
            <div className="text-xs font-medium text-muted-foreground">Response:</div>
            {request.responses.map((response) => (
              <div key={response.id} className="rounded-md border bg-muted/50 p-2 text-sm">
                <p>{response.content}</p>
                <p className="mt-1 text-xs text-muted-foreground">
                  via {response.channel} at {new Date(response.timestamp).toLocaleString()}
                </p>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
