"""
Email service for handling Gmail integration.
"""

from typing import Optional, Dict, List
import base64
from email.mime.text import MIMEText
from datetime import datetime
import json
import aiohttp
from fastapi import HTTPException
from ..config import settings
from ..models.base import Message, ChannelType, MessageType
from .session_service import session_service


class EmailService:
    """Service for handling Gmail API interactions."""
    
    def __init__(self):
        """Initialize the email service."""
        self.token_cache: Dict[str, Dict] = {}  # user_id -> token info
        self.base_url = "https://gmail.googleapis.com"
        
    async def get_auth_url(self) -> str:
        """Get the Gmail OAuth2 authorization URL."""
        scope = "https://www.googleapis.com/auth/gmail.send"
        params = {
            "client_id": settings.gmail_client_id,
            "redirect_uri": settings.gmail_redirect_uri,
            "scope": scope,
            "response_type": "code",
            "access_type": "offline",
            "prompt": "consent"
        }
        
        # Construct auth URL
        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"https://accounts.google.com/o/oauth2/v2/auth?{query}"
        
    async def exchange_code(self, code: str) -> Dict:
        """Exchange authorization code for access token."""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": settings.gmail_client_id,
                    "client_secret": settings.gmail_client_secret,
                    "code": code,
                    "redirect_uri": settings.gmail_redirect_uri,
                    "grant_type": "authorization_code"
                }
            ) as resp:
                if resp.status != 200:
                    raise HTTPException(
                        status_code=400,
                        detail="Failed to exchange authorization code"
                    )
                return await resp.json()
                
    async def refresh_token(self, refresh_token: str) -> Dict:
        """Refresh access token using refresh token."""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": settings.gmail_client_id,
                    "client_secret": settings.gmail_client_secret,
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token"
                }
            ) as resp:
                if resp.status != 200:
                    raise HTTPException(
                        status_code=400,
                        detail="Failed to refresh token"
                    )
                return await resp.json()

    async def send_message(
        self,
        session_id: str,
        content: str,
        to_email: str,
        access_token: str
    ) -> Message:
        """Send an email message via Gmail API."""
        # Create email message
        message = MIMEText(content)
        message["to"] = to_email
        message["subject"] = f"Chat Session {session_id}"
        
        # Encode message
        raw = base64.urlsafe_b64encode(
            message.as_bytes()
        ).decode("utf-8")
        
        # Send via Gmail API
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            async with session.post(
                f"{self.base_url}/gmail/v1/users/me/messages/send",
                headers=headers,
                json={"raw": raw}
            ) as resp:
                if resp.status != 200:
                    raise HTTPException(
                        status_code=500,
                        detail="Failed to send email"
                    )
                result = await resp.json()
                
        # Create message record
        email_message = session_service.create_message(
            session_id=session_id,
            content=content,
            message_type=MessageType.AGENT,
            channel=ChannelType.EMAIL,
            metadata={
                "gmail_message_id": result["id"],
                "to": to_email,
                "sent_at": datetime.utcnow().isoformat()
            }
        )
        
        return email_message


# Global email service instance
email_service = EmailService()