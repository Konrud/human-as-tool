"""
Rate limiter service implementing multi-level rate limiting with token bucket algorithm.
Supports per-user, per-session, and per-channel rate limits.
"""

from typing import Dict, Optional, Tuple
from datetime import datetime, timezone, timedelta
from ..storage.memory_store import store


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded."""
    
    def __init__(
        self,
        message: str,
        retry_after: int,
        limit: int,
        remaining: int,
        reset_at: float
    ):
        super().__init__(message)
        self.retry_after = retry_after
        self.limit = limit
        self.remaining = remaining
        self.reset_at = reset_at


class RateLimiter:
    """
    Multi-level rate limiter implementing token bucket algorithm.
    
    Levels:
    - Per user: 30 requests/minute (global across all channels)
    - Per session: 10 requests/minute
    - Per channel: 20 requests/minute
    """
    
    # Rate limit configurations
    USER_LIMIT = 30  # requests per minute
    SESSION_LIMIT = 10  # requests per minute
    CHANNEL_LIMIT = 20  # requests per minute
    WINDOW_SECONDS = 60  # 1 minute window
    
    def __init__(self):
        pass
    
    def _get_rate_limit_key(
        self,
        level: str,
        identifier: str
    ) -> str:
        """Generate rate limit key."""
        return f"rate_limit:{level}:{identifier}"
    
    def check_user_limit(self, user_id: str) -> Tuple[bool, Dict]:
        """
        Check user-level rate limit.
        
        Args:
            user_id: User identifier
            
        Returns:
            Tuple of (is_allowed, rate_limit_info)
            
        Raises:
            RateLimitExceeded: If rate limit is exceeded
        """
        key = self._get_rate_limit_key("user", user_id)
        allowed = store.check_rate_limit(
            key,
            self.USER_LIMIT,
            self.WINDOW_SECONDS
        )
        
        status = store.get_rate_limit_status(
            key,
            self.USER_LIMIT,
            self.WINDOW_SECONDS
        )
        
        if not allowed:
            retry_after = int(status["reset_at"] - datetime.now(timezone.utc).timestamp())
            raise RateLimitExceeded(
                message=f"User rate limit exceeded. Try again in {retry_after} seconds.",
                retry_after=retry_after,
                limit=status["limit"],
                remaining=status["remaining"],
                reset_at=status["reset_at"]
            )
        
        return True, status
    
    def check_session_limit(self, session_id: str) -> Tuple[bool, Dict]:
        """
        Check session-level rate limit.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Tuple of (is_allowed, rate_limit_info)
            
        Raises:
            RateLimitExceeded: If rate limit is exceeded
        """
        key = self._get_rate_limit_key("session", session_id)
        allowed = store.check_rate_limit(
            key,
            self.SESSION_LIMIT,
            self.WINDOW_SECONDS
        )
        
        status = store.get_rate_limit_status(
            key,
            self.SESSION_LIMIT,
            self.WINDOW_SECONDS
        )
        
        if not allowed:
            retry_after = int(status["reset_at"] - datetime.now(timezone.utc).timestamp())
            raise RateLimitExceeded(
                message=f"Session rate limit exceeded. Try again in {retry_after} seconds.",
                retry_after=retry_after,
                limit=status["limit"],
                remaining=status["remaining"],
                reset_at=status["reset_at"]
            )
        
        return True, status
    
    def check_channel_limit(self, channel: str, user_id: str) -> Tuple[bool, Dict]:
        """
        Check channel-level rate limit.
        
        Args:
            channel: Channel type (websocket, email, slack)
            user_id: User identifier
            
        Returns:
            Tuple of (is_allowed, rate_limit_info)
            
        Raises:
            RateLimitExceeded: If rate limit is exceeded
        """
        key = self._get_rate_limit_key("channel", f"{channel}:{user_id}")
        allowed = store.check_rate_limit(
            key,
            self.CHANNEL_LIMIT,
            self.WINDOW_SECONDS
        )
        
        status = store.get_rate_limit_status(
            key,
            self.CHANNEL_LIMIT,
            self.WINDOW_SECONDS
        )
        
        if not allowed:
            retry_after = int(status["reset_at"] - datetime.now(timezone.utc).timestamp())
            raise RateLimitExceeded(
                message=f"Channel rate limit exceeded. Try again in {retry_after} seconds.",
                retry_after=retry_after,
                limit=status["limit"],
                remaining=status["remaining"],
                reset_at=status["reset_at"]
            )
        
        return True, status
    
    def check_all_limits(
        self,
        user_id: str,
        session_id: str,
        channel: str
    ) -> Dict:
        """
        Check all rate limits for a request.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            channel: Channel type
            
        Returns:
            Combined rate limit status
            
        Raises:
            RateLimitExceeded: If any rate limit is exceeded
        """
        # Check in order: user -> session -> channel
        # Stop at first violation
        _, user_status = self.check_user_limit(user_id)
        _, session_status = self.check_session_limit(session_id)
        _, channel_status = self.check_channel_limit(channel, user_id)
        
        # Return the most restrictive status
        return {
            "user": user_status,
            "session": session_status,
            "channel": channel_status,
        }
    
    def get_rate_limit_headers(
        self,
        user_id: str,
        session_id: str,
        channel: str
    ) -> Dict[str, str]:
        """
        Get rate limit headers for HTTP responses.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            channel: Channel type
            
        Returns:
            Dictionary of rate limit headers
        """
        try:
            status = self.check_all_limits(user_id, session_id, channel)
            
            # Use the most restrictive limit
            user_remaining = status["user"]["remaining"]
            session_remaining = status["session"]["remaining"]
            channel_remaining = status["channel"]["remaining"]
            
            min_remaining = min(user_remaining, session_remaining, channel_remaining)
            
            # Use user limit as the primary limit shown
            return {
                "X-RateLimit-Limit": str(self.USER_LIMIT),
                "X-RateLimit-Remaining": str(min_remaining),
                "X-RateLimit-Reset": str(int(status["user"]["reset_at"])),
                "X-RateLimit-Window": str(self.WINDOW_SECONDS),
            }
        except RateLimitExceeded as e:
            return {
                "X-RateLimit-Limit": str(e.limit),
                "X-RateLimit-Remaining": str(e.remaining),
                "X-RateLimit-Reset": str(int(e.reset_at)),
                "X-RateLimit-Retry-After": str(e.retry_after),
            }
    
    def get_status(
        self,
        user_id: str,
        session_id: Optional[str] = None,
        channel: Optional[str] = None
    ) -> Dict:
        """
        Get current rate limit status without checking/decrementing.
        
        Args:
            user_id: User identifier
            session_id: Optional session identifier
            channel: Optional channel type
            
        Returns:
            Rate limit status information
        """
        result = {}
        
        # User status
        user_key = self._get_rate_limit_key("user", user_id)
        result["user"] = store.get_rate_limit_status(
            user_key,
            self.USER_LIMIT,
            self.WINDOW_SECONDS
        )
        
        # Session status
        if session_id:
            session_key = self._get_rate_limit_key("session", session_id)
            result["session"] = store.get_rate_limit_status(
                session_key,
                self.SESSION_LIMIT,
                self.WINDOW_SECONDS
            )
        
        # Channel status
        if channel:
            channel_key = self._get_rate_limit_key("channel", f"{channel}:{user_id}")
            result["channel"] = store.get_rate_limit_status(
                channel_key,
                self.CHANNEL_LIMIT,
                self.WINDOW_SECONDS
            )
        
        return result


# Global rate limiter instance
rate_limiter = RateLimiter()

