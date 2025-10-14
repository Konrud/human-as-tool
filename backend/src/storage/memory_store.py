from typing import Dict, List, Optional, Set
from datetime import datetime
from ..models.user import User
from ..models.base import ChatSession, SessionStatus


class MemoryStore:
    """In-memory storage for users, sessions, and rate limiting."""
    
    def __init__(self):
        # User storage
        self.users: Dict[str, User] = {}
        self.users_by_username: Dict[str, str] = {}  # username -> user_id
        self.users_by_email: Dict[str, str] = {}  # email -> user_id
        
        # Session storage
        self.sessions: Dict[str, ChatSession] = {}
        self.user_sessions: Dict[str, Set[str]] = {}  # user_id -> session_ids
        
        # Rate limiting storage
        self.rate_limits: Dict[str, List[datetime]] = {}  # key -> timestamps
    
    # ==================== User Operations ====================
    
    def create_user(self, user: User) -> User:
        """Create a new user in storage."""
        self.users[user.id] = user
        self.users_by_username[user.username] = user.id
        self.users_by_email[user.email] = user.id
        return user
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        return self.users.get(user_id)
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        user_id = self.users_by_username.get(username)
        return self.users.get(user_id) if user_id else None
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        user_id = self.users_by_email.get(email)
        return self.users.get(user_id) if user_id else None
    
    def update_user(self, user: User) -> User:
        """Update an existing user."""
        if user.id in self.users:
            self.users[user.id] = user
        return user
    
    # ==================== Session Operations ====================
    
    def create_session(self, session: ChatSession) -> ChatSession:
        """Create a new chat session."""
        self.sessions[session.id] = session
        if session.user_id not in self.user_sessions:
            self.user_sessions[session.user_id] = set()
        self.user_sessions[session.user_id].add(session.id)
        return session
    
    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """Get session by ID."""
        return self.sessions.get(session_id)
    
    def get_user_sessions(self, user_id: str) -> List[ChatSession]:
        """Get all sessions for a user."""
        session_ids = self.user_sessions.get(user_id, set())
        return [
            self.sessions[sid] 
            for sid in session_ids 
            if sid in self.sessions
        ]
    
    def get_user_active_sessions(self, user_id: str) -> List[ChatSession]:
        """Get all active sessions for a user."""
        session_ids = self.user_sessions.get(user_id, set())
        return [
            self.sessions[sid] 
            for sid in session_ids 
            if sid in self.sessions and self.sessions[sid].status == SessionStatus.ACTIVE
        ]
    
    def update_session(self, session: ChatSession) -> ChatSession:
        """Update an existing session."""
        if session.id in self.sessions:
            self.sessions[session.id] = session
        return session
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            # Remove from user sessions
            if session.user_id in self.user_sessions:
                self.user_sessions[session.user_id].discard(session_id)
                if not self.user_sessions[session.user_id]:
                    del self.user_sessions[session.user_id]
            # Remove session
            del self.sessions[session_id]
            return True
        return False
    
    # ==================== Rate Limiting ====================
    
    def check_rate_limit(self, key: str, limit: int, window_seconds: int) -> bool:
        """
        Check if a rate limit is exceeded.
        
        Args:
            key: Unique identifier for the rate limit (e.g., user_id, session_id)
            limit: Maximum number of requests allowed
            window_seconds: Time window in seconds
            
        Returns:
            True if request is allowed, False if rate limit exceeded
        """
        now = datetime.utcnow()
        cutoff_timestamp = datetime.timestamp(now) - window_seconds
        
        # Initialize or clean old timestamps
        if key in self.rate_limits:
            self.rate_limits[key] = [
                ts for ts in self.rate_limits[key] 
                if datetime.timestamp(ts) > cutoff_timestamp
            ]
        else:
            self.rate_limits[key] = []
        
        # Check if limit exceeded
        if len(self.rate_limits[key]) >= limit:
            return False
        
        # Add current timestamp
        self.rate_limits[key].append(now)
        return True
    
    def get_rate_limit_status(self, key: str, limit: int, window_seconds: int) -> dict:
        """Get current rate limit status for a key."""
        now = datetime.utcnow()
        cutoff_timestamp = datetime.timestamp(now) - window_seconds
        
        # Get valid timestamps
        if key in self.rate_limits:
            valid_timestamps = [
                ts for ts in self.rate_limits[key] 
                if datetime.timestamp(ts) > cutoff_timestamp
            ]
        else:
            valid_timestamps = []
        
        remaining = max(0, limit - len(valid_timestamps))
        
        # Calculate reset time
        if valid_timestamps:
            oldest = min(valid_timestamps)
            reset_at = oldest.timestamp() + window_seconds
        else:
            reset_at = now.timestamp() + window_seconds
        
        return {
            "limit": limit,
            "remaining": remaining,
            "reset_at": reset_at,
            "window_seconds": window_seconds
        }


# Global memory store instance
store = MemoryStore()

