"""
Tests for session service.
"""

import pytest
from datetime import datetime
from uuid import uuid4

from src.models.base import (
    ChannelType,
    MessageType,
    FeedbackType,
    SessionStatus,
)
from src.services.session_service import session_service
from src.services.validation import ValidationError
from src.storage.memory_store import MemoryStore


@pytest.fixture
def clean_store():
    """Provide a clean memory store for each test."""
    from src.storage import memory_store
    memory_store.store = MemoryStore()
    yield memory_store.store


class TestSessionService:
    """Test session service operations."""
    
    def test_create_session(self, clean_store):
        """Test session creation."""
        session = session_service.create_session(
            user_id="user123",
            preferred_channel=ChannelType.WEBSOCKET,
            user_agent="test-agent",
            ip_address="127.0.0.1"
        )
        
        assert session.id is not None
        assert session.user_id == "user123"
        assert session.status == SessionStatus.ACTIVE
        assert session.preferred_channel == ChannelType.WEBSOCKET
    
    def test_create_session_max_limit(self, clean_store):
        """Test session creation fails at max limit."""
        user_id = "user123"
        
        # Create 3 sessions
        for _ in range(3):
            session_service.create_session(
                user_id=user_id,
                preferred_channel=ChannelType.WEBSOCKET,
                user_agent="test",
                ip_address="127.0.0.1"
            )
        
        # Fourth should fail
        with pytest.raises(ValidationError, match="cannot have more than"):
            session_service.create_session(
                user_id=user_id,
                preferred_channel=ChannelType.WEBSOCKET,
                user_agent="test",
                ip_address="127.0.0.1"
            )
    
    def test_create_message(self, clean_store):
        """Test message creation."""
        # Create session first
        session = session_service.create_session(
            user_id="user123",
            preferred_channel=ChannelType.WEBSOCKET,
            user_agent="test",
            ip_address="127.0.0.1"
        )
        
        # Create message
        message = session_service.create_message(
            session_id=session.id,
            content="Hello world",
            message_type=MessageType.USER,
            channel=ChannelType.WEBSOCKET
        )
        
        assert message.id is not None
        assert message.content == "Hello world"
        assert message.session_id == session.id
    
    def test_get_session_messages(self, clean_store):
        """Test retrieving session messages."""
        # Create session
        session = session_service.create_session(
            user_id="user123",
            preferred_channel=ChannelType.WEBSOCKET,
            user_agent="test",
            ip_address="127.0.0.1"
        )
        
        # Create messages
        for i in range(5):
            session_service.create_message(
                session_id=session.id,
                content=f"Message {i}",
                message_type=MessageType.USER,
                channel=ChannelType.WEBSOCKET
            )
        
        # Retrieve all messages
        messages = session_service.get_session_messages(session.id)
        assert len(messages) == 5
        
        # Retrieve limited messages
        messages = session_service.get_session_messages(session.id, limit=2)
        assert len(messages) == 2
    
    def test_create_feedback_request(self, clean_store):
        """Test feedback request creation."""
        # Create session
        session = session_service.create_session(
            user_id="user123",
            preferred_channel=ChannelType.WEBSOCKET,
            user_agent="test",
            ip_address="127.0.0.1"
        )
        
        # Create feedback request
        feedback = session_service.create_feedback_request(
            session_id=session.id,
            feedback_type=FeedbackType.APPROVAL,
            prompt="Do you approve this action?",
            channels=[ChannelType.WEBSOCKET, ChannelType.EMAIL],
            priority=1
        )
        
        assert feedback.id is not None
        assert feedback.type == FeedbackType.APPROVAL
        assert len(feedback.channels) == 2
    
    def test_end_session(self, clean_store):
        """Test ending a session."""
        # Create session
        session = session_service.create_session(
            user_id="user123",
            preferred_channel=ChannelType.WEBSOCKET,
            user_agent="test",
            ip_address="127.0.0.1"
        )
        
        assert session.status == SessionStatus.ACTIVE
        
        # End session
        ended_session = session_service.end_session(session.id)
        assert ended_session.status == SessionStatus.ENDED


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

