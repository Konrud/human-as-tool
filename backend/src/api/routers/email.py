"""
Email authentication router.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from src.api.dependencies import get_current_active_user
from src.models.user import User
from src.services.email_service import email_service
from src.storage.memory_store import store

router = APIRouter(prefix="/api/auth/gmail", tags=["auth"])


class GmailAuthResponse(BaseModel):
    """Response model for Gmail authentication."""
    auth_url: str


@router.get("/authorize", response_model=GmailAuthResponse)
async def authorize_gmail(current_user: User = Depends(get_current_active_user)):
    """Get Gmail authorization URL."""
    auth_url = await email_service.get_auth_url()
    return GmailAuthResponse(auth_url=auth_url)


@router.get("/callback")
async def gmail_callback(
    code: str,
    state: str = None,
    error: str = None,
    current_user: User = Depends(get_current_active_user)
):
    """Handle Gmail OAuth callback."""
    if error:
        raise HTTPException(status_code=400, detail=error)
        
    try:
        # Exchange code for tokens
        token_info = await email_service.exchange_code(code)
        
        # Store tokens for user
        store.set_user_data(
            current_user.id,
            "gmail_tokens",
            {
                "access_token": token_info["access_token"],
                "refresh_token": token_info.get("refresh_token"),
                "expires_at": token_info["expires_in"]
            }
        )
        
        return {"message": "Gmail authentication successful"}
        
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to authenticate with Gmail: {str(e)}"
        )