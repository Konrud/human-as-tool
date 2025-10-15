"""Gmail OAuth2 and webhook endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse, JSONResponse
from datetime import datetime, timezone, timedelta
from typing import Optional
import secrets

from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2.credentials import Credentials

from ...api.dependencies import get_current_user
from ...models.user import User
from ...models.base import ChannelConnection, ChannelType
from ...storage.memory_store import store
from ...config import settings


router = APIRouter(prefix="/api/channels/gmail", tags=["gmail"])


# OAuth state storage (in production, use Redis or database)
oauth_states: dict[str, str] = {}  # state -> user_id


@router.get("/auth")
async def gmail_auth(current_user: User = Depends(get_current_user)):
    """
    Initiate Gmail OAuth2 flow.
    
    Returns redirect URL to Google OAuth consent screen.
    """
    if not settings.gmail_client_id or not settings.gmail_client_secret:
        raise HTTPException(
            status_code=500,
            detail="Gmail integration not configured"
        )
    
    # Create OAuth flow
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": settings.gmail_client_id,
                "client_secret": settings.gmail_client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [settings.gmail_redirect_uri or "http://localhost:8000/api/channels/gmail/callback"]
            }
        },
        scopes=[
            'https://www.googleapis.com/auth/gmail.send',
            'https://www.googleapis.com/auth/gmail.readonly',
            'https://www.googleapis.com/auth/gmail.modify',
            'https://www.googleapis.com/auth/userinfo.email'
        ]
    )
    
    flow.redirect_uri = settings.gmail_redirect_uri or "http://localhost:8000/api/channels/gmail/callback"
    
    # Generate state token for CSRF protection
    state = secrets.token_urlsafe(32)
    oauth_states[state] = current_user.id
    
    # Get authorization URL
    authorization_url, _ = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        state=state,
        prompt='consent'  # Force consent to get refresh token
    )
    
    return {"authorization_url": authorization_url}


@router.get("/callback")
async def gmail_callback(code: str, state: str):
    """
    Handle Gmail OAuth2 callback.
    
    Exchanges authorization code for access/refresh tokens.
    """
    # Verify state
    if state not in oauth_states:
        raise HTTPException(status_code=400, detail="Invalid state parameter")
    
    user_id = oauth_states.pop(state)
    user = store.get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        # Create OAuth flow
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": settings.gmail_client_id,
                    "client_secret": settings.gmail_client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [settings.gmail_redirect_uri or "http://localhost:8000/api/channels/gmail/callback"]
                }
            },
            scopes=[
                'https://www.googleapis.com/auth/gmail.send',
                'https://www.googleapis.com/auth/gmail.readonly',
                'https://www.googleapis.com/auth/gmail.modify',
                'https://www.googleapis.com/auth/userinfo.email'
            ]
        )
        
        flow.redirect_uri = settings.gmail_redirect_uri or "http://localhost:8000/api/channels/gmail/callback"
        
        # Exchange code for tokens
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        # Get user's email address
        from googleapiclient.discovery import build
        gmail_service = build('gmail', 'v1', credentials=credentials)
        profile = gmail_service.users().getProfile(userId='me').execute()
        user_email = profile.get('emailAddress')
        
        # Store connection
        connection = ChannelConnection(
            user_id=user_id,
            channel_type=ChannelType.EMAIL,
            access_token=credentials.token,
            refresh_token=credentials.refresh_token,
            token_expires_at=credentials.expiry if credentials.expiry else datetime.now(timezone.utc) + timedelta(hours=1),
            scope=' '.join(credentials.scopes) if credentials.scopes else None,
            extra_data={'email': user_email} if user_email else None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            is_active=True
        )
        
        store.create_channel_connection(connection)
        
        # Return success page or redirect to frontend
        return RedirectResponse(
            url=f"http://localhost:5173/dashboard?gmail_connected=true",
            status_code=302
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to complete OAuth flow: {str(e)}"
        )


@router.get("/status")
async def gmail_status(current_user: User = Depends(get_current_user)):
    """
    Check Gmail connection status for current user.
    
    Returns connection status and user email if connected.
    """
    connection = store.get_channel_connection(current_user.id, ChannelType.EMAIL)
    
    if not connection or not connection.is_active:
        return {
            "connected": False,
            "channel_type": "email",
            "user_email": None
        }
    
    # Check if token is expired
    is_expired = False
    if connection.token_expires_at:
        is_expired = connection.token_expires_at < datetime.now(timezone.utc)
    
    return {
        "connected": True,
        "channel_type": "email",
        "user_email": connection.extra_data.get('email') if connection.extra_data else None,
        "token_expired": is_expired,
        "connected_at": connection.created_at.isoformat()
    }


@router.delete("/disconnect")
async def gmail_disconnect(current_user: User = Depends(get_current_user)):
    """
    Disconnect Gmail for current user.
    
    Removes stored OAuth tokens.
    """
    deleted = store.delete_channel_connection(current_user.id, ChannelType.EMAIL)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Gmail not connected")
    
    return {"message": "Gmail disconnected successfully"}


@router.post("/webhook")
async def gmail_webhook(request: Request):
    """
    Handle Gmail push notifications (optional).
    
    Receives notifications about new emails for real-time response processing.
    """
    # This is optional - for receiving email replies in real-time
    # Requires setting up Gmail Pub/Sub push notifications
    
    try:
        body = await request.json()
        
        # Extract notification data
        # message = body.get('message', {})
        # data = message.get('data', '')
        
        # Decode and process notification
        # This would trigger email reply processing
        
        return {"status": "received"}
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

