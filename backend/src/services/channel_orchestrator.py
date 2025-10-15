"""Channel orchestrator for managing multi-channel communication."""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
import uuid
import asyncio

from .channels.base_channel import BaseChannel, ChannelError, ChannelConnectionError
from .channels.gmail_channel import GmailChannel
from .channels.slack_channel import SlackChannel
from ..models.base import (
    Message,
    FeedbackRequest,
    ChannelType,
    ChannelStatus,
    MessageStatus,
    DeliveryAttempt,
)
from ..storage.memory_store import store


class ChannelOrchestrator:
    """
    Orchestrates message delivery across multiple channels.
    
    Features:
    - Intelligent channel routing based on user preferences
    - Automatic fallback on channel failures
    - Circuit breaker pattern for failing channels
    - Retry logic with exponential backoff
    - Message delivery tracking
    """
    
    def __init__(self):
        """Initialize channel orchestrator."""
        self.channels: Dict[ChannelType, BaseChannel] = {}
        self.user_channels: Dict[str, Dict[ChannelType, BaseChannel]] = {}  # user_id -> initialized channels
        
        # Default channel priority for fallback
        self.fallback_priority = [
            ChannelType.WEBSOCKET,
            ChannelType.SLACK,
            ChannelType.EMAIL
        ]
    
    async def initialize_user_channels(self, user_id: str) -> List[ChannelType]:
        """
        Initialize all available channels for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of successfully initialized channel types
        """
        initialized = []
        
        if user_id not in self.user_channels:
            self.user_channels[user_id] = {}
        
        # Try to initialize each channel type
        for channel_type in [ChannelType.EMAIL, ChannelType.SLACK]:
            try:
                channel = await self._get_or_create_channel(user_id, channel_type)
                if channel and channel.status == ChannelStatus.ACTIVE:
                    initialized.append(channel_type)
            except Exception:
                # Channel initialization failed, continue with others
                pass
        
        return initialized
    
    async def _get_or_create_channel(
        self,
        user_id: str,
        channel_type: ChannelType
    ) -> Optional[BaseChannel]:
        """
        Get or create and initialize a channel for a user.
        
        Args:
            user_id: User identifier
            channel_type: Type of channel
            
        Returns:
            Initialized channel or None
        """
        # Check if already initialized for this user
        if user_id in self.user_channels and channel_type in self.user_channels[user_id]:
            channel = self.user_channels[user_id][channel_type]
            if channel.status == ChannelStatus.ACTIVE:
                return channel
        
        # Create new channel instance
        channel: Optional[BaseChannel] = None
        
        if channel_type == ChannelType.EMAIL:
            channel = GmailChannel()
        elif channel_type == ChannelType.SLACK:
            channel = SlackChannel()
        else:
            return None
        
        # Initialize channel
        try:
            success = await channel.initialize(user_id)
            if success:
                if user_id not in self.user_channels:
                    self.user_channels[user_id] = {}
                self.user_channels[user_id][channel_type] = channel
                return channel
        except Exception:
            pass
        
        return None
    
    async def send_message(
        self,
        message: Message,
        user_id: str,
        recipient: str,
        preferred_channel: Optional[ChannelType] = None,
        enable_fallback: bool = True
    ) -> bool:
        """
        Send a message through the best available channel.
        
        Args:
            message: Message to send
            user_id: User identifier
            recipient: Channel-specific recipient identifier
            preferred_channel: Preferred channel (if any)
            enable_fallback: Whether to try fallback channels on failure
            
        Returns:
            True if message sent successfully through any channel
        """
        # Determine channel priority
        channels_to_try = await self._get_channel_priority(
            user_id,
            preferred_channel,
            enable_fallback
        )
        
        # Try each channel in priority order
        last_error = None
        
        for channel_type in channels_to_try:
            # Skip WebSocket (handled separately via WebSocket connection)
            if channel_type == ChannelType.WEBSOCKET:
                continue
            
            try:
                # Get channel
                channel = await self._get_or_create_channel(user_id, channel_type)
                
                if not channel:
                    continue
                
                # Check circuit breaker
                if not channel.circuit_breaker.can_execute():
                    continue
                
                # Record delivery attempt
                attempt = DeliveryAttempt(
                    id=str(uuid.uuid4()),
                    message_id=message.id,
                    session_id=message.session_id,
                    channel=channel_type,
                    status=MessageStatus.SENT,
                    attempt_number=len(store.get_message_delivery_attempts(message.id)) + 1,
                    attempted_at=datetime.now(timezone.utc)
                )
                store.create_delivery_attempt(attempt)
                
                # Send message
                success = await channel.send_message(
                    message,
                    recipient,
                    subject=f"Agent Message - Session {message.session_id[:8]}"
                )
                
                if success:
                    # Update attempt status
                    attempt.status = MessageStatus.DELIVERED
                    store.create_delivery_attempt(attempt)  # Update
                    return True
                
            except ChannelError as e:
                last_error = e
                # Record failed attempt
                attempt.status = MessageStatus.FAILED
                attempt.error_message = str(e)
                store.create_delivery_attempt(attempt)
                
                if not enable_fallback:
                    raise
                
                # Continue to next channel
                continue
        
        # All channels failed
        if last_error:
            raise ChannelError(f"Failed to send message through any channel: {str(last_error)}")
        
        return False
    
    async def send_feedback_request(
        self,
        feedback_request: FeedbackRequest,
        user_id: str,
        recipient: str,
        preferred_channel: Optional[ChannelType] = None,
        enable_fallback: bool = True
    ) -> List[ChannelType]:
        """
        Send a feedback request through available channels.
        
        Attempts to send through all specified channels in the request.
        
        Args:
            feedback_request: Feedback request to send
            user_id: User identifier
            recipient: Channel-specific recipient identifier
            preferred_channel: Preferred channel (if any)
            enable_fallback: Whether to try fallback channels on failure
            
        Returns:
            List of channel types that successfully sent the request
        """
        successful_channels = []
        
        # Determine channels to use
        target_channels = feedback_request.channels if feedback_request.channels else []
        
        if not target_channels and preferred_channel:
            target_channels = [preferred_channel]
        
        if not target_channels:
            # Use all available channels
            await self.initialize_user_channels(user_id)
            if user_id in self.user_channels:
                target_channels = list(self.user_channels[user_id].keys())
        
        # Try to send through each channel
        for channel_type in target_channels:
            # Skip WebSocket
            if channel_type == ChannelType.WEBSOCKET:
                continue
            
            try:
                channel = await self._get_or_create_channel(user_id, channel_type)
                
                if not channel or not channel.circuit_breaker.can_execute():
                    continue
                
                # Send feedback request
                success = await channel.request_feedback(
                    feedback_request,
                    recipient
                )
                
                if success:
                    successful_channels.append(channel_type)
                
            except ChannelError:
                # Continue with other channels
                continue
        
        return successful_channels
    
    async def _get_channel_priority(
        self,
        user_id: str,
        preferred_channel: Optional[ChannelType],
        enable_fallback: bool
    ) -> List[ChannelType]:
        """
        Determine channel priority order for sending.
        
        Args:
            user_id: User identifier
            preferred_channel: User's preferred channel
            enable_fallback: Whether to include fallback channels
            
        Returns:
            Ordered list of channels to try
        """
        if not enable_fallback and preferred_channel:
            return [preferred_channel]
        
        # Start with preferred channel
        priority = []
        if preferred_channel:
            priority.append(preferred_channel)
        
        # Add fallback channels
        if enable_fallback:
            for channel_type in self.fallback_priority:
                if channel_type not in priority:
                    priority.append(channel_type)
        
        return priority
    
    async def get_channel_health(self, user_id: str) -> Dict[str, Any]:
        """
        Get health status of all channels for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Dictionary of channel health statuses
        """
        health_status = {}
        
        await self.initialize_user_channels(user_id)
        
        if user_id not in self.user_channels:
            return health_status
        
        for channel_type, channel in self.user_channels[user_id].items():
            health_status[channel_type.value] = channel.get_health_status()
        
        return health_status
    
    async def check_all_channels_health(self, user_id: str) -> Dict[ChannelType, bool]:
        """
        Check health of all channels for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Dictionary mapping channel types to health status
        """
        health = {}
        
        await self.initialize_user_channels(user_id)
        
        if user_id not in self.user_channels:
            return health
        
        # Check each channel
        for channel_type, channel in self.user_channels[user_id].items():
            try:
                is_healthy = await channel.check_health()
                health[channel_type] = is_healthy
            except Exception:
                health[channel_type] = False
        
        return health
    
    def get_delivery_history(self, message_id: str) -> List[DeliveryAttempt]:
        """
        Get delivery attempt history for a message.
        
        Args:
            message_id: Message identifier
            
        Returns:
            List of delivery attempts
        """
        return store.get_message_delivery_attempts(message_id)


# Global orchestrator instance
channel_orchestrator = ChannelOrchestrator()

