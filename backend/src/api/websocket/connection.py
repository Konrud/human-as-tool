from datetime import datetime, timezone
from typing import Dict, Optional
from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel
import asyncio
import json

from .manager import manager
from ...models.base import (
    AgentStatus,
    ChatSession,
    ChannelType,
    Message,
    MessageType,
    MessageStatus,
    SessionStatus,
)
from ...services.rate_limiter import rate_limiter, RateLimitExceeded
from ...services.session_service import session_service
from ...services.agent_service import agent_service
from ...services.validation import ValidationError

class WebSocketMessage(BaseModel):
    type: str
    payload: Dict
    
class RateLimitInfo(BaseModel):
    limited: bool = False
    retry_after: Optional[int] = None
    limit: int = 0
    remaining: int = 0
    reset_at: float = 0

async def handle_start_session(
    websocket: WebSocket,
    user_id: str,
    payload: Dict
) -> Optional[str]:
    """
    Handle session start request and return session ID.
    
    Args:
        websocket: WebSocket connection
        user_id: User identifier
        payload: Request payload
        
    Returns:
        Session ID if successful
    """
    try:
        # Get preferred channel from payload
        preferred_channel_str = payload.get("preferred_channel", "websocket")
        try:
            preferred_channel = ChannelType(preferred_channel_str)
        except ValueError:
            preferred_channel = ChannelType.WEBSOCKET
        
        # Create session via session service
        session = session_service.create_session(
            user_id=user_id,
            preferred_channel=preferred_channel,
            user_agent=websocket.headers.get("user-agent", "unknown"),
            ip_address=websocket.client.host if websocket.client else "unknown"
        )
        
        # Initialize agent state
        session_service.create_agent_state(session.id, AgentStatus.IDLE)
        
        # Connect WebSocket to session
        await manager.connect(websocket, session.id, user_id)
        
        # Send session confirmation
        await websocket.send_json({
            "type": "session_started",
            "payload": {
                "session_id": session.id,
                "status": session.status.value,
                "preferred_channel": session.preferred_channel.value,
                "created_at": session.created_at.isoformat()
            }
        })
        
        return session.id
        
    except ValidationError as e:
        await websocket.send_json({
            "type": "error",
            "payload": {
                "code": "VALIDATION_ERROR",
                "message": str(e)
            }
        })
        return None
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "payload": {
                "code": "SESSION_ERROR",
                "message": f"Failed to create session: {str(e)}"
            }
        })
        return None

async def handle_message(
    websocket: WebSocket,
    session_id: str,
    user_id: str,
    payload: Dict
):
    """
    Handle incoming chat message with rate limiting and validation.
    
    Args:
        websocket: WebSocket connection
        session_id: Session identifier
        user_id: User identifier
        payload: Message payload
    """
    try:
        # Check rate limits
        try:
            rate_limiter.check_all_limits(
                user_id=user_id,
                session_id=session_id,
                channel="websocket"
            )
        except RateLimitExceeded as e:
            await websocket.send_json({
                "type": "rate_limit_exceeded",
                "payload": {
                    "message": e.message,
                    "retry_after": e.retry_after,
                    "limit": e.limit,
                    "remaining": e.remaining,
                    "reset_at": e.reset_at
                }
            })
            return
        
        # Get message content
        content = payload.get("content")
        if not content or not content.strip():
            await websocket.send_json({
                "type": "error",
                "payload": {
                    "code": "INVALID_MESSAGE",
                    "message": "Message content is required"
                }
            })
            return
        
        # Create user message
        user_message = session_service.create_message(
            session_id=session_id,
            content=content,
            message_type=MessageType.USER,
            channel=ChannelType.WEBSOCKET
        )
        
        # Send confirmation
        await websocket.send_json({
            "type": "message_received",
            "payload": {
                "message_id": user_message.id,
                "timestamp": user_message.timestamp.isoformat()
            }
        })
        
        # Update agent status to thinking
        await websocket.send_json({
            "type": "agent_status",
            "payload": {"status": AgentStatus.THINKING.value}
        })
        
        # Check if streaming is requested
        stream = payload.get("stream", False)
        
        if stream:
            # Stream response
            await websocket.send_json({
                "type": "agent_status",
                "payload": {"status": AgentStatus.RESPONDING.value}
            })
            
            await websocket.send_json({
                "type": "stream_start",
                "payload": {}
            })
            
            try:
                async for chunk in agent_service.stream_response(session_id, content):
                    await websocket.send_json({
                        "type": "stream_chunk",
                        "payload": {"content": chunk}
                    })
                    await asyncio.sleep(0.01)  # Small delay for better streaming
                
                await websocket.send_json({
                    "type": "stream_end",
                    "payload": {}
                })
                
            except Exception as e:
                await websocket.send_json({
                    "type": "stream_error",
                    "payload": {"message": str(e)}
                })
        else:
            # Process and send complete response
            agent_message = await agent_service.process_user_message(
                session_id=session_id,
                user_message=content,
                channel=ChannelType.WEBSOCKET
            )
            
            await websocket.send_json({
                "type": "message",
                "payload": {
                    "id": agent_message.id,
                    "content": agent_message.content,
                    "type": agent_message.type.value,
                    "timestamp": agent_message.timestamp.isoformat()
                }
            })
        
        # Update agent status back to idle
        await websocket.send_json({
            "type": "agent_status",
            "payload": {"status": AgentStatus.IDLE.value}
        })
        
    except ValidationError as e:
        await websocket.send_json({
            "type": "error",
            "payload": {
                "code": "VALIDATION_ERROR",
                "message": str(e)
            }
        })
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "payload": {
                "code": "MESSAGE_ERROR",
                "message": f"Failed to process message: {str(e)}"
            }
        })
        
        # Update agent to error state
        session_service.update_agent_status(session_id, AgentStatus.ERROR)

