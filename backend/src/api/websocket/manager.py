from typing import Dict, Optional
from fastapi import WebSocket
from pydantic import BaseModel

class ConnectionManager:
    def __init__(self):
        # Map session_id to WebSocket connection
        self.active_connections: Dict[str, WebSocket] = {}
        # Map session_id to user_id
        self.session_users: Dict[str, str] = {}
        # Map user_id to set of session_ids
        self.user_sessions: Dict[str, set[str]] = {}

    async def connect(self, websocket: WebSocket, session_id: str, user_id: str):
        """Connect and map a WebSocket to a session and user."""
        await websocket.accept()
        
        # Store WebSocket connection
        self.active_connections[session_id] = websocket
        
        # Map session to user
        self.session_users[session_id] = user_id
        
        # Add session to user's sessions set
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = set()
        self.user_sessions[user_id].add(session_id)

    def disconnect(self, session_id: str):
        """Clean up all mappings for a disconnected session."""
        if session_id in self.session_users:
            user_id = self.session_users[session_id]
            
            # Remove session from user's sessions
            if user_id in self.user_sessions:
                self.user_sessions[user_id].discard(session_id)
                if not self.user_sessions[user_id]:
                    del self.user_sessions[user_id]
            
            # Remove session mappings
            del self.session_users[session_id]
            
        # Remove WebSocket connection
        if session_id in self.active_connections:
            del self.active_connections[session_id]

    def get_user_session_count(self, user_id: str) -> int:
        """Get the number of active sessions for a user."""
        return len(self.user_sessions.get(user_id, set()))

    def get_connection(self, session_id: str) -> Optional[WebSocket]:
        """Get the WebSocket connection for a session."""
        return self.active_connections.get(session_id)

    async def broadcast_to_user(self, user_id: str, message: BaseModel):
        """Send a message to all sessions belonging to a user."""
        if user_id in self.user_sessions:
            json_message = message.model_dump_json()
            for session_id in self.user_sessions[user_id]:
                if websocket := self.active_connections.get(session_id):
                    try:
                        await websocket.send_text(json_message)
                    except:
                        # If sending fails, clean up the connection
                        self.disconnect(session_id)

    async def send_to_session(self, session_id: str, message: BaseModel) -> bool:
        """Send a message to a specific session."""
        if websocket := self.active_connections.get(session_id):
            try:
                await websocket.send_text(message.model_dump_json())
                return True
            except:
                self.disconnect(session_id)
        return False

# Global connection manager instance
manager = ConnectionManager()