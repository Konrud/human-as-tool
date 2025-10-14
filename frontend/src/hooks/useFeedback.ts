import type { FeedbackRequest, FeedbackResponse } from "@/types/models";
import { FeedbackStatus } from "@/types/models";
import { useCallback, useState } from "react";

interface UseFeedbackOptions {
  sessionId: string | null;
  onSubmit?: (requestId: string, response: Partial<FeedbackResponse>) => void;
}

interface FeedbackState {
  loading: Record<string, boolean>;
  errors: Record<string, string>;
}

export function useFeedback({ sessionId, onSubmit }: UseFeedbackOptions) {
  const [state, setState] = useState<FeedbackState>({
    loading: {},
    errors: {},
  });

  // Calculate time remaining until expiration
  const getTimeRemaining = useCallback((expiresAt: Date): number => {
    const now = new Date().getTime();
    const expiry = new Date(expiresAt).getTime();
    return Math.max(0, expiry - now);
  }, []);

  // Format time remaining as human-readable string
  const formatTimeRemaining = useCallback((milliseconds: number): string => {
    const hours = Math.floor(milliseconds / (1000 * 60 * 60));
    const minutes = Math.floor((milliseconds % (1000 * 60 * 60)) / (1000 * 60));

    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    }
    return `${minutes}m`;
  }, []);

  // Check if feedback is expiring soon (less than 2 hours)
  const isExpiringSoon = useCallback(
    (expiresAt: Date): boolean => {
      const remaining = getTimeRemaining(expiresAt);
      return remaining < 2 * 60 * 60 * 1000; // 2 hours in milliseconds
    },
    [getTimeRemaining]
  );

  // Check if feedback is expired
  const isExpired = useCallback(
    (expiresAt: Date): boolean => {
      return getTimeRemaining(expiresAt) === 0;
    },
    [getTimeRemaining]
  );

  // Set loading state for a specific request
  const setLoading = useCallback((requestId: string, loading: boolean) => {
    setState((prev) => ({
      ...prev,
      loading: { ...prev.loading, [requestId]: loading },
    }));
  }, []);

  // Set error state for a specific request
  const setError = useCallback((requestId: string, error: string) => {
    setState((prev) => ({
      ...prev,
      errors: { ...prev.errors, [requestId]: error },
    }));
  }, []);

  // Clear error for a specific request
  const clearError = useCallback((requestId: string) => {
    setState((prev) => {
      const { [requestId]: _, ...rest } = prev.errors;
      return { ...prev, errors: rest };
    });
  }, []);

  // Submit approval response
  const submitApproval = useCallback(
    async (request: FeedbackRequest, approved: boolean) => {
      if (!sessionId) return;

      try {
        setLoading(request.id, true);
        clearError(request.id);

        const response: Partial<FeedbackResponse> = {
          requestId: request.id,
          content: approved ? "approved" : "rejected",
          timestamp: new Date(),
          channel: request.channels[0], // Use first channel
        };

        onSubmit?.(request.id, response);
      } catch (error) {
        setError(request.id, error instanceof Error ? error.message : "Failed to submit");
      } finally {
        setLoading(request.id, false);
      }
    },
    [sessionId, onSubmit, setLoading, clearError, setError]
  );

  // Submit input response
  const submitInput = useCallback(
    async (request: FeedbackRequest, content: string) => {
      if (!sessionId) return;
      if (!content.trim()) {
        setError(request.id, "Response cannot be empty");
        return;
      }

      try {
        setLoading(request.id, true);
        clearError(request.id);

        const response: Partial<FeedbackResponse> = {
          requestId: request.id,
          content: content.trim(),
          timestamp: new Date(),
          channel: request.channels[0], // Use first channel
        };

        onSubmit?.(request.id, response);
      } catch (error) {
        setError(request.id, error instanceof Error ? error.message : "Failed to submit");
      } finally {
        setLoading(request.id, false);
      }
    },
    [sessionId, onSubmit, setLoading, clearError, setError]
  );

  // Get pending feedback requests
  const getPendingRequests = useCallback(
    (requests: FeedbackRequest[]): FeedbackRequest[] => {
      return requests.filter(
        (req) => req.status === FeedbackStatus.PENDING && !isExpired(req.expiresAt)
      );
    },
    [isExpired]
  );

  // Get completed feedback requests
  const getCompletedRequests = useCallback(
    (requests: FeedbackRequest[]): FeedbackRequest[] => {
      return requests.filter(
        (req) => req.status !== FeedbackStatus.PENDING || isExpired(req.expiresAt)
      );
    },
    [isExpired]
  );

  return {
    loading: state.loading,
    errors: state.errors,
    getTimeRemaining,
    formatTimeRemaining,
    isExpiringSoon,
    isExpired,
    submitApproval,
    submitInput,
    getPendingRequests,
    getCompletedRequests,
    clearError,
  };
}