async def handle_ping(websocket: WebSocket):
    """Handle ping/pong for connection keepalive."""
    await websocket.send_json({
        "type": "pong",
        "payload": {"timestamp": datetime.now(timezone.utc).isoformat()}
    })


async def handle_get_rate_limit_status(
    websocket: WebSocket,
    user_id: str,
    session_id: str
):
    """Send current rate limit status."""
    status = rate_limiter.get_status(
        user_id=user_id,
        session_id=session_id,
        channel="websocket"
    )
    
    await websocket.send_json({
        "type": "rate_limit_status",
        "payload": status
    })


async def handle_client_connection(websocket: WebSocket, user_id: str):
    """
    Handle main WebSocket client connection lifecycle.
    
    Supports:
    - Session management
    - Message handling with rate limiting
    - Streaming responses
    - Connection keepalive (ping/pong)
    - Rate limit status queries
    
    Args:
        websocket: WebSocket connection
        user_id: User identifier
    """
    session_id = None
    
    try:
        while True:
            # Receive and parse message
            raw_message = await websocket.receive_text()
            try:
                message = WebSocketMessage.model_validate_json(raw_message)
            except Exception as e:
                await websocket.send_json({
                    "type": "error",
                    "payload": {
                        "code": "INVALID_FORMAT",
                        "message": "Invalid message format"
                    }
                })
                continue

            # Handle different message types
            if message.type == "start_session":
                if session_id:
                    await websocket.send_json({
                        "type": "error",
                        "payload": {
                            "code": "SESSION_EXISTS",
                            "message": "Session already started"
                        }
                    })
                else:
                    session_id = await handle_start_session(
                        websocket,
                        user_id,
                        message.payload
                    )

            elif message.type == "message":
                if not session_id:
                    await websocket.send_json({
                        "type": "error",
                        "payload": {
                            "code": "NO_SESSION",
                            "message": "No active session. Start a session first."
                        }
                    })
                else:
                    await handle_message(
                        websocket,
                        session_id,
                        user_id,
                        message.payload
                    )
            
            elif message.type == "ping":
                await handle_ping(websocket)
            
            elif message.type == "get_rate_limit_status":
                if session_id:
                    await handle_get_rate_limit_status(websocket, user_id, session_id)
                else:
                    await websocket.send_json({
                        "type": "error",
                        "payload": {
                            "code": "NO_SESSION",
                            "message": "No active session"
                        }
                    })
            
            elif message.type == "end_session":
                if session_id:
                    try:
                        session_service.end_session(session_id)
                        await websocket.send_json({
                            "type": "session_ended",
                            "payload": {"session_id": session_id}
                        })
                        manager.disconnect(session_id)
                        session_id = None
                    except Exception as e:
                        await websocket.send_json({
                            "type": "error",
                            "payload": {
                                "code": "END_SESSION_ERROR",
                                "message": str(e)
                            }
                        })

            else:
                await websocket.send_json({
                    "type": "error",
                    "payload": {
                        "code": "UNKNOWN_TYPE",
                        "message": f"Unknown message type: {message.type}"
                    }
                })

    except WebSocketDisconnect:
        if session_id:
            # Don't end session on disconnect - allow reconnection
            manager.disconnect(session_id)
    except Exception as e:
        if session_id:
            manager.disconnect(session_id)
        # Log error but don't raise to prevent server crash
        print(f"WebSocket error: {e}")