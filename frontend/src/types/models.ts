// Session related types
export enum SessionStatus {
  ACTIVE = "active",
  PAUSED = "paused",
  ENDED = "ended",
}

export interface ChatSession {
  id: string;
  userId: string;
  status: SessionStatus;
  createdAt: Date;
  updatedAt: Date;
  preferredChannel: ChannelType;
  messages: Message[];
  feedbackRequests: FeedbackRequest[];
  metadata: {
    userAgent: string;
    ipAddress: string;
    lastActive: Date;
  };
}

// Message related types
export enum MessageType {
  USER = "user",
  AGENT = "agent",
  SYSTEM = "system",
}

export enum MessageStatus {
  SENT = "sent",
  DELIVERED = "delivered",
  READ = "read",
  FAILED = "failed",
}

export interface Message {
  id: string;
  sessionId: string;
  content: string;
  type: MessageType;
  timestamp: Date;
  status: MessageStatus;
  channel: ChannelType;
  metadata?: {
    streamingComplete?: boolean;
    errorCount?: number;
    retryTimestamp?: Date;
  };
}

// Feedback related types
export enum FeedbackType {
  APPROVAL = "approval",
  INPUT = "input",
}

export enum FeedbackStatus {
  PENDING = "pending",
  APPROVED = "approved",
  REJECTED = "rejected",
  EXPIRED = "expired",
}

export interface FeedbackRequest {
  id: string;
  sessionId: string;
  type: FeedbackType;
  status: FeedbackStatus;
  prompt: string;
  createdAt: Date;
  expiresAt: Date;
  channels: ChannelType[];
  responses: FeedbackResponse[];
  metadata: {
    priority: number;
    attemptsCount: number;
    lastAttempt: Date;
  };
}

export interface FeedbackResponse {
  id: string;
  requestId: string;
  content: string;
  timestamp: Date;
  channel: ChannelType;
}

// Channel related types
export enum ChannelType {
  WEBSOCKET = "websocket",
  EMAIL = "email",
  SLACK = "slack",
}

export enum ChannelStatus {
  ACTIVE = "active",
  INACTIVE = "inactive",
  ERROR = "error",
  RECONNECTING = "reconnecting",
}

export interface CommunicationChannel {
  type: ChannelType;
  status: ChannelStatus;
  config: Record<string, unknown>;
  metadata: {
    lastActive: Date;
    errorCount: number;
    retryTimestamp?: Date;
  };
}

// Agent related types
export enum AgentStatus {
  IDLE = "idle",
  THINKING = "thinking",
  RESPONDING = "responding",
  ERROR = "error",
}

export interface AgentState {
  status: AgentStatus;
  sessionId: string;
  lastUpdate: Date;
  context?: Record<string, unknown>;
  metadata: {
    processingTime?: number;
    errorDetails?: string;
    retryCount?: number;
  };
}
