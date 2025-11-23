"""Slack channel handler for Slack messaging."""

from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
import json

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from .base_channel import (
    BaseChannel,
    ChannelError,
    ChannelConnectionError,
    ChannelRateLimitError,
)
from ...models.base import (
    Message,
    FeedbackRequest,
    ChannelType,
    ChannelStatus,
    FeedbackType,
)
from ...storage.memory_store import store
from ...config import settings


class SlackChannel(BaseChannel):
    """
    Slack channel implementation using Slack SDK.
    
    Handles OAuth2 authentication, sending messages with interactive buttons,
    and processing user interactions.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize Slack channel."""
        super().__init__(ChannelType.SLACK, config)
        self.slack_client: Optional[WebClient] = None
        self.bot_user_id: Optional[str] = None
    
    async def initialize(self, user_id: str) -> bool:
        """
        Initialize Slack connection for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            True if initialization successful
        """
        try:
            # Get channel connection from storage
            connection = store.get_channel_connection(user_id, ChannelType.SLACK)
            
            if not connection or not connection.is_active:
                self.status = ChannelStatus.INACTIVE
                return False
            
            # Create Slack client with bot token
            self.slack_client = WebClient(token=connection.access_token)
            
            # Get bot user ID from extra_data
            if connection.extra_data and 'bot_user_id' in connection.extra_data:
                self.bot_user_id = connection.extra_data['bot_user_id']
            
            # Test authentication
            response = self.slack_client.auth_test()
            if not response['ok']:
                raise ChannelConnectionError("Slack authentication failed")
            
            self.status = ChannelStatus.ACTIVE
            self.last_health_check = datetime.now(timezone.utc)
            return True
            
        except SlackApiError as e:
            self.status = ChannelStatus.ERROR
            raise ChannelConnectionError(f"Failed to initialize Slack: {str(e)}")
        except Exception as e:
            self.status = ChannelStatus.ERROR
            raise ChannelConnectionError(f"Failed to initialize Slack: {str(e)}")
    
    async def send_message(
        self,
        message: Message,
        recipient: str,
        **kwargs
    ) -> bool:
        """
        Send a message via Slack.
        
        Args:
            message: Message to send
            recipient: Slack user ID
            **kwargs: Additional parameters
            
        Returns:
            True if message sent successfully
        """
        if not self.slack_client:
            raise ChannelConnectionError("Slack client not initialized")
        
        async def _send():
            try:
                # Format message blocks
                blocks = self._format_message_blocks(message)
                
                # Send message
                response = self.slack_client.chat_postMessage(
                    channel=recipient,
                    text=message.content,  # Fallback text
                    blocks=blocks,
                    metadata={
                        "event_type": "agent_message",
                        "event_payload": {
                            "session_id": message.session_id,
                            "message_id": message.id
                        }
                    }
                )
                
                return response['ok']
                
            except SlackApiError as e:
                if e.response['error'] == 'ratelimited':
                    # Rate limit
                    retry_after = int(e.response.headers.get('Retry-After', 60))
                    raise ChannelRateLimitError(
                        "Slack rate limit exceeded",
                        retry_after=retry_after
                    )
                elif e.response['error'] in ['invalid_auth', 'token_revoked', 'account_inactive']:
                    # Authentication issue
                    self.status = ChannelStatus.ERROR
                    raise ChannelConnectionError(f"Slack authentication failed: {e.response['error']}")
                else:
                    raise ChannelError(f"Slack send failed: {e.response['error']}")
        
        return await self.execute_with_retry(_send, max_retries=3)
    
    async def request_feedback(
        self,
        feedback_request: FeedbackRequest,
        recipient: str,
        **kwargs
    ) -> bool:
        """
        Send a feedback request via Slack with interactive buttons.
        
        Args:
            feedback_request: Feedback request to send
            recipient: Slack user ID
            **kwargs: Additional parameters
            
        Returns:
            True if request sent successfully
        """
        if not self.slack_client:
            raise ChannelConnectionError("Slack client not initialized")
        
        async def _send():
            try:
                # Format feedback blocks with buttons
                blocks = self._format_feedback_blocks(feedback_request)
                
                # Send message
                response = self.slack_client.chat_postMessage(
                    channel=recipient,
                    text=feedback_request.prompt,  # Fallback text
                    blocks=blocks,
                    metadata={
                        "event_type": "feedback_request",
                        "event_payload": {
                            "session_id": feedback_request.session_id,
                            "request_id": feedback_request.id,
                            "type": feedback_request.type.value
                        }
                    }
                )
                
                return response['ok']
                
            except SlackApiError as e:
                if e.response['error'] == 'ratelimited':
                    retry_after = int(e.response.headers.get('Retry-After', 60))
                    raise ChannelRateLimitError(
                        "Slack rate limit exceeded",
                        retry_after=retry_after
                    )
                elif e.response['error'] in ['invalid_auth', 'token_revoked', 'account_inactive']:
                    self.status = ChannelStatus.ERROR
                    raise ChannelConnectionError(f"Slack authentication failed: {e.response['error']}")
                else:
                    raise ChannelError(f"Slack send failed: {e.response['error']}")
        
        return await self.execute_with_retry(_send, max_retries=3)
    
    async def check_health(self) -> bool:
        """
        Check Slack API connectivity.
        
        Returns:
            True if Slack is accessible
        """
        if not self.slack_client:
            return False
        
        try:
            response = self.slack_client.auth_test()
            self.status = ChannelStatus.ACTIVE if response['ok'] else ChannelStatus.ERROR
            self.last_health_check = datetime.now(timezone.utc)
            return response['ok']
        except Exception:
            self.status = ChannelStatus.ERROR
            return False
    
    def _format_message_blocks(self, message: Message) -> List[Dict[str, Any]]:
        """Format agent message as Slack blocks."""
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "💬 Message from Agent"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": message.content
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"🕐 {message.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"📝 Session: `{message.session_id[:8]}`"
                    }
                ]
            }
        ]
        return blocks
    
    def _format_feedback_blocks(self, feedback_request: FeedbackRequest) -> List[Dict[str, Any]]:
        """Format feedback request as Slack blocks with interactive buttons."""
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{'✋ Approval Required' if feedback_request.type == FeedbackType.APPROVAL else '💬 Input Required'}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": feedback_request.prompt
                }
            }
        ]
        
        # Add interactive buttons
        if feedback_request.type == FeedbackType.APPROVAL:
            blocks.append({
                "type": "actions",
                "block_id": f"feedback_{feedback_request.id}",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "✅ Approve"
                        },
                        "style": "primary",
                        "action_id": "approve",
                        "value": json.dumps({
                            "request_id": feedback_request.id,
                            "session_id": feedback_request.session_id,
                            "action": "approve"
                        })
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "❌ Reject"
                        },
                        "style": "danger",
                        "action_id": "reject",
                        "value": json.dumps({
                            "request_id": feedback_request.id,
                            "session_id": feedback_request.session_id,
                            "action": "reject"
                        })
                    }
                ]
            })
        else:
            # For input requests, add a button to open a modal
            blocks.append({
                "type": "actions",
                "block_id": f"feedback_{feedback_request.id}",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "📝 Provide Input"
                        },
                        "style": "primary",
                        "action_id": "provide_input",
                        "value": json.dumps({
                            "request_id": feedback_request.id,
                            "session_id": feedback_request.session_id,
                            "action": "input"
                        })
                    }
                ]
            })
        
        # Add context
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"⏱️ Expires: {feedback_request.expires_at.strftime('%Y-%m-%d %H:%M:%S UTC')}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"📝 Request ID: `{feedback_request.id[:8]}`"
                }
            ]
        })
        
        return blocks

