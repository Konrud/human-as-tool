import { useCallback, useEffect, useState } from "react";

export interface RateLimitState {
  limit: number;
  remaining: number;
  resetTime: Date | null;
  isLimited: boolean;
  warningThreshold: number;
}

interface UseRateLimitOptions {
  limit?: number; // requests per minute
  warningThreshold?: number; // percentage (0-1)
}

export function useRateLimit({
  limit = 30,
  warningThreshold = 0.2,
}: UseRateLimitOptions = {}) {
  const [state, setState] = useState<RateLimitState>({
    limit,
    remaining: limit,
    resetTime: null,
    isLimited: false,
    warningThreshold,
  });

  const [requestTimestamps, setRequestTimestamps] = useState<number[]>([]);

  // Clean up old timestamps and update state
  const updateRateLimit = useCallback(() => {
    const now = Date.now();
    const oneMinuteAgo = now - 60000;

    // Filter out timestamps older than 1 minute
    const recentTimestamps = requestTimestamps.filter((ts) => ts > oneMinuteAgo);

    const remaining = Math.max(0, limit - recentTimestamps.length);
    const isLimited = remaining === 0;

    // Calculate reset time (1 minute from oldest timestamp)
    let resetTime: Date | null = null;
    if (recentTimestamps.length > 0) {
      const oldestTimestamp = Math.min(...recentTimestamps);
      resetTime = new Date(oldestTimestamp + 60000);
    }

    setState({
      limit,
      remaining,
      resetTime,
      isLimited,
      warningThreshold,
    });

    setRequestTimestamps(recentTimestamps);
  }, [requestTimestamps, limit, warningThreshold]);

  // Track a new request
  const trackRequest = useCallback(() => {
    const now = Date.now();
    setRequestTimestamps((prev) => [...prev, now]);
  }, []);

  // Handle rate limit errors from backend
  const handleRateLimitError = useCallback((resetTimestamp?: number) => {
    if (resetTimestamp) {
      setState((prev) => ({
        ...prev,
        remaining: 0,
        isLimited: true,
        resetTime: new Date(resetTimestamp),
      }));
    }
  }, []);

  // Reset rate limit (for testing or manual reset)
  const reset = useCallback(() => {
    setRequestTimestamps([]);
    setState({
      limit,
      remaining: limit,
      resetTime: null,
      isLimited: false,
      warningThreshold,
    });
  }, [limit, warningThreshold]);

  // Update state periodically
  useEffect(() => {
    const interval = setInterval(updateRateLimit, 1000);
    return () => clearInterval(interval);
  }, [updateRateLimit]);

  // Check if we should show warning
  const shouldWarn = state.remaining / state.limit <= warningThreshold;

  return {
    ...state,
    shouldWarn,
    trackRequest,
    handleRateLimitError,
    reset,
  };
}
