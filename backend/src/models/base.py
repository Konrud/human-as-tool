from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class SessionStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    ENDED = "ended"

class MessageType(str, Enum):
    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"

class MessageStatus(str, Enum):
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"

class FeedbackType(str, Enum):
    APPROVAL = "approval"
    INPUT = "input"

class FeedbackStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"

class ChannelType(str, Enum):
    WEBSOCKET = "websocket"
    EMAIL = "email"
    SLACK = "slack"

class ChannelStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    RECONNECTING = "reconnecting"

class AgentStatus(str, Enum):
    IDLE = "idle"
    THINKING = "thinking"
    RESPONDING = "responding"
    ERROR = "error"

class MessageMetadata(BaseModel):
    streaming_complete: Optional[bool] = None
    error_count: Optional[int] = None
    retry_timestamp: Optional[datetime] = None

class Message(BaseModel):
    id: str
    session_id: str
    content: str
    type: MessageType
    timestamp: datetime
    status: MessageStatus
    channel: ChannelType
    metadata: Optional[MessageMetadata] = None

class FeedbackResponse(BaseModel):
    id: str
    request_id: str
    content: str
    timestamp: datetime
    channel: ChannelType

class FeedbackMetadata(BaseModel):
    priority: int = Field(ge=0)
    attempts_count: int = Field(ge=0)
    last_attempt: datetime

class FeedbackRequest(BaseModel):
    id: str
    session_id: str
    type: FeedbackType
    status: FeedbackStatus
    prompt: str
    created_at: datetime
    expires_at: datetime
    channels: List[ChannelType]
    responses: List[FeedbackResponse] = []
    metadata: FeedbackMetadata

class ChannelMetadata(BaseModel):
    last_active: datetime
    error_count: int = Field(ge=0)
    retry_timestamp: Optional[datetime] = None

class CommunicationChannel(BaseModel):
    type: ChannelType
    status: ChannelStatus
    config: Dict[str, str]
    metadata: ChannelMetadata

class AgentMetadata(BaseModel):
    processing_time: Optional[float] = None
    error_details: Optional[str] = None
    retry_count: Optional[int] = Field(ge=0)

class AgentState(BaseModel):
    status: AgentStatus
    session_id: str
    last_update: datetime
    context: Optional[Dict[str, str]] = None
    metadata: AgentMetadata

class SessionMetadata(BaseModel):
    user_agent: str
    ip_address: str
    last_active: datetime

class ChatSession(BaseModel):
    id: str
    user_id: str
    status: SessionStatus
    created_at: datetime
    updated_at: datetime
    preferred_channel: ChannelType
    messages: List[Message] = []
    feedback_requests: List[FeedbackRequest] = []
    metadata: SessionMetadata