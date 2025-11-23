from typing import Dict, List, Optional, Set
from datetime import datetime, timezone
from ..models.user import User
from ..models.base import (
    ChatSession,
    SessionStatus,
    Message,
    FeedbackRequest,
    FeedbackResponse,
    AgentState,
    ChannelConnection,
    ChannelType,
    DeliveryAttempt,
)


class MemoryStore:
    """In-memory storage for users, sessions, messages, feedback, and rate limiting."""
    
    def __init__(self):
        # User storage
        self.users: Dict[str, User] = {}
        self.users_by_username: Dict[str, str] = {}  # username -> user_id
        self.users_by_email: Dict[str, str] = {}  # email -> user_id
        
        # Session storage
        self.sessions: Dict[str, ChatSession] = {}
        self.user_sessions: Dict[str, Set[str]] = {}  # user_id -> session_ids
        
        # Message storage
        self.messages: Dict[str, Message] = {}
        self.session_messages: Dict[str, List[str]] = {}  # session_id -> message_ids
        
        # Feedback storage
        self.feedback_requests: Dict[str, FeedbackRequest] = {}
        self.feedback_responses: Dict[str, FeedbackResponse] = {}
        self.session_feedbacks: Dict[str, List[str]] = {}  # session_id -> feedback_request_ids
        self.request_responses: Dict[str, List[str]] = {}  # request_id -> response_ids
        
        # Agent state storage
        self.agent_states: Dict[str, AgentState] = {}  # session_id -> agent_state
        
        # Rate limiting storage
        self.rate_limits: Dict[str, List[datetime]] = {}  # key -> timestamps
        
        # Channel connection storage
        self.channel_connections: Dict[str, ChannelConnection] = {}  # "{user_id}_{channel_type}" -> connection
        self.user_channels: Dict[str, Set[ChannelType]] = {}  # user_id -> set of connected channel types
        
        # Delivery attempt storage
        self.delivery_attempts: Dict[str, DeliveryAttempt] = {}  # attempt_id -> attempt
        self.message_attempts: Dict[str, List[str]] = {}  # message_id -> attempt_ids
    
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
        now = datetime.now(timezone.utc)
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
        now = datetime.now(timezone.utc)
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
    
    # ==================== Message Operations ====================
    
    def create_message(self, message: Message) -> Message:
        """Create a new message."""
        self.messages[message.id] = message
        if message.session_id not in self.session_messages:
            self.session_messages[message.session_id] = []
        self.session_messages[message.session_id].append(message.id)
        return message
    
    def get_message(self, message_id: str) -> Optional[Message]:
        """Get message by ID."""
        return self.messages.get(message_id)
    
    def get_session_messages(
        self,
        session_id: str,
        limit: Optional[int] = None
    ) -> List[Message]:
        """Get all messages for a session, optionally limited."""
        message_ids = self.session_messages.get(session_id, [])
        messages = [
            self.messages[mid]
            for mid in message_ids
            if mid in self.messages
        ]
        
        if limit:
            messages = messages[-limit:]
        
        return messages
    
    def update_message(self, message: Message) -> Message:
        """Update an existing message."""
        if message.id in self.messages:
            self.messages[message.id] = message
        return message
    
    # ==================== Feedback Request Operations ====================
    
    def create_feedback_request(
        self,
        feedback_request: FeedbackRequest
    ) -> FeedbackRequest:
        """Create a new feedback request."""
        self.feedback_requests[feedback_request.id] = feedback_request
        if feedback_request.session_id not in self.session_feedbacks:
            self.session_feedbacks[feedback_request.session_id] = []
        self.session_feedbacks[feedback_request.session_id].append(
            feedback_request.id
        )
        return feedback_request
    
    def get_feedback_request(
        self,
        request_id: str
    ) -> Optional[FeedbackRequest]:
        """Get feedback request by ID."""
        return self.feedback_requests.get(request_id)
    
    def get_session_feedback_requests(
        self,
        session_id: str
    ) -> List[FeedbackRequest]:
        """Get all feedback requests for a session."""
        request_ids = self.session_feedbacks.get(session_id, [])
        return [
            self.feedback_requests[rid]
            for rid in request_ids
            if rid in self.feedback_requests
        ]
    
    def update_feedback_request(
        self,
        feedback_request: FeedbackRequest
    ) -> FeedbackRequest:
        """Update an existing feedback request."""
        if feedback_request.id in self.feedback_requests:
            self.feedback_requests[feedback_request.id] = feedback_request
        return feedback_request
    
    # ==================== Feedback Response Operations ====================
    
    def create_feedback_response(
        self,
        feedback_response: FeedbackResponse
    ) -> FeedbackResponse:
        """Create a new feedback response."""
        self.feedback_responses[feedback_response.id] = feedback_response
        if feedback_response.request_id not in self.request_responses:
            self.request_responses[feedback_response.request_id] = []
        self.request_responses[feedback_response.request_id].append(
            feedback_response.id
        )
        return feedback_response
    
    def get_feedback_response(
        self,
        response_id: str
    ) -> Optional[FeedbackResponse]:
        """Get feedback response by ID."""
        return self.feedback_responses.get(response_id)
    
    def get_request_responses(
        self,
        request_id: str
    ) -> List[FeedbackResponse]:
        """Get all responses for a feedback request."""
        response_ids = self.request_responses.get(request_id, [])
        return [
            self.feedback_responses[rid]
            for rid in response_ids
            if rid in self.feedback_responses
        ]
    
    # ==================== Agent State Operations ====================
    
    def create_agent_state(self, agent_state: AgentState) -> AgentState:
        """Create or update agent state for a session."""
        self.agent_states[agent_state.session_id] = agent_state
        return agent_state
    
    def get_agent_state(self, session_id: str) -> Optional[AgentState]:
        """Get agent state for a session."""
        return self.agent_states.get(session_id)
    
    def update_agent_state(self, agent_state: AgentState) -> AgentState:
        """Update agent state for a session."""
        self.agent_states[agent_state.session_id] = agent_state
        return agent_state
    
    def delete_agent_state(self, session_id: str) -> bool:
        """Delete agent state for a session."""
        if session_id in self.agent_states:
            del self.agent_states[session_id]
            return True
        return False
    
    # ==================== Channel Connection Operations ====================
    
    def create_channel_connection(self, connection: ChannelConnection) -> ChannelConnection:
        """Create or update a channel connection."""
        key = f"{connection.user_id}_{connection.channel_type.value}"
        self.channel_connections[key] = connection
        
        # Track user's connected channels
        if connection.user_id not in self.user_channels:
            self.user_channels[connection.user_id] = set()
        self.user_channels[connection.user_id].add(connection.channel_type)
        
        return connection
    
    def get_channel_connection(
        self,
        user_id: str,
        channel_type: ChannelType
    ) -> Optional[ChannelConnection]:
        """Get channel connection for a user and channel type."""
        key = f"{user_id}_{channel_type.value}"
        return self.channel_connections.get(key)
    
    def get_user_channel_connections(self, user_id: str) -> List[ChannelConnection]:
        """Get all channel connections for a user."""
        channel_types = self.user_channels.get(user_id, set())
        connections = []
        for channel_type in channel_types:
            key = f"{user_id}_{channel_type.value}"
            if key in self.channel_connections:
                connections.append(self.channel_connections[key])
        return connections
    
    def update_channel_connection(self, connection: ChannelConnection) -> ChannelConnection:
        """Update an existing channel connection."""
        key = f"{connection.user_id}_{connection.channel_type.value}"
        if key in self.channel_connections:
            self.channel_connections[key] = connection
        return connection
    
    def delete_channel_connection(self, user_id: str, channel_type: ChannelType) -> bool:
        """Delete a channel connection."""
        key = f"{user_id}_{channel_type.value}"
        if key in self.channel_connections:
            del self.channel_connections[key]
            
            # Update user's connected channels
            if user_id in self.user_channels:
                self.user_channels[user_id].discard(channel_type)
                if not self.user_channels[user_id]:
                    del self.user_channels[user_id]
            
            return True
        return False
    
    # ==================== Delivery Attempt Operations ====================
    
    def create_delivery_attempt(self, attempt: DeliveryAttempt) -> DeliveryAttempt:
        """Create a new delivery attempt."""
        self.delivery_attempts[attempt.id] = attempt
        
        # Track attempts by message
        if attempt.message_id not in self.message_attempts:
            self.message_attempts[attempt.message_id] = []
        self.message_attempts[attempt.message_id].append(attempt.id)
        
        return attempt
    
    def get_delivery_attempt(self, attempt_id: str) -> Optional[DeliveryAttempt]:
        """Get delivery attempt by ID."""
        return self.delivery_attempts.get(attempt_id)
    
    def get_message_delivery_attempts(self, message_id: str) -> List[DeliveryAttempt]:
        """Get all delivery attempts for a message."""
        attempt_ids = self.message_attempts.get(message_id, [])
        return [
            self.delivery_attempts[aid]
            for aid in attempt_ids
            if aid in self.delivery_attempts
        ]


# Global memory store instance
store = MemoryStore()

