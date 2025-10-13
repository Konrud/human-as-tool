from datetime import datetime
from typing import Dict, Optional
from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel

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

class WebSocketMessage(BaseModel):
    type: str
    payload: Dict

async def handle_start_session(websocket: WebSocket, user_id: str, payload: Dict) -> Optional[str]:
    """Handle session start request and return session ID."""
    # Create new session
    session = ChatSession(
        id=f"session_{datetime.utcnow().timestamp()}",
        user_id=user_id,
        status=SessionStatus.ACTIVE,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        preferred_channel=ChannelType.WEBSOCKET,
        metadata={
            "user_agent": websocket.headers.get("user-agent", "unknown"),
            "ip_address": websocket.client.host,
            "last_active": datetime.utcnow(),
        }
    )

    # Connect WebSocket to session
    await manager.connect(websocket, session.id, user_id)

    # Send session confirmation
    await websocket.send_json({
        "type": "session_started",
        "payload": session.model_dump()
    })

    return session.id

async def handle_message(websocket: WebSocket, session_id: str, payload: Dict):
    """Handle incoming chat message."""
    content = payload.get("content")
    if not content:
        await websocket.send_json({
            "type": "error",
            "payload": "Message content is required"
        })
        return

    # Create and send message
    message = Message(
        id=f"msg_{datetime.utcnow().timestamp()}",
        session_id=session_id,
        content=content,
        type=MessageType.USER,
        timestamp=datetime.utcnow(),
        status=MessageStatus.SENT,
        channel=ChannelType.WEBSOCKET
    )

    await websocket.send_json({
        "type": "message_received",
        "payload": message.model_dump()
    })

    # Update agent status to thinking
    await websocket.send_json({
        "type": "agent_status",
        "payload": AgentStatus.THINKING
    })

    # TODO: Process message through agent
    # For now, send echo response
    response = Message(
        id=f"msg_{datetime.utcnow().timestamp()}",
        session_id=session_id,
        content=f"Echo: {content}",
        type=MessageType.AGENT,
        timestamp=datetime.utcnow(),
        status=MessageStatus.SENT,
        channel=ChannelType.WEBSOCKET
    )

    await websocket.send_json({
        "type": "message",
        "payload": response.model_dump()
    })

    # Update agent status back to idle
    await websocket.send_json({
        "type": "agent_status",
        "payload": AgentStatus.IDLE
    })

async def handle_client_connection(websocket: WebSocket, user_id: str):
    """Handle main WebSocket client connection lifecycle."""
    session_id = None
    
    try:
        while True:
            # Receive and parse message
            raw_message = await websocket.receive_text()
            try:
                message = WebSocketMessage.model_validate_json(raw_message)
            except:
                await websocket.send_json({
                    "type": "error",
                    "payload": "Invalid message format"
                })
                continue

            # Handle different message types
            if message.type == "start_session":
                if session_id:
                    await websocket.send_json({
                        "type": "error",
                        "payload": "Session already started"
                    })
                else:
                    session_id = await handle_start_session(websocket, user_id, message.payload)

            elif message.type == "message":
                if not session_id:
                    await websocket.send_json({
                        "type": "error",
                        "payload": "No active session"
                    })
                else:
                    await handle_message(websocket, session_id, message.payload)

            else:
                await websocket.send_json({
                    "type": "error",
                    "payload": f"Unknown message type: {message.type}"
                })

    except WebSocketDisconnect:
        if session_id:
            manager.disconnect(session_id)
    except:
        if session_id:
            manager.disconnect(session_id)
        raise