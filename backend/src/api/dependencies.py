from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from ..services.auth_service import auth_service
from ..storage.memory_store import store
from ..models.user import User


# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    Dependency to get the current authenticated user from JWT token.
    
    Args:
        token: JWT token from Authorization header
        
    Returns:
        User object if authentication successful
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Decode token
    token_data = auth_service.decode_token(token)
    if token_data is None or token_data.user_id is None:
        raise credentials_exception
    
    # Get user from storage
    user = store.get_user_by_id(token_data.user_id)
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to get the current authenticated and active user.
    
    Args:
        current_user: User from get_current_user dependency
        
    Returns:
        User object if user is active
        
    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Inactive user"
        )
    return current_user

