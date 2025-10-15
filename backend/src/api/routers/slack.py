"""Slack OAuth2 and webhook endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse, JSONResponse
from datetime import datetime, timezone
from typing import Optional
import secrets
import hmac
import hashlib
import json

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from slack_sdk.oauth import AuthorizeUrlGenerator
from slack_sdk.oauth.state_store import FileOAuthStateStore

from ...api.dependencies import get_current_user
from ...models.user import User
from ...models.base import ChannelConnection, ChannelType
from ...storage.memory_store import store
from ...config import settings
from ...services.channels.slack_event_handler import slack_event_handler


router = APIRouter(prefix="/api/channels/slack", tags=["slack"])


# OAuth state storage (in production, use Redis or database)
oauth_states: dict[str, str] = {}  # state -> user_id


@router.get("/auth")
async def slack_auth(current_user: User = Depends(get_current_user)):
    """
    Initiate Slack OAuth2 flow.
    
    Returns redirect URL to Slack OAuth consent screen.
    """
    if not settings.slack_client_id or not settings.slack_client_secret:
        raise HTTPException(
            status_code=500,
            detail="Slack integration not configured"
        )
    
    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)
    oauth_states[state] = current_user.id
    
    # Create authorization URL
    authorize_url_generator = AuthorizeUrlGenerator(
        client_id=settings.slack_client_id,
        scopes=[
            "chat:write",
            "users:read",
            "users:read.email",
            "im:write",
            "im:history"
        ],
        user_scopes=[]
    )
    
    authorization_url = authorize_url_generator.generate(
        state=state,
        redirect_uri=settings.slack_redirect_uri or "http://localhost:8000/api/channels/slack/callback"
    )
    
    return {"authorization_url": authorization_url}


@router.get("/callback")
async def slack_callback(code: str, state: str):
    """
    Handle Slack OAuth2 callback.
    
    Exchanges authorization code for access token.
    """
    # Verify state
    if state not in oauth_states:
        raise HTTPException(status_code=400, detail="Invalid state parameter")
    
    user_id = oauth_states.pop(state)
    user = store.get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        # Exchange code for token
        client = WebClient()
        response = client.oauth_v2_access(
            client_id=settings.slack_client_id,
            client_secret=settings.slack_client_secret,
            code=code,
            redirect_uri=settings.slack_redirect_uri or "http://localhost:8000/api/channels/slack/callback"
        )
        
        if not response['ok']:
            raise HTTPException(
                status_code=400,
                detail=f"Slack OAuth failed: {response.get('error', 'unknown')}"
            )
        
        # Extract token and bot info
        access_token = response['access_token']
        bot_user_id = response.get('bot_user_id')
        team_id = response.get('team', {}).get('id')
        
        # Get authed user info
        authed_user = response.get('authed_user', {})
        slack_user_id = authed_user.get('id')
        
        # Store connection
        connection = ChannelConnection(
            user_id=user_id,
            channel_type=ChannelType.SLACK,
            access_token=access_token,
            refresh_token=None,  # Slack doesn't use refresh tokens in this flow
            token_expires_at=None,  # Slack tokens don't expire
            scope=response.get('scope'),
            extra_data={
                'bot_user_id': bot_user_id,
                'team_id': team_id,
                'slack_user_id': slack_user_id
            },
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            is_active=True
        )
        
        store.create_channel_connection(connection)
        
        # Return success page or redirect to frontend
        return RedirectResponse(
            url=f"http://localhost:5173/dashboard?slack_connected=true",
            status_code=302
        )
        
    except SlackApiError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to complete OAuth flow: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to complete OAuth flow: {str(e)}"
        )


@router.get("/status")
async def slack_status(current_user: User = Depends(get_current_user)):
    """
    Check Slack connection status for current user.
    
    Returns connection status and workspace info if connected.
    """
    connection = store.get_channel_connection(current_user.id, ChannelType.SLACK)
    
    if not connection or not connection.is_active:
        return {
            "connected": False,
            "channel_type": "slack",
            "team_id": None,
            "slack_user_id": None
        }
    
    return {
        "connected": True,
        "channel_type": "slack",
        "team_id": connection.extra_data.get('team_id') if connection.extra_data else None,
        "slack_user_id": connection.extra_data.get('slack_user_id') if connection.extra_data else None,
        "connected_at": connection.created_at.isoformat()
    }


@router.delete("/disconnect")
async def slack_disconnect(current_user: User = Depends(get_current_user)):
    """
    Disconnect Slack for current user.
    
    Removes stored OAuth tokens.
    """
    deleted = store.delete_channel_connection(current_user.id, ChannelType.SLACK)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Slack not connected")
    
    return {"message": "Slack disconnected successfully"}


def verify_slack_signature(request_body: bytes, timestamp: str, signature: str) -> bool:
    """
    Verify Slack request signature.
    
    Args:
        request_body: Raw request body bytes
        timestamp: X-Slack-Request-Timestamp header
        signature: X-Slack-Signature header
        
    Returns:
        True if signature is valid
    """
    if not settings.slack_signing_secret:
        return False
    
    # Create signature basestring
    sig_basestring = f"v0:{timestamp}:".encode() + request_body
    
    # Calculate signature
    my_signature = 'v0=' + hmac.new(
        settings.slack_signing_secret.encode(),
        sig_basestring,
        hashlib.sha256
    ).hexdigest()
    
    # Compare signatures
    return hmac.compare_digest(my_signature, signature)


@router.post("/events")
async def slack_events(request: Request):
    """
    Handle Slack events webhook.
    
    Receives events like messages, reactions, etc.
    """
    # Get headers
    timestamp = request.headers.get('X-Slack-Request-Timestamp', '')
    signature = request.headers.get('X-Slack-Signature', '')
    
    # Read body
    body = await request.body()
    
    # Verify signature
    if not verify_slack_signature(body, timestamp, signature):
        raise HTTPException(status_code=403, detail="Invalid signature")
    
    try:
        payload = json.loads(body)
        
        # Handle URL verification challenge
        if payload.get('type') == 'url_verification':
            return {"challenge": payload.get('challenge')}
        
        # Handle event callback
        if payload.get('type') == 'event_callback':
            event = payload.get('event', {})
            await slack_event_handler.handle_event(event)
            return {"status": "ok"}
        
        return {"status": "ok"}
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@router.post("/interactions")
async def slack_interactions(request: Request):
    """
    Handle Slack interactive components.
    
    Receives button clicks, menu selections, modal submissions, etc.
    """
    # Get headers
    timestamp = request.headers.get('X-Slack-Request-Timestamp', '')
    signature = request.headers.get('X-Slack-Signature', '')
    
    # Read body
    body = await request.body()
    
    # Verify signature
    if not verify_slack_signature(body, timestamp, signature):
        raise HTTPException(status_code=403, detail="Invalid signature")
    
    try:
        # Parse form data (Slack sends interactions as form-encoded)
        body_str = body.decode('utf-8')
        if body_str.startswith('payload='):
            payload_str = body_str[8:]  # Remove 'payload=' prefix
            # URL decode
            import urllib.parse
            payload_str = urllib.parse.unquote(payload_str)
            payload = json.loads(payload_str)
        else:
            payload = json.loads(body_str)
        
        # Handle interaction
        response = await slack_event_handler.handle_interaction(payload)
        
        return response
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

