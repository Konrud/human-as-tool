"""
Chat REST API router for session management.
Provides HTTP endpoints for managing chat sessions and messages.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from ...api.dependencies import get_current_active_user
from ...models.user import User
from ...models.base import (
    ChatSession,
    Message,
    FeedbackRequest,
    SessionStatus,
    ChannelType,
)
from ...services.session_service import session_service
from ...services.validation import ValidationError


router = APIRouter(prefix="/api/sessions", tags=["sessions"])


# ==================== Response Models ====================

class SessionListResponse(BaseModel):
    """Response model for session list."""
    sessions: List[ChatSession]
    total: int
    active_count: int


class MessageListResponse(BaseModel):
    """Response model for message list."""
    messages: List[Message]
    total: int
    session_id: str


class FeedbackListResponse(BaseModel):
    """Response model for feedback request list."""
    feedback_requests: List[FeedbackRequest]
    total: int
    session_id: str


# ==================== Session Endpoints ====================

@router.get("/", response_model=SessionListResponse)
async def list_sessions(
    active_only: bool = False,
    current_user: User = Depends(get_current_active_user)
):
    """
    List all sessions for the current user.
    
    Args:
        active_only: If True, only return active sessions
        current_user: Authenticated user
        
    Returns:
        List of chat sessions
    """
    sessions = session_service.get_user_sessions(
        current_user.id,
        active_only=active_only
    )
    
    active_sessions = [s for s in sessions if s.status == SessionStatus.ACTIVE]
    
    return SessionListResponse(
        sessions=sessions,
        total=len(sessions),
        active_count=len(active_sessions)
    )


@router.get("/{session_id}", response_model=ChatSession)
async def get_session(
    session_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get a specific session by ID.
    
    Args:
        session_id: Session identifier
        current_user: Authenticated user
        
    Returns:
        Chat session details
        
    Raises:
        HTTPException: If session not found or unauthorized
    """
    session = session_service.get_session(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )
    
    # Check authorization
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this session"
        )
    
    return session


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def end_session(
    session_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    End a chat session.
    
    Args:
        session_id: Session identifier
        current_user: Authenticated user
        
    Raises:
        HTTPException: If session not found or unauthorized
    """
    session = session_service.get_session(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )
    
    # Check authorization
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this session"
        )
    
    try:
        session_service.end_session(session_id)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ==================== Message Endpoints ====================

@router.get("/{session_id}/messages", response_model=MessageListResponse)
async def get_session_messages(
    session_id: str,
    limit: Optional[int] = None,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all messages for a session.
    
    Args:
        session_id: Session identifier
        limit: Optional limit on number of messages
        current_user: Authenticated user
        
    Returns:
        List of messages
        
    Raises:
        HTTPException: If session not found or unauthorized
    """
    session = session_service.get_session(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )
    
    # Check authorization
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this session"
        )
    
    messages = session_service.get_session_messages(session_id, limit=limit)
    
    return MessageListResponse(
        messages=messages,
        total=len(messages),
        session_id=session_id
    )


# ==================== Feedback Endpoints ====================

@router.get("/{session_id}/feedback", response_model=FeedbackListResponse)
async def get_session_feedback_requests(
    session_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all feedback requests for a session.
    
    Args:
        session_id: Session identifier
        current_user: Authenticated user
        
    Returns:
        List of feedback requests
        
    Raises:
        HTTPException: If session not found or unauthorized
    """
    session = session_service.get_session(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )
    
    # Check authorization
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this session"
        )
    
    feedback_requests = session_service.get_session_feedback_requests(session_id)
    
    return FeedbackListResponse(
        feedback_requests=feedback_requests,
        total=len(feedback_requests),
        session_id=session_id
    )


class FeedbackResponseCreate(BaseModel):
    """Request model for creating a feedback response."""
    content: str
    channel: ChannelType = ChannelType.WEBSOCKET


@router.post("/{session_id}/feedback/{request_id}/respond", status_code=status.HTTP_201_CREATED)
async def respond_to_feedback(
    session_id: str,
    request_id: str,
    response_data: FeedbackResponseCreate,
    current_user: User = Depends(get_current_active_user)
):
    """
    Submit a response to a feedback request.
    
    Args:
        session_id: Session identifier
        request_id: Feedback request identifier
        response_data: Response content and channel
        current_user: Authenticated user
        
    Returns:
        Created feedback response
        
    Raises:
        HTTPException: If validation fails or unauthorized
    """
    session = session_service.get_session(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )
    
    # Check authorization
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this session"
        )
    
    try:
        feedback_response = session_service.submit_feedback_response(
            request_id=request_id,
            content=response_data.content,
            channel=response_data.channel
        )
        return feedback_response
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ==================== Cleanup Endpoints ====================

@router.post("/cleanup/expired", status_code=status.HTTP_200_OK)
async def cleanup_expired_sessions(
    current_user: User = Depends(get_current_active_user)
):
    """
    Cleanup expired sessions and feedback requests.
    
    Note: In production, this should be a scheduled task, not an API endpoint.
    This is provided for development and testing.
    
    Args:
        current_user: Authenticated user (admin only in production)
        
    Returns:
        Cleanup statistics
    """
    expired_sessions = session_service.cleanup_expired_sessions()
    expired_feedback = session_service.expire_old_feedback_requests()
    
    return {
        "expired_sessions": expired_sessions,
        "expired_feedback_requests": expired_feedback,
        "message": "Cleanup completed"
    }

