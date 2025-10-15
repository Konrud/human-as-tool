"""Tests for channel orchestrator."""

import pytest
from datetime import datetime, timezone
import uuid

from src.services.channel_orchestrator import channel_orchestrator
from src.models.base import (
    Message,
    MessageType,
    MessageStatus,
    ChannelType,
    FeedbackRequest,
    FeedbackType,
    FeedbackStatus,
    FeedbackMetadata,
)
from src.storage.memory_store import store


@pytest.fixture
def test_user_id():
    """Create test user ID."""
    return str(uuid.uuid4())


@pytest.fixture
def test_session_id():
    """Create test session ID."""
    return str(uuid.uuid4())


@pytest.fixture
def test_message(test_session_id):
    """Create test message."""
    return Message(
        id=str(uuid.uuid4()),
        session_id=test_session_id,
        content="Test message content",
        type=MessageType.AGENT,
        timestamp=datetime.now(timezone.utc),
        status=MessageStatus.SENT,
        channel=ChannelType.EMAIL,
        metadata=None
    )


@pytest.fixture
def test_feedback_request(test_session_id):
    """Create test feedback request."""
    return FeedbackRequest(
        id=str(uuid.uuid4()),
        session_id=test_session_id,
        type=FeedbackType.APPROVAL,
        status=FeedbackStatus.PENDING,
        prompt="Do you approve this action?",
        created_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc),
        channels=[ChannelType.EMAIL, ChannelType.SLACK],
        responses=[],
        metadata=FeedbackMetadata(
            priority=1,
            attempts_count=0,
            last_attempt=datetime.now(timezone.utc)
        )
    )


class TestChannelOrchestrator:
    """Test channel orchestrator functionality."""
    
    @pytest.mark.asyncio
    async def test_initialize_user_channels(self, test_user_id):
        """Test initializing user channels."""
        # Without connections, should return empty list
        channels = await channel_orchestrator.initialize_user_channels(test_user_id)
        assert isinstance(channels, list)
    
    @pytest.mark.asyncio
    async def test_get_channel_health(self, test_user_id):
        """Test getting channel health status."""
        health = await channel_orchestrator.get_channel_health(test_user_id)
        assert isinstance(health, dict)
    
    @pytest.mark.asyncio
    async def test_check_all_channels_health(self, test_user_id):
        """Test checking health of all channels."""
        health = await channel_orchestrator.check_all_channels_health(test_user_id)
        assert isinstance(health, dict)
    
    def test_get_delivery_history(self, test_message):
        """Test getting delivery history for a message."""
        history = channel_orchestrator.get_delivery_history(test_message.id)
        assert isinstance(history, list)
    
    @pytest.mark.asyncio
    async def test_channel_priority_with_preferred(self, test_user_id):
        """Test channel priority determination with preferred channel."""
        priority = await channel_orchestrator._get_channel_priority(
            test_user_id,
            ChannelType.EMAIL,
            enable_fallback=True
        )
        
        assert ChannelType.EMAIL == priority[0]
        assert len(priority) > 1  # Should include fallback channels
    
    @pytest.mark.asyncio
    async def test_channel_priority_no_fallback(self, test_user_id):
        """Test channel priority without fallback."""
        priority = await channel_orchestrator._get_channel_priority(
            test_user_id,
            ChannelType.EMAIL,
            enable_fallback=False
        )
        
        assert priority == [ChannelType.EMAIL]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

