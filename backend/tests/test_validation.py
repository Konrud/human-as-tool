"""
Tests for validation service.
"""

import pytest
from datetime import datetime, timezone, timedelta
from uuid import uuid4

from src.models.base import (
    ChatSession,
    Message,
    MessageType,
    MessageStatus,
    SessionStatus,
    ChannelType,
    FeedbackRequest,
    FeedbackResponse,
    FeedbackType,
    FeedbackStatus,
    AgentState,
    AgentStatus,
    CommunicationChannel,
    ChannelStatus,
    SessionMetadata,
    MessageMetadata,
    FeedbackMetadata,
    AgentMetadata,
    ChannelMetadata,
)
from src.services.validation import (
    ChatSessionValidator,
    MessageValidator,
    FeedbackRequestValidator,
    FeedbackResponseValidator,
    AgentStateValidator,
    CommunicationChannelValidator,
    ValidationError,
)


class TestChatSessionValidator:
    """Test ChatSession validation."""
    
    def test_validate_create_success(self):
        """Test successful session creation validation."""
        now = datetime.now(timezone.utc)
        session = ChatSession(
            id=str(uuid4()),
            user_id="user123",
            status=SessionStatus.ACTIVE,
            created_at=now,
            updated_at=now,
            preferred_channel=ChannelType.WEBSOCKET,
            messages=[],
            feedback_requests=[],
            metadata=SessionMetadata(
                user_agent="test",
                ip_address="127.0.0.1",
                last_active=now
            )
        )
        
        # Should not raise
        ChatSessionValidator.validate_create(session, active_session_count=0)
    
    def test_validate_create_max_sessions(self):
        """Test validation fails when max sessions reached."""
        now = datetime.now(timezone.utc)
        session = ChatSession(
            id=str(uuid4()),
            user_id="user123",
            status=SessionStatus.ACTIVE,
            created_at=now,
            updated_at=now,
            preferred_channel=ChannelType.WEBSOCKET,
            messages=[],
            feedback_requests=[],
            metadata=SessionMetadata(
                user_agent="test",
                ip_address="127.0.0.1",
                last_active=now
            )
        )
        
        with pytest.raises(ValidationError, match="cannot have more than"):
            ChatSessionValidator.validate_create(session, active_session_count=3)
    
    def test_validate_status_transition(self):
        """Test session status transitions."""
        # Valid transitions
        ChatSessionValidator.validate_status_transition(
            SessionStatus.ACTIVE,
            SessionStatus.PAUSED
        )
        
        ChatSessionValidator.validate_status_transition(
            SessionStatus.PAUSED,
            SessionStatus.ACTIVE
        )
        
        # Invalid transition
        with pytest.raises(ValidationError, match="Invalid status transition"):
            ChatSessionValidator.validate_status_transition(
                SessionStatus.ENDED,
                SessionStatus.ACTIVE
            )


class TestMessageValidator:
    """Test Message validation."""
    
    def test_validate_create_success(self):
        """Test successful message validation."""
        now = datetime.now(timezone.utc)
        message = Message(
            id=str(uuid4()),
            session_id=str(uuid4()),
            content="Hello world",
            type=MessageType.USER,
            timestamp=now,
            status=MessageStatus.SENT,
            channel=ChannelType.WEBSOCKET,
            metadata=MessageMetadata()
        )
        
        # Should not raise
        MessageValidator.validate_create(message)
    
    def test_validate_empty_content(self):
        """Test validation fails for empty content."""
        now = datetime.now(timezone.utc)
        message = Message(
            id=str(uuid4()),
            session_id=str(uuid4()),
            content="",
            type=MessageType.USER,
            timestamp=now,
            status=MessageStatus.SENT,
            channel=ChannelType.WEBSOCKET
        )
        
        with pytest.raises(ValidationError, match="content cannot be empty"):
            MessageValidator.validate_create(message)
    
    def test_validate_future_timestamp(self):
        """Test validation fails for future timestamp."""
        future = datetime.now(timezone.utc) + timedelta(hours=1)
        message = Message(
            id=str(uuid4()),
            session_id=str(uuid4()),
            content="Hello",
            type=MessageType.USER,
            timestamp=future,
            status=MessageStatus.SENT,
            channel=ChannelType.WEBSOCKET
        )
        
        with pytest.raises(ValidationError, match="cannot be in the future"):
            MessageValidator.validate_create(message)


class TestFeedbackRequestValidator:
    """Test FeedbackRequest validation."""
    
    def test_validate_create_success(self):
        """Test successful feedback request validation."""
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=48)
        
        feedback = FeedbackRequest(
            id=str(uuid4()),
            session_id=str(uuid4()),
            type=FeedbackType.APPROVAL,
            status=FeedbackStatus.PENDING,
            prompt="Do you approve?",
            created_at=now,
            expires_at=expires_at,
            channels=[ChannelType.WEBSOCKET],
            responses=[],
            metadata=FeedbackMetadata(
                priority=1,
                attempts_count=0,
                last_attempt=now
            )
        )
        
        # Should not raise
        FeedbackRequestValidator.validate_create(feedback)
    
    def test_validate_no_channels(self):
        """Test validation fails when no channels provided."""
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=48)
        
        feedback = FeedbackRequest(
            id=str(uuid4()),
            session_id=str(uuid4()),
            type=FeedbackType.APPROVAL,
            status=FeedbackStatus.PENDING,
            prompt="Do you approve?",
            created_at=now,
            expires_at=expires_at,
            channels=[],
            responses=[],
            metadata=FeedbackMetadata(
                priority=1,
                attempts_count=0,
                last_attempt=now
            )
        )
        
        with pytest.raises(ValidationError, match="at least one channel"):
            FeedbackRequestValidator.validate_create(feedback)


class TestRateLimiting:
    """Test rate limiting functionality."""
    
    def test_rate_limiter_import(self):
        """Test that rate limiter can be imported."""
        from src.services.rate_limiter import rate_limiter
        assert rate_limiter is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

