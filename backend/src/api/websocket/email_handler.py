"""
Email channel handler for session messages.
"""

import asyncio
from datetime import datetime
from fastapi import HTTPException
from typing import Dict, Optional

from ...models.base import ChannelType, Message, MessageType, AgentStatus
from ...services.agent_service import agent_service
from ...services.session_service import session_service
from ...services.email_service import email_service
from ...storage.memory_store import store


async def handle_email_message(
    session_id: str,
    user_id: str,
    message: Message,
    gmail_tokens: Optional[Dict] = None
) -> Message:
    """
    Handle sending a message via email channel.
    
    Args:
        session_id: Session identifier
        user_id: User identifier
        message: Message to send
        gmail_tokens: Optional Gmail tokens
        
    Returns:
        Sent message
    """
    # Update agent status to thinking
    session_service.update_agent_status(session_id, AgentStatus.THINKING)
    
    try:
        # Get Gmail tokens if not provided
        if not gmail_tokens:
            gmail_tokens = store.get_user_data(user_id, "gmail_tokens")
            if not gmail_tokens:
                raise HTTPException(
                    status_code=401,
                    detail="Gmail authentication required"
                )
        
        # Process message via agent
        agent_message = await agent_service.process_user_message(
            session_id=session_id,
            user_message=message.content,
            channel=ChannelType.EMAIL
        )
        
        # Get user's email
        user = store.get_user(user_id)
        if not user or not user.email:
            raise HTTPException(
                status_code=400,
                detail="User email not found"
            )
            
        # Send via email service
        try:
            sent_message = await email_service.send_message(
                session_id=session_id,
                content=agent_message.content,
                to_email=user.email,
                access_token=gmail_tokens["access_token"]
            )
            
            # Update message status
            session_service.update_message_status(
                sent_message.id,
                "delivered"
            )
            
            return sent_message
            
        except Exception as e:
            # Try refreshing token if expired
            if "invalid_grant" in str(e).lower() and gmail_tokens.get("refresh_token"):
                new_tokens = await email_service.refresh_token(
                    gmail_tokens["refresh_token"]
                )
                
                # Update stored tokens
                store.set_user_data(
                    user_id,
                    "gmail_tokens",
                    {
                        "access_token": new_tokens["access_token"],
                        "refresh_token": gmail_tokens["refresh_token"],
                        "expires_at": new_tokens["expires_in"]
                    }
                )
                
                # Retry with new token
                sent_message = await email_service.send_message(
                    session_id=session_id,
                    content=agent_message.content,
                    to_email=user.email,
                    access_token=new_tokens["access_token"]
                )
                
                session_service.update_message_status(
                    sent_message.id,
                    "delivered"
                )
                
                return sent_message
            else:
                raise
                
    except Exception as e:
        # Create error message
        error_message = session_service.create_message(
            session_id=session_id,
            content=f"Failed to send email: {str(e)}",
            message_type=MessageType.SYSTEM,
            channel=ChannelType.EMAIL
        )
        
        # Update agent status to error
        session_service.update_agent_status(session_id, AgentStatus.ERROR)
        
        return error_message
    finally:
        # Reset agent status to idle
        session_service.update_agent_status(session_id, AgentStatus.IDLE)