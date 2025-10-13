import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Progress } from "@/components/ui/progress";
import type { RateLimitState } from "@/hooks/useRateLimit";
import { cn } from "@/lib/utils";
import { AlertTriangle, Clock } from "lucide-react";
import { useEffect, useState } from "react";

interface RateLimitIndicatorProps {
  rateLimit: RateLimitState;
  className?: string;
}

export function RateLimitIndicator({ rateLimit, className }: RateLimitIndicatorProps) {
  const [timeToReset, setTimeToReset] = useState<string>("");

  useEffect(() => {
    if (!rateLimit.resetTime) {
      setTimeToReset("");
      return;
    }

    const updateTime = () => {
      const now = Date.now();
      const reset = rateLimit.resetTime!.getTime();
      const diff = Math.max(0, reset - now);

      if (diff === 0) {
        setTimeToReset("");
        return;
      }

      const seconds = Math.ceil(diff / 1000);
      const minutes = Math.floor(seconds / 60);
      const remainingSeconds = seconds % 60;

      if (minutes > 0) {
        setTimeToReset(`${minutes}m ${remainingSeconds}s`);
      } else {
        setTimeToReset(`${remainingSeconds}s`);
      }
    };

    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, [rateLimit.resetTime]);

  const percentage = (rateLimit.remaining / rateLimit.limit) * 100;

  // Only show if limited or warning
  if (!rateLimit.isLimited && !rateLimit.shouldWarn) {
    return null;
  }

  return (
    <Alert
      variant={rateLimit.isLimited ? "destructive" : "default"}
      className={cn("mx-4 mb-4", className)}
    >
      {rateLimit.isLimited ? (
        <AlertTriangle className="h-4 w-4" />
      ) : (
        <Clock className="h-4 w-4" />
      )}
      <div className="flex-1">
        <AlertTitle>
          {rateLimit.isLimited ? "Rate Limit Reached" : "Approaching Rate Limit"}
        </AlertTitle>
        <AlertDescription className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span>
              {rateLimit.remaining} of {rateLimit.limit} requests remaining
            </span>
            {timeToReset && <span className="text-xs">Resets in {timeToReset}</span>}
          </div>
          <Progress value={percentage} className="h-2" />
          {rateLimit.isLimited && (
            <p className="text-xs mt-2">
              You've reached the request limit. Please wait for the quota to reset.
            </p>
          )}
        </AlertDescription>
      </div>
    </Alert>
  );
}
