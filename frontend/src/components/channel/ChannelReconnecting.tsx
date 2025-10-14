import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";
import { ChannelType } from "@/types/models";
import { Loader2, X } from "lucide-react";
import { useEffect, useState } from "react";
import { ChannelIcon, getChannelLabel } from "./ChannelIcon";

interface ChannelReconnectingProps {
  channel: ChannelType;
  attempts: number;
  maxAttempts: number;
  nextRetryIn?: number; // seconds
  onCancel?: () => void;
  className?: string;
}

export function ChannelReconnecting({
  channel,
  attempts,
  maxAttempts,
  nextRetryIn = 5,
  onCancel,
  className,
}: ChannelReconnectingProps) {
  const [countdown, setCountdown] = useState(nextRetryIn);
  const progress = (attempts / maxAttempts) * 100;

  useEffect(() => {
    setCountdown(nextRetryIn);
  }, [nextRetryIn]);

  useEffect(() => {
    if (countdown <= 0) {
      return;
    }

    const timer = setInterval(() => {
      setCountdown((prev) => Math.max(0, prev - 1));
    }, 1000);

    return () => clearInterval(timer);
  }, [countdown]);

  return (
    <div
      className={cn(
        "bg-blue-50 dark:bg-blue-950 border-b border-blue-200 dark:border-blue-800 px-4 py-3 animate-in slide-in-from-top-2",
        className
      )}
    >
      <div className="container max-w-6xl mx-auto">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-3 flex-1">
            <Loader2 className="h-5 w-5 animate-spin text-blue-600 dark:text-blue-400 flex-shrink-0" />
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <ChannelIcon
                  channel={channel}
                  size={14}
                  className="text-blue-600 dark:text-blue-400"
                />
                <span className="text-sm font-medium text-blue-900 dark:text-blue-100">
                  Reconnecting to {getChannelLabel(channel)}
                </span>
              </div>
              <div className="flex items-center gap-3 text-xs text-blue-700 dark:text-blue-300">
                <span>
                  Attempt {attempts} of {maxAttempts}
                </span>
                {countdown > 0 && (
                  <>
                    <span className="text-blue-400 dark:text-blue-600">•</span>
                    <span>Next retry in {countdown}s</span>
                  </>
                )}
              </div>
              <Progress value={progress} className="h-1 mt-2 bg-blue-200 dark:bg-blue-900" />
            </div>
          </div>
          {onCancel && (
            <Button
              variant="ghost"
              size="sm"
              onClick={onCancel}
              className="h-8 text-blue-700 hover:bg-blue-200 dark:text-blue-300 dark:hover:bg-blue-900 flex-shrink-0"
            >
              <X className="h-4 w-4 mr-1" />
              <span className="hidden sm:inline">Cancel</span>
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
