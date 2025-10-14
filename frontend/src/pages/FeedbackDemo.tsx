import { FeedbackList } from "@/components/feedback/FeedbackList";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useFeedback } from "@/hooks/useFeedback";
import type { FeedbackRequest } from "@/types/models";
import { ChannelType, FeedbackStatus, FeedbackType } from "@/types/models";
import { useState } from "react";

export function FeedbackDemo() {
  const [mockRequests, setMockRequests] = useState<FeedbackRequest[]>([
    {
      id: "req-1",
      sessionId: "session-123",
      type: FeedbackType.APPROVAL,
      status: FeedbackStatus.PENDING,
      prompt: "Do you approve deploying the new feature to production?",
      createdAt: new Date(Date.now() - 1000 * 60 * 30), // 30 minutes ago
      expiresAt: new Date(Date.now() + 1000 * 60 * 60 * 47.5), // 47.5 hours from now
      channels: [ChannelType.WEBSOCKET, ChannelType.EMAIL],
      responses: [],
      metadata: {
        priority: 1,
        attemptsCount: 1,
        lastAttempt: new Date(),
      },
    },
    {
      id: "req-2",
      sessionId: "session-123",
      type: FeedbackType.INPUT,
      status: FeedbackStatus.PENDING,
      prompt: "Please provide the API key for the third-party service integration.",
      createdAt: new Date(Date.now() - 1000 * 60 * 60), // 1 hour ago
      expiresAt: new Date(Date.now() + 1000 * 60 * 90), // 1.5 hours from now (expiring soon)
      channels: [ChannelType.WEBSOCKET],
      responses: [],
      metadata: {
        priority: 2,
        attemptsCount: 1,
        lastAttempt: new Date(),
      },
    },
    {
      id: "req-3",
      sessionId: "session-123",
      type: FeedbackType.APPROVAL,
      status: FeedbackStatus.APPROVED,
      prompt: "Approve database migration?",
      createdAt: new Date(Date.now() - 1000 * 60 * 120), // 2 hours ago
      expiresAt: new Date(Date.now() + 1000 * 60 * 60 * 46), // 46 hours from now
      channels: [ChannelType.WEBSOCKET],
      responses: [
        {
          id: "resp-1",
          requestId: "req-3",
          content: "approved",
          timestamp: new Date(Date.now() - 1000 * 60 * 90), // 1.5 hours ago
          channel: ChannelType.WEBSOCKET,
        },
      ],
      metadata: {
        priority: 1,
        attemptsCount: 1,
        lastAttempt: new Date(),
      },
    },
  ]);

  const feedback = useFeedback({
    sessionId: "session-123",
    onSubmit: (requestId, response) => {
      console.log("Feedback submitted:", { requestId, response });
      // Simulate backend updating the request status
      setMockRequests((prev) =>
        prev.map((req) =>
          req.id === requestId
            ? {
                ...req,
                status:
                  response.content === "approved"
                    ? FeedbackStatus.APPROVED
                    : response.content === "rejected"
                    ? FeedbackStatus.REJECTED
                    : FeedbackStatus.APPROVED,
                responses: [
                  ...req.responses,
                  {
                    id: `resp-${Date.now()}`,
                    requestId,
                    content: response.content || "",
                    timestamp: new Date(),
                    channel: response.channel || ChannelType.WEBSOCKET,
                  },
                ],
              }
            : req
        )
      );
    },
  });

  const handleSubmitApproval = (requestId: string, approved: boolean) => {
    const request = mockRequests.find((r) => r.id === requestId);
    if (request) {
      feedback.submitApproval(request, approved);
    }
  };

  const handleSubmitInput = (requestId: string, content: string) => {
    const request = mockRequests.find((r) => r.id === requestId);
    if (request) {
      feedback.submitInput(request, content);
    }
  };

  const addMockRequest = (type: FeedbackType) => {
    const newRequest: FeedbackRequest = {
      id: `req-${Date.now()}`,
      sessionId: "session-123",
      type,
      status: FeedbackStatus.PENDING,
      prompt:
        type === FeedbackType.APPROVAL
          ? "New approval request: Do you want to proceed with this action?"
          : "New input request: Please provide additional information.",
      createdAt: new Date(),
      expiresAt: new Date(Date.now() + 1000 * 60 * 60 * 48), // 48 hours
      channels: [ChannelType.WEBSOCKET],
      responses: [],
      metadata: {
        priority: 1,
        attemptsCount: 1,
        lastAttempt: new Date(),
      },
    };
    setMockRequests((prev) => [...prev, newRequest]);
  };

  return (
    <div className="container mx-auto p-4 max-w-4xl">
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Phase 3: Feedback Request Demo</CardTitle>
          <CardDescription>
            Test the feedback request UI with mock data. This demonstrates the pause/resume
            workflow with approval and input requests.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2">
            <Button onClick={() => addMockRequest(FeedbackType.APPROVAL)}>
              Add Approval Request
            </Button>
            <Button onClick={() => addMockRequest(FeedbackType.INPUT)} variant="outline">
              Add Input Request
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Feedback Requests</CardTitle>
          <CardDescription>
            Pending requests require action. Completed requests are collapsed by default.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <FeedbackList
            requests={mockRequests}
            onSubmitApproval={handleSubmitApproval}
            onSubmitInput={handleSubmitInput}
            loading={feedback.loading}
            errors={feedback.errors}
            getPendingRequests={feedback.getPendingRequests}
            getCompletedRequests={feedback.getCompletedRequests}
            getTimeRemaining={feedback.getTimeRemaining}
            isExpiringSoon={feedback.isExpiringSoon}
          />
        </CardContent>
      </Card>
    </div>
  );
}
