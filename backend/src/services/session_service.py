"""
Session service for managing chat sessions, messages, and feedback requests.
Implements full lifecycle management with validation.
"""

from datetime import datetime, timezone, timedelta
from typing import List, Optional
from uuid import uuid4

from ..models.base import (
    ChatSession,
    Message,
    MessageType,
    MessageStatus,
    FeedbackRequest,
    FeedbackResponse,
    FeedbackType,
    FeedbackStatus,
    SessionStatus,
    ChannelType,
    AgentState,
    AgentStatus,
    SessionMetadata,
    MessageMetadata,
    FeedbackMetadata,
    AgentMetadata,
)
from ..storage.memory_store import store
from .validation import (
    ChatSessionValidator,
    MessageValidator,
    FeedbackRequestValidator,
    FeedbackResponseValidator,
    ValidationError,
)


class SessionService:
    """Service for managing chat sessions and related entities."""
    
    SESSION_TIMEOUT_HOURS = 24
    FEEDBACK_TIMEOUT_HOURS = 48
    
    # ==================== Session Management ====================
    
    def create_session(
        self,
        user_id: str,
        preferred_channel: ChannelType,
        user_agent: str,
        ip_address: str
    ) -> ChatSession:
        """
        Create a new chat session.
        
        Args:
            user_id: User identifier
            preferred_channel: User's preferred communication channel
            user_agent: Client user agent string
            ip_address: User's IP address
            
        Returns:
            Created ChatSession
            
        Raises:
            ValidationError: If validation fails
        """
        # Check active session count
        active_sessions = store.get_user_active_sessions(user_id)
        
        # Create session
        now = datetime.now(timezone.utc)
        session = ChatSession(
            id=str(uuid4()),
            user_id=user_id,
            status=SessionStatus.ACTIVE,
            created_at=now,
            updated_at=now,
            preferred_channel=preferred_channel,
            messages=[],
            feedback_requests=[],
            metadata=SessionMetadata(
                user_agent=user_agent,
                ip_address=ip_address,
                last_active=now
            )
        )
        
        # Validate
        ChatSessionValidator.validate_create(session, len(active_sessions))
        
        # Store
        return store.create_session(session)
    
    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """Get session by ID."""
        return store.get_session(session_id)
    
    def get_user_sessions(
        self,
        user_id: str,
        active_only: bool = False
    ) -> List[ChatSession]:
        """Get all sessions for a user."""
        if active_only:
            return store.get_user_active_sessions(user_id)
        return store.get_user_sessions(user_id)
    
    def update_session_status(
        self,
        session_id: str,
        new_status: SessionStatus
    ) -> ChatSession:
        """
        Update session status.
        
        Args:
            session_id: Session identifier
            new_status: New status
            
        Returns:
            Updated ChatSession
            
        Raises:
            ValidationError: If validation fails
        """
        session = store.get_session(session_id)
        if not session:
            raise ValidationError(f"Session {session_id} not found")
        
        # Validate status transition
        ChatSessionValidator.validate_status_transition(
            session.status,
            new_status
        )
        
        # Update
        session.status = new_status
        session.updated_at = datetime.now(timezone.utc)
        
        return store.update_session(session)
    
    def end_session(self, session_id: str) -> ChatSession:
        """End a chat session."""
        return self.update_session_status(session_id, SessionStatus.ENDED)
    
    def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions (inactive for SESSION_TIMEOUT_HOURS).
        
        Returns:
            Number of sessions cleaned up
        """
        cutoff_time = datetime.now(timezone.utc) - timedelta(
            hours=self.SESSION_TIMEOUT_HOURS
        )
        cleaned_count = 0
        
        for session in list(store.sessions.values()):
            if (session.status == SessionStatus.ACTIVE and
                session.metadata.last_active < cutoff_time):
                self.end_session(session.id)
                cleaned_count += 1
        
        return cleaned_count
    
    # ==================== Message Management ====================
    
    def create_message(
        self,
        session_id: str,
        content: str,
        message_type: MessageType,
        channel: ChannelType
    ) -> Message:
        """
        Create a new message in a session.
        
        Args:
            session_id: Session identifier
            content: Message content
            message_type: Type of message (USER, AGENT, SYSTEM)
            channel: Delivery channel
            
        Returns:
            Created Message
            
        Raises:
            ValidationError: If validation fails
        """
        # Verify session exists
        session = store.get_session(session_id)
        if not session:
            raise ValidationError(f"Session {session_id} not found")
        
        # Create message
        now = datetime.now(timezone.utc)
        message = Message(
            id=str(uuid4()),
            session_id=session_id,
            content=content,
            type=message_type,
            timestamp=now,
            status=MessageStatus.SENT,
            channel=channel,
            metadata=MessageMetadata(
                streaming_complete=True,
                error_count=0
            )
        )
        
        # Validate
        MessageValidator.validate_create(message)
        
        # Store
        stored_message = store.create_message(message)
        
        # Update session activity
        session.updated_at = now
        session.metadata.last_active = now
        store.update_session(session)
        
        return stored_message
    
    def get_session_messages(
        self,
        session_id: str,
        limit: Optional[int] = None
    ) -> List[Message]:
        """Get messages for a session."""
        return store.get_session_messages(session_id, limit)
    
    def update_message_status(
        self,
        message_id: str,
        new_status: MessageStatus
    ) -> Message:
        """
        Update message status.
        
        Args:
            message_id: Message identifier
            new_status: New status
            
        Returns:
            Updated Message
            
        Raises:
            ValidationError: If validation fails
        """
        message = store.get_message(message_id)
        if not message:
            raise ValidationError(f"Message {message_id} not found")
        
        # Validate status transition
        MessageValidator.validate_status_transition(
            message.status,
            new_status
        )
        
        # Update
        message.status = new_status
        return store.update_message(message)
    
    # ==================== Feedback Request Management ====================
    
    def create_feedback_request(
        self,
        session_id: str,
        feedback_type: FeedbackType,
        prompt: str,
        channels: List[ChannelType],
        priority: int = 1
    ) -> FeedbackRequest:
        """
        Create a new feedback request.
        
        Args:
            session_id: Session identifier
            feedback_type: Type of feedback (APPROVAL or INPUT)
            prompt: Feedback request prompt
            channels: Channels to attempt delivery
            priority: Request priority (1-3)
            
        Returns:
            Created FeedbackRequest
            
        Raises:
            ValidationError: If validation fails
        """
        # Verify session exists
        session = store.get_session(session_id)
        if not session:
            raise ValidationError(f"Session {session_id} not found")
        
        # Create feedback request
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=self.FEEDBACK_TIMEOUT_HOURS)
        
        feedback_request = FeedbackRequest(
            id=str(uuid4()),
            session_id=session_id,
            type=feedback_type,
            status=FeedbackStatus.PENDING,
            prompt=prompt,
            created_at=now,
            expires_at=expires_at,
            channels=channels,
            responses=[],
            metadata=FeedbackMetadata(
                priority=priority,
                attempts_count=0,
                last_attempt=now
            )
        )
        
        # Validate
        FeedbackRequestValidator.validate_create(feedback_request)
        
        # Store
        return store.create_feedback_request(feedback_request)
    
    def get_feedback_request(
        self,
        request_id: str
    ) -> Optional[FeedbackRequest]:
        """Get feedback request by ID."""
        return store.get_feedback_request(request_id)
    
    def get_session_feedback_requests(
        self,
        session_id: str
    ) -> List[FeedbackRequest]:
        """Get all feedback requests for a session."""
        return store.get_session_feedback_requests(session_id)
    
    def submit_feedback_response(
        self,
        request_id: str,
        content: str,
        channel: ChannelType
    ) -> FeedbackResponse:
        """
        Submit a response to a feedback request.
        
        Implements "first valid wins" logic.
        
        Args:
            request_id: Feedback request identifier
            content: Response content
            channel: Channel used for response
            
        Returns:
            Created FeedbackResponse
            
        Raises:
            ValidationError: If validation fails
        """
        # Get request
        request = store.get_feedback_request(request_id)
        if not request:
            raise ValidationError(f"FeedbackRequest {request_id} not found")
        
        # Check if already processed
        if request.status != FeedbackStatus.PENDING:
            raise ValidationError(
                f"FeedbackRequest {request_id} already processed with status {request.status}"
            )
        
        # Check expiration
        if request.expires_at < datetime.now(timezone.utc):
            # Update request status
            request.status = FeedbackStatus.EXPIRED
            store.update_feedback_request(request)
            raise ValidationError(f"FeedbackRequest {request_id} has expired")
        
        # Create response
        now = datetime.now(timezone.utc)
        response = FeedbackResponse(
            id=str(uuid4()),
            request_id=request_id,
            content=content,
            channel=channel,
            timestamp=now
        )
        
        # Validate
        FeedbackResponseValidator.validate_create(response, request.status)
        
        # Store response
        stored_response = store.create_feedback_response(response)
        
        # Update request status (first valid wins)
        if request.type == FeedbackType.APPROVAL:
            if content.lower() in ["yes", "approve", "approved", "confirm"]:
                request.status = FeedbackStatus.APPROVED
            else:
                request.status = FeedbackStatus.REJECTED
        else:
            request.status = FeedbackStatus.APPROVED  # Input received
        
        store.update_feedback_request(request)
        
        return stored_response
    
    def expire_old_feedback_requests(self) -> int:
        """
        Expire feedback requests past their expiration time.
        
        Returns:
            Number of requests expired
        """
        now = datetime.now(timezone.utc)
        expired_count = 0
        
        for request in list(store.feedback_requests.values()):
            if (request.status == FeedbackStatus.PENDING and
                request.expires_at < now):
                request.status = FeedbackStatus.EXPIRED
                store.update_feedback_request(request)
                expired_count += 1
        
        return expired_count
    
    # ==================== Agent State Management ====================
    
    def create_agent_state(
        self,
        session_id: str,
        status: AgentStatus = AgentStatus.IDLE
    ) -> AgentState:
        """Create agent state for a session."""
        now = datetime.now(timezone.utc)
        agent_state = AgentState(
            status=status,
            session_id=session_id,
            last_update=now,
            context={},
            metadata=AgentMetadata(
                processing_time=None,
                error_details=None,
                retry_count=0
            )
        )
        
        return store.create_agent_state(agent_state)
    
    def get_agent_state(self, session_id: str) -> Optional[AgentState]:
        """Get agent state for a session."""
        return store.get_agent_state(session_id)
    
    def update_agent_status(
        self,
        session_id: str,
        status: AgentStatus
    ) -> AgentState:
        """Update agent status for a session."""
        agent_state = store.get_agent_state(session_id)
        
        if not agent_state:
            # Create if doesn't exist
            agent_state = self.create_agent_state(session_id, status)
        else:
            agent_state.status = status
            agent_state.last_update = datetime.now(timezone.utc)
            store.update_agent_state(agent_state)
        
        return agent_state


# Global session service instance
session_service = SessionService()

