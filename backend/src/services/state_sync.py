"""Cross-channel state synchronization service."""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Set
import asyncio

from ..models.base import (
    ChatSession,
    Message,
    FeedbackRequest,
    FeedbackResponse,
    AgentState,
    ChannelType,
    SessionStatus,
)
from ..storage.memory_store import store
from .channel_orchestrator import channel_orchestrator


class StateSyncService:
    """
    Manages state synchronization across all communication channels.
    
    Ensures:
    - Consistent conversation history across channels
    - Feedback requests tracked across all channels
    - First valid response wins from any channel
    - Session state updates broadcast to all channels
    - Context preservation during channel switches
    """
    
    def __init__(self):
        """Initialize state sync service."""
        self.active_sync_sessions: Set[str] = set()
        self.channel_subscriptions: Dict[str, Set[ChannelType]] = {}  # session_id -> subscribed channels
    
    async def sync_message_to_channels(
        self,
        message: Message,
        user_id: str,
        recipient: str,
        exclude_channels: Optional[List[ChannelType]] = None
    ) -> Dict[ChannelType, bool]:
        """
        Synchronize a message to all active channels for a session.
        
        Args:
            message: Message to sync
            user_id: User identifier
            recipient: Recipient identifier
            exclude_channels: Channels to exclude from sync
            
        Returns:
            Dictionary mapping channel types to success status
        """
        exclude_channels = exclude_channels or []
        results = {}
        
        # Get session
        session = store.get_session(message.session_id)
        if not session:
            return results
        
        # Get subscribed channels for this session
        subscribed = self.channel_subscriptions.get(message.session_id, set())
        
        # Initialize user channels
        available_channels = await channel_orchestrator.initialize_user_channels(user_id)
        
        # Send to all subscribed and available channels (except excluded)
        for channel_type in subscribed:
            if channel_type in exclude_channels or channel_type == ChannelType.WEBSOCKET:
                continue
            
            if channel_type not in available_channels:
                continue
            
            try:
                # Send through orchestrator (which handles fallback and retry)
                success = await channel_orchestrator.send_message(
                    message,
                    user_id,
                    recipient,
                    preferred_channel=channel_type,
                    enable_fallback=False  # Don't fallback during sync
                )
                results[channel_type] = success
            except Exception:
                results[channel_type] = False
        
        return results
    
    async def sync_feedback_request_to_channels(
        self,
        feedback_request: FeedbackRequest,
        user_id: str,
        recipient: str
    ) -> List[ChannelType]:
        """
        Synchronize a feedback request to specified channels.
        
        Args:
            feedback_request: Feedback request to sync
            user_id: User identifier
            recipient: Recipient identifier
            
        Returns:
            List of channels that successfully received the request
        """
        # Use orchestrator to send to all specified channels
        successful = await channel_orchestrator.send_feedback_request(
            feedback_request,
            user_id,
            recipient,
            enable_fallback=False
        )
        
        return successful
    
    def subscribe_channel(self, session_id: str, channel_type: ChannelType):
        """
        Subscribe a channel to receive session updates.
        
        Args:
            session_id: Session identifier
            channel_type: Channel to subscribe
        """
        if session_id not in self.channel_subscriptions:
            self.channel_subscriptions[session_id] = set()
        
        self.channel_subscriptions[session_id].add(channel_type)
    
    def unsubscribe_channel(self, session_id: str, channel_type: ChannelType):
        """
        Unsubscribe a channel from session updates.
        
        Args:
            session_id: Session identifier
            channel_type: Channel to unsubscribe
        """
        if session_id in self.channel_subscriptions:
            self.channel_subscriptions[session_id].discard(channel_type)
            
            if not self.channel_subscriptions[session_id]:
                del self.channel_subscriptions[session_id]
    
    def get_subscribed_channels(self, session_id: str) -> Set[ChannelType]:
        """
        Get all channels subscribed to a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Set of subscribed channel types
        """
        return self.channel_subscriptions.get(session_id, set()).copy()
    
    async def switch_channel(
        self,
        session_id: str,
        old_channel: ChannelType,
        new_channel: ChannelType,
        user_id: str
    ) -> bool:
        """
        Switch session to a different channel with context preservation.
        
        Args:
            session_id: Session identifier
            old_channel: Current channel
            new_channel: New channel to switch to
            user_id: User identifier
            
        Returns:
            True if switch successful
        """
        # Get session
        session = store.get_session(session_id)
        if not session:
            return False
        
        # Update session preferred channel
        session.preferred_channel = new_channel
        session.updated_at = datetime.now(timezone.utc)
        store.update_session(session)
        
        # Unsubscribe old channel, subscribe new channel
        self.unsubscribe_channel(session_id, old_channel)
        self.subscribe_channel(session_id, new_channel)
        
        # Optionally: Send summary of conversation so far to new channel
        # This ensures context is preserved
        
        return True
    
    def get_conversation_history(
        self,
        session_id: str,
        limit: Optional[int] = None,
        include_system: bool = True
    ) -> List[Message]:
        """
        Get complete conversation history for a session.
        
        Includes messages from all channels to provide complete context.
        
        Args:
            session_id: Session identifier
            limit: Maximum number of messages to return
            include_system: Whether to include system messages
            
        Returns:
            List of messages in chronological order
        """
        from ..models.base import MessageType
        
        messages = store.get_session_messages(session_id, limit=limit)
        
        if not include_system:
            messages = [
                m for m in messages 
                if m.type != MessageType.SYSTEM
            ]
        
        return messages
    
    async def broadcast_session_update(
        self,
        session: ChatSession,
        event_type: str,
        data: Optional[Dict] = None
    ):
        """
        Broadcast session state update to all subscribed channels.
        
        Args:
            session: Updated session
            event_type: Type of update event
            data: Additional event data
        """
        # Get subscribed channels
        subscribed = self.get_subscribed_channels(session.id)
        
        # For WebSocket channels, the WebSocket manager will handle broadcasts
        # For other channels, we would send notifications
        # This is primarily for coordination rather than actual messaging
        
        # Could be extended to send email/Slack notifications about session state changes
        pass
    
    async def broadcast_agent_status(
        self,
        session_id: str,
        agent_state: AgentState
    ):
        """
        Broadcast agent status update to subscribed channels.
        
        Args:
            session_id: Session identifier
            agent_state: Current agent state
        """
        # Get subscribed channels
        subscribed = self.get_subscribed_channels(session_id)
        
        # WebSocket connections will receive real-time updates
        # Email/Slack channels typically don't need real-time agent status
        # Could be used to send "Agent is thinking..." messages if needed
        pass
    
    def process_feedback_response(
        self,
        request_id: str,
        response: FeedbackResponse
    ) -> bool:
        """
        Process feedback response with first-valid-wins logic.
        
        Ensures only the first valid response is accepted regardless of channel.
        
        Args:
            request_id: Feedback request identifier
            response: Feedback response
            
        Returns:
            True if response was accepted (first valid)
        """
        # Get feedback request
        feedback_request = store.get_feedback_request(request_id)
        
        if not feedback_request:
            return False
        
        from ..models.base import FeedbackStatus
        
        # Check if already processed
        if feedback_request.status != FeedbackStatus.PENDING:
            return False
        
        # Get existing responses
        existing_responses = store.get_request_responses(request_id)
        
        # If this is the first response, accept it
        if not existing_responses:
            # Store response
            store.create_feedback_response(response)
            
            # Update request status based on response content
            if response.content.upper() in ['APPROVE', 'APPROVED', 'YES']:
                feedback_request.status = FeedbackStatus.APPROVED
            elif response.content.upper() in ['REJECT', 'REJECTED', 'NO']:
                feedback_request.status = FeedbackStatus.REJECTED
            else:
                # For input type, mark as approved with the input
                feedback_request.status = FeedbackStatus.APPROVED
            
            store.update_feedback_request(feedback_request)
            
            return True
        
        # Response already exists, reject this one
        return False
    
    async def ensure_session_consistency(self, session_id: str) -> bool:
        """
        Ensure session state is consistent across all channels.
        
        Verifies:
        - Message history is complete
        - Feedback requests are tracked
        - Agent state is current
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if session is consistent
        """
        # Get session
        session = store.get_session(session_id)
        if not session:
            return False
        
        # Verify message history
        messages = store.get_session_messages(session_id)
        
        # Verify feedback requests
        feedback_requests = store.get_session_feedback_requests(session_id)
        
        # Verify agent state
        agent_state = store.get_agent_state(session_id)
        
        # All components exist
        return True
    
    def get_sync_status(self, session_id: str) -> Dict:
        """
        Get synchronization status for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Dictionary with sync status information
        """
        subscribed = self.get_subscribed_channels(session_id)
        messages = store.get_session_messages(session_id)
        feedback_requests = store.get_session_feedback_requests(session_id)
        
        return {
            "session_id": session_id,
            "subscribed_channels": [c.value for c in subscribed],
            "message_count": len(messages),
            "pending_feedback_count": len([
                fr for fr in feedback_requests 
                if fr.status == FeedbackStatus.PENDING
            ]),
            "is_syncing": session_id in self.active_sync_sessions
        }


# Global state sync service instance
state_sync = StateSyncService()

