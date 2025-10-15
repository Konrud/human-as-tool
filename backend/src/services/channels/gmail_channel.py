"""Gmail channel handler for email communication."""

import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import json

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

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


class GmailChannel(BaseChannel):
    """
    Gmail channel implementation using Gmail API.
    
    Handles OAuth2 authentication, sending emails, and parsing replies.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize Gmail channel."""
        super().__init__(ChannelType.EMAIL, config)
        self.gmail_service = None
        self.user_email: Optional[str] = None
        
        # Gmail API configuration
        self.scopes = [
            'https://www.googleapis.com/auth/gmail.send',
            'https://www.googleapis.com/auth/gmail.readonly',
            'https://www.googleapis.com/auth/gmail.modify'
        ]
    
    async def initialize(self, user_id: str) -> bool:
        """
        Initialize Gmail connection for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            True if initialization successful
        """
        try:
            # Get channel connection from storage
            connection = store.get_channel_connection(user_id, ChannelType.EMAIL)
            
            if not connection or not connection.is_active:
                self.status = ChannelStatus.INACTIVE
                return False
            
            # Create credentials from stored tokens
            creds = Credentials(
                token=connection.access_token,
                refresh_token=connection.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=settings.gmail_client_id,
                client_secret=settings.gmail_client_secret,
                scopes=self.scopes
            )
            
            # Refresh token if expired
            if connection.token_expires_at and connection.token_expires_at < datetime.now(timezone.utc):
                if creds.refresh_token:
                    creds.refresh(Request())
                    
                    # Update stored tokens
                    connection.access_token = creds.token
                    connection.token_expires_at = creds.expiry
                    store.update_channel_connection(connection)
                else:
                    raise ChannelConnectionError("Refresh token not available")
            
            # Build Gmail service
            self.gmail_service = build('gmail', 'v1', credentials=creds)
            
            # Get user email from extra_data
            if connection.extra_data and 'email' in connection.extra_data:
                self.user_email = connection.extra_data['email']
            
            self.status = ChannelStatus.ACTIVE
            self.last_health_check = datetime.now(timezone.utc)
            return True
            
        except Exception as e:
            self.status = ChannelStatus.ERROR
            raise ChannelConnectionError(f"Failed to initialize Gmail: {str(e)}")
    
    async def send_message(
        self,
        message: Message,
        recipient: str,
        subject: Optional[str] = None,
        **kwargs
    ) -> bool:
        """
        Send a message via email.
        
        Args:
            message: Message to send
            recipient: Recipient email address
            subject: Email subject line
            **kwargs: Additional parameters
            
        Returns:
            True if message sent successfully
        """
        if not self.gmail_service:
            raise ChannelConnectionError("Gmail service not initialized")
        
        async def _send():
            try:
                # Create email message
                mime_message = MIMEMultipart('alternative')
                mime_message['to'] = recipient
                mime_message['subject'] = subject or f"Message from Agent - Session {message.session_id[:8]}"
                
                # Add session ID to headers for threading
                mime_message['X-Session-ID'] = message.session_id
                mime_message['X-Message-ID'] = message.id
                
                # Create HTML version
                html_content = self._format_message_html(message)
                mime_message.attach(MIMEText(html_content, 'html'))
                
                # Create plain text version
                mime_message.attach(MIMEText(message.content, 'plain'))
                
                # Encode and send
                raw_message = base64.urlsafe_b64encode(mime_message.as_bytes()).decode()
                
                send_result = self.gmail_service.users().messages().send(
                    userId='me',
                    body={'raw': raw_message}
                ).execute()
                
                return bool(send_result.get('id'))
                
            except HttpError as e:
                if e.resp.status == 429:
                    # Rate limit
                    retry_after = int(e.resp.get('Retry-After', 60))
                    raise ChannelRateLimitError(
                        "Gmail rate limit exceeded",
                        retry_after=retry_after
                    )
                elif e.resp.status in [401, 403]:
                    # Authentication issue
                    self.status = ChannelStatus.ERROR
                    raise ChannelConnectionError(f"Gmail authentication failed: {str(e)}")
                else:
                    raise ChannelError(f"Gmail send failed: {str(e)}")
        
        return await self.execute_with_retry(_send, max_retries=3)
    
    async def request_feedback(
        self,
        feedback_request: FeedbackRequest,
        recipient: str,
        **kwargs
    ) -> bool:
        """
        Send a feedback request via email.
        
        Args:
            feedback_request: Feedback request to send
            recipient: Recipient email address
            **kwargs: Additional parameters
            
        Returns:
            True if request sent successfully
        """
        if not self.gmail_service:
            raise ChannelConnectionError("Gmail service not initialized")
        
        async def _send():
            try:
                # Create email message
                mime_message = MIMEMultipart('alternative')
                mime_message['to'] = recipient
                
                if feedback_request.type == FeedbackType.APPROVAL:
                    mime_message['subject'] = f"Approval Required - {feedback_request.prompt[:50]}"
                else:
                    mime_message['subject'] = f"Input Required - {feedback_request.prompt[:50]}"
                
                # Add tracking headers
                mime_message['X-Session-ID'] = feedback_request.session_id
                mime_message['X-Feedback-Request-ID'] = feedback_request.id
                mime_message['X-Feedback-Type'] = feedback_request.type.value
                
                # Create HTML version
                html_content = self._format_feedback_html(feedback_request)
                mime_message.attach(MIMEText(html_content, 'html'))
                
                # Create plain text version
                plain_content = self._format_feedback_plain(feedback_request)
                mime_message.attach(MIMEText(plain_content, 'plain'))
                
                # Encode and send
                raw_message = base64.urlsafe_b64encode(mime_message.as_bytes()).decode()
                
                send_result = self.gmail_service.users().messages().send(
                    userId='me',
                    body={'raw': raw_message}
                ).execute()
                
                return bool(send_result.get('id'))
                
            except HttpError as e:
                if e.resp.status == 429:
                    retry_after = int(e.resp.get('Retry-After', 60))
                    raise ChannelRateLimitError(
                        "Gmail rate limit exceeded",
                        retry_after=retry_after
                    )
                elif e.resp.status in [401, 403]:
                    self.status = ChannelStatus.ERROR
                    raise ChannelConnectionError(f"Gmail authentication failed: {str(e)}")
                else:
                    raise ChannelError(f"Gmail send failed: {str(e)}")
        
        return await self.execute_with_retry(_send, max_retries=3)
    
    async def check_health(self) -> bool:
        """
        Check Gmail API connectivity.
        
        Returns:
            True if Gmail is accessible
        """
        if not self.gmail_service:
            return False
        
        try:
            # Simple API call to check connectivity
            self.gmail_service.users().getProfile(userId='me').execute()
            self.status = ChannelStatus.ACTIVE
            self.last_health_check = datetime.now(timezone.utc)
            return True
        except Exception:
            self.status = ChannelStatus.ERROR
            return False
    
    def _format_message_html(self, message: Message) -> str:
        """Format agent message as HTML email."""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #4F46E5; color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
                .content {{ background-color: #f9fafb; padding: 20px; border: 1px solid #e5e7eb; }}
                .message {{ background-color: white; padding: 15px; border-radius: 6px; margin: 10px 0; }}
                .footer {{ font-size: 12px; color: #6b7280; margin-top: 20px; padding-top: 20px; border-top: 1px solid #e5e7eb; }}
                .timestamp {{ font-size: 12px; color: #9ca3af; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>Message from Agent</h2>
                </div>
                <div class="content">
                    <div class="message">
                        <p>{message.content}</p>
                    </div>
                    <p class="timestamp">Sent: {message.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                </div>
                <div class="footer">
                    <p>Session ID: {message.session_id}</p>
                    <p>Reply to this email to continue the conversation.</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _format_feedback_html(self, feedback_request: FeedbackRequest) -> str:
        """Format feedback request as HTML email."""
        if feedback_request.type == FeedbackType.APPROVAL:
            action_section = """
            <div style="margin: 20px 0;">
                <p><strong>Reply with one of:</strong></p>
                <ul>
                    <li><strong>APPROVE</strong> or <strong>YES</strong> to approve</li>
                    <li><strong>REJECT</strong> or <strong>NO</strong> to reject</li>
                </ul>
            </div>
            """
        else:
            action_section = """
            <div style="margin: 20px 0;">
                <p><strong>Reply with your input:</strong></p>
                <p>Simply reply to this email with your response.</p>
            </div>
            """
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #DC2626; color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
                .content {{ background-color: #f9fafb; padding: 20px; border: 1px solid #e5e7eb; }}
                .request {{ background-color: white; padding: 15px; border-radius: 6px; margin: 10px 0; border-left: 4px solid #DC2626; }}
                .footer {{ font-size: 12px; color: #6b7280; margin-top: 20px; padding-top: 20px; border-top: 1px solid #e5e7eb; }}
                .expires {{ color: #DC2626; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>{'Approval' if feedback_request.type == FeedbackType.APPROVAL else 'Input'} Required</h2>
                </div>
                <div class="content">
                    <div class="request">
                        <p>{feedback_request.prompt}</p>
                    </div>
                    {action_section}
                    <p class="expires">Expires: {feedback_request.expires_at.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                </div>
                <div class="footer">
                    <p>Session ID: {feedback_request.session_id}</p>
                    <p>Request ID: {feedback_request.id}</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _format_feedback_plain(self, feedback_request: FeedbackRequest) -> str:
        """Format feedback request as plain text email."""
        if feedback_request.type == FeedbackType.APPROVAL:
            action = "Reply with APPROVE/YES or REJECT/NO"
        else:
            action = "Reply with your input"
        
        return f"""
{'APPROVAL' if feedback_request.type == FeedbackType.APPROVAL else 'INPUT'} REQUIRED

{feedback_request.prompt}

{action}

Expires: {feedback_request.expires_at.strftime('%Y-%m-%d %H:%M:%S UTC')}

---
Session ID: {feedback_request.session_id}
Request ID: {feedback_request.id}
        """

