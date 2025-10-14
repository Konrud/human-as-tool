"""
Validation service for all entities in the Interactive Agent Chat System.
Implements validation rules from the data model specification.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional
from pydantic import ValidationError

from ..models.base import (
    ChatSession,
    Message,
    MessageType,
    MessageStatus,
    FeedbackRequest,
    FeedbackResponse,
    AgentState,
    AgentStatus,
    CommunicationChannel,
    ChannelType,
    SessionStatus,
    FeedbackStatus,
)


class ValidationError(Exception):
    """Custom validation error."""
    pass


class ChatSessionValidator:
    """Validator for ChatSession entities."""
    
    MAX_CONCURRENT_SESSIONS = 3
    
    @staticmethod
    def validate_create(session: ChatSession, active_session_count: int) -> None:
        """
        Validate ChatSession creation.
        
        Rules:
        - Maximum 3 concurrent active sessions per user
        - Must have valid userId and preferredChannel
        """
        if not session.user_id:
            raise ValidationError("ChatSession must have a valid user_id")
        
        if not session.preferred_channel:
            raise ValidationError("ChatSession must have a preferred_channel")
        
        if active_session_count >= ChatSessionValidator.MAX_CONCURRENT_SESSIONS:
            raise ValidationError(
                f"User cannot have more than {ChatSessionValidator.MAX_CONCURRENT_SESSIONS} active sessions"
            )
    
    @staticmethod
    def validate_update(session: ChatSession) -> None:
        """
        Validate ChatSession update.
        
        Rules:
        - Cannot update ended sessions
        """
        if session.status == SessionStatus.ENDED:
            raise ValidationError("Cannot update an ended session")
    
    @staticmethod
    def validate_status_transition(
        current_status: SessionStatus,
        new_status: SessionStatus
    ) -> None:
        """
        Validate session status transitions.
        
        Valid transitions:
        - ACTIVE -> PAUSED
        - ACTIVE -> ENDED
        - PAUSED -> ACTIVE
        - PAUSED -> ENDED
        """
        valid_transitions = {
            SessionStatus.ACTIVE: [SessionStatus.PAUSED, SessionStatus.ENDED],
            SessionStatus.PAUSED: [SessionStatus.ACTIVE, SessionStatus.ENDED],
            SessionStatus.ENDED: [],  # No transitions from ENDED
        }
        
        if new_status not in valid_transitions.get(current_status, []):
            raise ValidationError(
                f"Invalid status transition from {current_status} to {new_status}"
            )


class MessageValidator:
    """Validator for Message entities."""
    
    @staticmethod
    def validate_create(message: Message) -> None:
        """
        Validate Message creation.
        
        Rules:
        - Content cannot be empty
        - Must have valid sessionId and channel
        - Timestamp cannot be in future
        """
        if not message.content or not message.content.strip():
            raise ValidationError("Message content cannot be empty")
        
        if not message.session_id:
            raise ValidationError("Message must have a valid session_id")
        
        if not message.channel:
            raise ValidationError("Message must have a valid channel")
        
        if message.timestamp > datetime.now(timezone.utc):
            raise ValidationError("Message timestamp cannot be in the future")
    
    @staticmethod
    def validate_status_transition(
        current_status: MessageStatus,
        new_status: MessageStatus
    ) -> None:
        """
        Validate message status transitions.
        
        Valid transitions:
        - SENT -> DELIVERED
        - SENT -> FAILED
        - DELIVERED -> READ
        - FAILED -> SENT (retry)
        """
        valid_transitions = {
            MessageStatus.SENT: [MessageStatus.DELIVERED, MessageStatus.FAILED],
            MessageStatus.DELIVERED: [MessageStatus.READ],
            MessageStatus.FAILED: [MessageStatus.SENT],  # Retry
            MessageStatus.READ: [],  # Terminal state
        }
        
        if new_status not in valid_transitions.get(current_status, []):
            raise ValidationError(
                f"Invalid message status transition from {current_status} to {new_status}"
            )


class FeedbackRequestValidator:
    """Validator for FeedbackRequest entities."""
    
    EXPIRATION_HOURS = 48
    
    @staticmethod
    def validate_create(feedback_request: FeedbackRequest) -> None:
        """
        Validate FeedbackRequest creation.
        
        Rules:
        - Must have valid sessionId and type
        - ExpiresAt must be 48 hours from creation
        - Must have at least one channel
        """
        if not feedback_request.session_id:
            raise ValidationError("FeedbackRequest must have a valid session_id")
        
        if not feedback_request.type:
            raise ValidationError("FeedbackRequest must have a valid type")
        
        if not feedback_request.channels or len(feedback_request.channels) == 0:
            raise ValidationError("FeedbackRequest must have at least one channel")
        
        # Check expiration is approximately 48 hours from creation
        expected_expiration = feedback_request.created_at + timedelta(
            hours=FeedbackRequestValidator.EXPIRATION_HOURS
        )
        time_diff = abs(
            (feedback_request.expires_at - expected_expiration).total_seconds()
        )
        
        # Allow 1 minute tolerance
        if time_diff > 60:
            raise ValidationError(
                f"FeedbackRequest must expire {FeedbackRequestValidator.EXPIRATION_HOURS} hours from creation"
            )
    
    @staticmethod
    def validate_update(feedback_request: FeedbackRequest) -> None:
        """
        Validate FeedbackRequest update.
        
        Rules:
        - Cannot modify after expiration
        """
        if feedback_request.expires_at < datetime.now(timezone.utc):
            raise ValidationError("Cannot modify expired FeedbackRequest")
        
        if feedback_request.status == FeedbackStatus.EXPIRED:
            raise ValidationError("Cannot modify expired FeedbackRequest")
    
    @staticmethod
    def validate_status_transition(
        current_status: FeedbackStatus,
        new_status: FeedbackStatus
    ) -> None:
        """
        Validate feedback request status transitions.
        
        Valid transitions:
        - PENDING -> APPROVED
        - PENDING -> REJECTED
        - PENDING -> EXPIRED
        """
        valid_transitions = {
            FeedbackStatus.PENDING: [
                FeedbackStatus.APPROVED,
                FeedbackStatus.REJECTED,
                FeedbackStatus.EXPIRED,
            ],
            FeedbackStatus.APPROVED: [],  # Terminal state
            FeedbackStatus.REJECTED: [],  # Terminal state
            FeedbackStatus.EXPIRED: [],  # Terminal state
        }
        
        if new_status not in valid_transitions.get(current_status, []):
            raise ValidationError(
                f"Invalid feedback status transition from {current_status} to {new_status}"
            )


class FeedbackResponseValidator:
    """Validator for FeedbackResponse entities."""
    
    @staticmethod
    def validate_create(
        feedback_response: FeedbackResponse,
        request_status: FeedbackStatus
    ) -> None:
        """
        Validate FeedbackResponse creation.
        
        Rules:
        - Must have valid requestId
        - Content cannot be empty
        - Can only respond to pending requests
        """
        if not feedback_response.request_id:
            raise ValidationError("FeedbackResponse must have a valid request_id")
        
        if not feedback_response.content or not feedback_response.content.strip():
            raise ValidationError("FeedbackResponse content cannot be empty")
        
        if request_status != FeedbackStatus.PENDING:
            raise ValidationError(
                f"Cannot respond to feedback request with status {request_status}"
            )
    
    @staticmethod
    def validate_update(processed: bool) -> None:
        """
        Validate FeedbackResponse update.
        
        Rules:
        - Cannot modify after processing
        """
        if processed:
            raise ValidationError("Cannot modify processed FeedbackResponse")


class AgentStateValidator:
    """Validator for AgentState entities."""
    
    MAX_CONTEXT_SIZE = 100000  # 100KB
    
    @staticmethod
    def validate_create(agent_state: AgentState) -> None:
        """
        Validate AgentState creation.
        
        Rules:
        - Must have valid sessionId
        - Context size must be within limits
        """
        if not agent_state.session_id:
            raise ValidationError("AgentState must have a valid session_id")
        
        if agent_state.context:
            context_size = len(str(agent_state.context))
            if context_size > AgentStateValidator.MAX_CONTEXT_SIZE:
                raise ValidationError(
                    f"AgentState context size ({context_size}) exceeds limit "
                    f"({AgentStateValidator.MAX_CONTEXT_SIZE})"
                )
    
    @staticmethod
    def validate_consistency(
        status: AgentStatus,
        has_pending_feedback: bool
    ) -> None:
        """
        Validate AgentState consistency.
        
        Rules:
        - Cannot have conflicting status and pending actions
        - AWAITING_FEEDBACK status requires pending feedback
        """
        if status == AgentStatus.IDLE and has_pending_feedback:
            raise ValidationError(
                "Agent cannot be IDLE with pending feedback requests"
            )


class CommunicationChannelValidator:
    """Validator for CommunicationChannel entities."""
    
    MIN_PRIORITY = 1
    MAX_PRIORITY = 3
    MAX_RETRY_LIMIT = 10
    MAX_TIMEOUT_SECONDS = 3600  # 1 hour
    
    @staticmethod
    def validate_config(channel: CommunicationChannel) -> None:
        """
        Validate CommunicationChannel configuration.
        
        Rules:
        - Must have valid priority (1-3)
        - Retry limit cannot exceed 10
        - Timeout cannot exceed 1 hour
        """
        priority = channel.config.get("priority")
        if priority:
            try:
                priority_int = int(priority)
                if not (
                    CommunicationChannelValidator.MIN_PRIORITY
                    <= priority_int
                    <= CommunicationChannelValidator.MAX_PRIORITY
                ):
                    raise ValidationError(
                        f"Channel priority must be between "
                        f"{CommunicationChannelValidator.MIN_PRIORITY} and "
                        f"{CommunicationChannelValidator.MAX_PRIORITY}"
                    )
            except ValueError:
                raise ValidationError("Channel priority must be a valid integer")
        
        retry_limit = channel.config.get("retry_limit")
        if retry_limit:
            try:
                retry_int = int(retry_limit)
                if retry_int > CommunicationChannelValidator.MAX_RETRY_LIMIT:
                    raise ValidationError(
                        f"Channel retry limit cannot exceed "
                        f"{CommunicationChannelValidator.MAX_RETRY_LIMIT}"
                    )
            except ValueError:
                raise ValidationError("Channel retry_limit must be a valid integer")
        
        timeout = channel.config.get("timeout")
        if timeout:
            try:
                timeout_int = int(timeout)
                if timeout_int > CommunicationChannelValidator.MAX_TIMEOUT_SECONDS:
                    raise ValidationError(
                        f"Channel timeout cannot exceed "
                        f"{CommunicationChannelValidator.MAX_TIMEOUT_SECONDS} seconds"
                    )
            except ValueError:
                raise ValidationError("Channel timeout must be a valid integer")


# Convenience functions for validation

def validate_chat_session(
    session: ChatSession,
    active_session_count: int = 0,
    is_update: bool = False
) -> None:
    """Validate a ChatSession."""
    if is_update:
        ChatSessionValidator.validate_update(session)
    else:
        ChatSessionValidator.validate_create(session, active_session_count)


def validate_message(message: Message) -> None:
    """Validate a Message."""
    MessageValidator.validate_create(message)


def validate_feedback_request(
    feedback_request: FeedbackRequest,
    is_update: bool = False
) -> None:
    """Validate a FeedbackRequest."""
    if is_update:
        FeedbackRequestValidator.validate_update(feedback_request)
    else:
        FeedbackRequestValidator.validate_create(feedback_request)


def validate_feedback_response(
    feedback_response: FeedbackResponse,
    request_status: FeedbackStatus,
    processed: bool = False
) -> None:
    """Validate a FeedbackResponse."""
    if processed:
        FeedbackResponseValidator.validate_update(processed)
    else:
        FeedbackResponseValidator.validate_create(feedback_response, request_status)


def validate_agent_state(
    agent_state: AgentState,
    has_pending_feedback: bool = False
) -> None:
    """Validate an AgentState."""
    AgentStateValidator.validate_create(agent_state)
    AgentStateValidator.validate_consistency(
        agent_state.status,
        has_pending_feedback
    )


def validate_communication_channel(channel: CommunicationChannel) -> None:
    """Validate a CommunicationChannel."""
    CommunicationChannelValidator.validate_config(channel)

