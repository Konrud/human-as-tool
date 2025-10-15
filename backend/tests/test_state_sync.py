"""Tests for state synchronization service."""

import pytest
from datetime import datetime, timezone
import uuid

from src.services.state_sync import state_sync
from src.models.base import (
    ChatSession,
    SessionStatus,
    ChannelType,
    Message,
    MessageType,
    MessageStatus,
    FeedbackRequest,
    FeedbackResponse,
    FeedbackType,
    FeedbackStatus,
    FeedbackMetadata,
    SessionMetadata,
)
from src.storage.memory_store import store


@pytest.fixture
def test_session():
    """Create test session."""
    session_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    
    session = ChatSession(
        id=session_id,
        user_id=user_id,
        status=SessionStatus.ACTIVE,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        preferred_channel=ChannelType.WEBSOCKET,
        messages=[],
        feedback_requests=[],
        metadata=SessionMetadata(
            user_agent="test",
            ip_address="127.0.0.1",
            last_active=datetime.now(timezone.utc)
        )
    )
    
    store.create_session(session)
    return session


@pytest.fixture
def test_message(test_session):
    """Create test message."""
    message = Message(
        id=str(uuid.uuid4()),
        session_id=test_session.id,
        content="Test message",
        type=MessageType.USER,
        timestamp=datetime.now(timezone.utc),
        status=MessageStatus.SENT,
        channel=ChannelType.WEBSOCKET,
        metadata=None
    )
    
    store.create_message(message)
    return message


@pytest.fixture
def test_feedback_request(test_session):
    """Create test feedback request."""
    request = FeedbackRequest(
        id=str(uuid.uuid4()),
        session_id=test_session.id,
        type=FeedbackType.APPROVAL,
        status=FeedbackStatus.PENDING,
        prompt="Test prompt",
        created_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc),
        channels=[ChannelType.EMAIL],
        responses=[],
        metadata=FeedbackMetadata(
            priority=1,
            attempts_count=0,
            last_attempt=datetime.now(timezone.utc)
        )
    )
    
    store.create_feedback_request(request)
    return request


class TestStateSyncService:
    """Test state synchronization service."""
    
    def test_subscribe_channel(self, test_session):
        """Test subscribing a channel to session updates."""
        state_sync.subscribe_channel(test_session.id, ChannelType.EMAIL)
        
        subscribed = state_sync.get_subscribed_channels(test_session.id)
        assert ChannelType.EMAIL in subscribed
    
    def test_unsubscribe_channel(self, test_session):
        """Test unsubscribing a channel from session updates."""
        state_sync.subscribe_channel(test_session.id, ChannelType.EMAIL)
        state_sync.unsubscribe_channel(test_session.id, ChannelType.EMAIL)
        
        subscribed = state_sync.get_subscribed_channels(test_session.id)
        assert ChannelType.EMAIL not in subscribed
    
    def test_get_subscribed_channels(self, test_session):
        """Test getting subscribed channels."""
        state_sync.subscribe_channel(test_session.id, ChannelType.EMAIL)
        state_sync.subscribe_channel(test_session.id, ChannelType.SLACK)
        
        subscribed = state_sync.get_subscribed_channels(test_session.id)
        assert len(subscribed) == 2
        assert ChannelType.EMAIL in subscribed
        assert ChannelType.SLACK in subscribed
    
    @pytest.mark.asyncio
    async def test_switch_channel(self, test_session):
        """Test switching session channel."""
        success = await state_sync.switch_channel(
            test_session.id,
            ChannelType.WEBSOCKET,
            ChannelType.EMAIL,
            test_session.user_id
        )
        
        assert success
        
        # Verify session was updated
        updated_session = store.get_session(test_session.id)
        assert updated_session.preferred_channel == ChannelType.EMAIL
    
    def test_get_conversation_history(self, test_session, test_message):
        """Test getting conversation history."""
        history = state_sync.get_conversation_history(test_session.id)
        
        assert len(history) == 1
        assert history[0].id == test_message.id
    
    def test_get_conversation_history_no_system(self, test_session, test_message):
        """Test getting conversation history without system messages."""
        # Create system message
        system_msg = Message(
            id=str(uuid.uuid4()),
            session_id=test_session.id,
            content="System message",
            type=MessageType.SYSTEM,
            timestamp=datetime.now(timezone.utc),
            status=MessageStatus.SENT,
            channel=ChannelType.WEBSOCKET,
            metadata=None
        )
        store.create_message(system_msg)
        
        history = state_sync.get_conversation_history(
            test_session.id,
            include_system=False
        )
        
        # Should only include user message, not system
        assert len(history) == 1
        assert all(m.type != MessageType.SYSTEM for m in history)
    
    def test_process_feedback_response_first_wins(self, test_feedback_request):
        """Test first valid response wins logic."""
        # Create first response
        response1 = FeedbackResponse(
            id=str(uuid.uuid4()),
            request_id=test_feedback_request.id,
            content="APPROVE",
            timestamp=datetime.now(timezone.utc),
            channel=ChannelType.EMAIL
        )
        
        # Should accept first response
        accepted1 = state_sync.process_feedback_response(
            test_feedback_request.id,
            response1
        )
        assert accepted1
        
        # Create second response
        response2 = FeedbackResponse(
            id=str(uuid.uuid4()),
            request_id=test_feedback_request.id,
            content="REJECT",
            timestamp=datetime.now(timezone.utc),
            channel=ChannelType.SLACK
        )
        
        # Should reject second response
        accepted2 = state_sync.process_feedback_response(
            test_feedback_request.id,
            response2
        )
        assert not accepted2
    
    @pytest.mark.asyncio
    async def test_ensure_session_consistency(self, test_session, test_message):
        """Test ensuring session consistency."""
        consistent = await state_sync.ensure_session_consistency(test_session.id)
        assert consistent
    
    def test_get_sync_status(self, test_session, test_message):
        """Test getting sync status."""
        state_sync.subscribe_channel(test_session.id, ChannelType.EMAIL)
        
        status = state_sync.get_sync_status(test_session.id)
        
        assert status["session_id"] == test_session.id
        assert ChannelType.EMAIL.value in status["subscribed_channels"]
        assert status["message_count"] == 1
        assert "pending_feedback_count" in status
        assert "is_syncing" in status


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

