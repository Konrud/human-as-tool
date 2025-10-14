import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { ChannelType } from "@/types/models";
import { AlertCircle, RefreshCw, X } from "lucide-react";
import { useEffect, useState } from "react";
import { ChannelIcon, getChannelLabel } from "./ChannelIcon";

interface ChannelFallbackAlertProps {
  previousChannel: ChannelType;
  currentChannel: ChannelType;
  reason: string;
  onRetry?: () => void;
  onDismiss?: () => void;
  retryDelay?: number; // seconds until retry is available
  className?: string;
}

export function ChannelFallbackAlert({
  previousChannel,
  currentChannel,
  reason,
  onRetry,
  onDismiss,
  retryDelay = 30,
  className,
}: ChannelFallbackAlertProps) {
  const [countdown, setCountdown] = useState(retryDelay);
  const [canRetry, setCanRetry] = useState(false);

  useEffect(() => {
    if (countdown <= 0) {
      setCanRetry(true);
      return;
    }

    const timer = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          setCanRetry(true);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [countdown]);

  const handleRetry = () => {
    if (canRetry && onRetry) {
      setCanRetry(false);
      setCountdown(retryDelay);
      onRetry();
    }
  };

  return (
    <Alert
      variant="default"
      className={cn(
        "animate-in slide-in-from-top-2 duration-300 border-yellow-500 bg-yellow-50 dark:bg-yellow-950 dark:border-yellow-800",
        className
      )}
    >
      <AlertCircle className="h-4 w-4 text-yellow-600 dark:text-yellow-400" />
      <AlertTitle className="text-yellow-900 dark:text-yellow-100 flex items-center justify-between pr-6">
        Channel Switched
        {onDismiss && (
          <Button
            variant="ghost"
            size="icon"
            onClick={onDismiss}
            className="h-6 w-6 absolute right-2 top-2 hover:bg-yellow-200 dark:hover:bg-yellow-900"
            aria-label="Dismiss alert"
          >
            <X className="h-3 w-3" />
          </Button>
        )}
      </AlertTitle>
      <AlertDescription className="text-yellow-800 dark:text-yellow-200">
        <div className="space-y-3">
          <div className="flex items-center gap-2 flex-wrap">
            <div className="flex items-center gap-1">
              <ChannelIcon channel={previousChannel} size={14} />
              <span className="font-medium">{getChannelLabel(previousChannel)}</span>
            </div>
            <span>unavailable.</span>
            <span>Now using</span>
            <div className="flex items-center gap-1 font-semibold">
              <ChannelIcon channel={currentChannel} size={14} />
              <span>{getChannelLabel(currentChannel)}</span>
            </div>
          </div>

          {reason && (
            <p className="text-xs text-yellow-700 dark:text-yellow-300">Reason: {reason}</p>
          )}

          {onRetry && (
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleRetry}
                disabled={!canRetry}
                className="h-8 bg-white dark:bg-gray-900 border-yellow-600 hover:bg-yellow-100 dark:hover:bg-yellow-950"
              >
                <RefreshCw className={cn("h-3 w-3 mr-1", !canRetry && "animate-spin")} />
                {canRetry
                  ? `Retry ${getChannelLabel(previousChannel)}`
                  : `Retry in ${countdown}s`}
              </Button>
            </div>
          )}
        </div>
      </AlertDescription>
    </Alert>
  );
}
