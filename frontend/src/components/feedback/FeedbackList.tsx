import { cn } from "@/lib/utils";
import type { FeedbackRequest as FeedbackRequestType } from "@/types/models";
import { FeedbackStatus } from "@/types/models";
import { ChevronDown, ChevronUp } from "lucide-react";
import { useState } from "react";
import { Button } from "../ui/button";
import { FeedbackRequest } from "./FeedbackRequest";
import { FeedbackResponse } from "./FeedbackResponse";

interface FeedbackListProps {
  requests: FeedbackRequestType[];
  onSubmitApproval?: (requestId: string, approved: boolean) => void;
  onSubmitInput?: (requestId: string, content: string) => void;
  loading?: Record<string, boolean>;
  errors?: Record<string, string>;
  getPendingRequests?: (requests: FeedbackRequestType[]) => FeedbackRequestType[];
  getCompletedRequests?: (requests: FeedbackRequestType[]) => FeedbackRequestType[];
  getTimeRemaining?: (expiresAt: Date) => number;
  isExpiringSoon?: (expiresAt: Date) => boolean;
  className?: string;
}

export function FeedbackList({
  requests,
  onSubmitApproval,
  onSubmitInput,
  loading = {},
  errors = {},
  getPendingRequests,
  getCompletedRequests,
  getTimeRemaining,
  isExpiringSoon,
  className,
}: FeedbackListProps) {
  const [showCompleted, setShowCompleted] = useState(false);

  // Filter requests
  const pendingRequests = getPendingRequests
    ? getPendingRequests(requests)
    : requests.filter((r) => r.status === FeedbackStatus.PENDING);

  const completedRequests = getCompletedRequests
    ? getCompletedRequests(requests)
    : requests.filter((r) => r.status !== FeedbackStatus.PENDING);

  // Empty state
  if (requests.length === 0) {
    return (
      <div className={cn("text-center py-8 text-muted-foreground", className)}>
        <p>No feedback requests</p>
      </div>
    );
  }

  return (
    <div className={cn("space-y-4", className)}>
      {/* Pending Requests Section */}
      {pendingRequests.length > 0 && (
        <div className="space-y-4 animate-in fade-in slide-in-from-top-4 duration-500">
          <h3 className="text-sm font-medium text-muted-foreground">
            Action Required ({pendingRequests.length})
          </h3>
          {pendingRequests.map((request) => (
            <div
              key={request.id}
              className="space-y-3 animate-in fade-in slide-in-from-left-4 duration-300"
            >
              <FeedbackRequest
                request={request}
                error={errors[request.id]}
                timeRemaining={getTimeRemaining?.(request.expiresAt)}
                isExpiringSoon={isExpiringSoon?.(request.expiresAt)}
              />
              <FeedbackResponse
                request={request}
                onSubmitApproval={(approved) => onSubmitApproval?.(request.id, approved)}
                onSubmitInput={(content) => onSubmitInput?.(request.id, content)}
                loading={loading[request.id]}
              />
            </div>
          ))}
        </div>
      )}

      {/* Completed Requests Section (Collapsible) */}
      {completedRequests.length > 0 && (
        <div className="space-y-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowCompleted(!showCompleted)}
            className="w-full justify-between text-muted-foreground hover:text-foreground"
          >
            <span className="text-sm font-medium">Completed ({completedRequests.length})</span>
            {showCompleted ? (
              <ChevronUp className="h-4 w-4" />
            ) : (
              <ChevronDown className="h-4 w-4" />
            )}
          </Button>

          {showCompleted && (
            <div className="space-y-3 animate-in fade-in slide-in-from-top-2 duration-300">
              {completedRequests.map((request) => (
                <div
                  key={request.id}
                  className="opacity-60 transition-opacity hover:opacity-100"
                >
                  <FeedbackRequest
                    request={request}
                    timeRemaining={getTimeRemaining?.(request.expiresAt)}
                    isExpiringSoon={false}
                  />
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Empty state when only completed requests exist */}
      {pendingRequests.length === 0 && completedRequests.length > 0 && !showCompleted && (
        <div className="text-center py-4 text-sm text-muted-foreground">
          <p>All feedback requests have been completed</p>
        </div>
      )}
    </div>
  );
}
