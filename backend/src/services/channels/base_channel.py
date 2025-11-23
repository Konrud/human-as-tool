"""Base abstract class for all communication channels."""

from abc import ABC, abstractmethod
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from enum import Enum
import asyncio

from ...models.base import (
    Message,
    FeedbackRequest,
    ChannelType,
    ChannelStatus,
    MessageStatus,
)


class ChannelError(Exception):
    """Base exception for channel errors."""
    pass


class ChannelConnectionError(ChannelError):
    """Channel connection failed."""
    pass


class ChannelRateLimitError(ChannelError):
    """Channel rate limit exceeded."""
    def __init__(self, message: str, retry_after: Optional[int] = None):
        super().__init__(message)
        self.retry_after = retry_after


class CircuitState(str, Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Failures exceeded, blocking requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """
    Circuit breaker pattern implementation for channel health management.
    
    Prevents repeated calls to failing channels by tracking errors and 
    temporarily blocking requests when failure threshold is exceeded.
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        timeout_seconds: int = 60,
        half_open_max_calls: int = 3
    ):
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.half_open_max_calls = half_open_max_calls
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.half_open_calls = 0
    
    def can_execute(self) -> bool:
        """Check if request can be executed based on circuit state."""
        if self.state == CircuitState.CLOSED:
            return True
        
        if self.state == CircuitState.OPEN:
            # Check if timeout has elapsed
            if self.last_failure_time:
                elapsed = (datetime.now(timezone.utc) - self.last_failure_time).total_seconds()
                if elapsed >= self.timeout_seconds:
                    # Move to half-open state
                    self.state = CircuitState.HALF_OPEN
                    self.half_open_calls = 0
                    return True
            return False
        
        if self.state == CircuitState.HALF_OPEN:
            # Allow limited calls in half-open state
            return self.half_open_calls < self.half_open_max_calls
        
        return False
    
    def record_success(self):
        """Record successful execution."""
        if self.state == CircuitState.HALF_OPEN:
            # Service recovered, close the circuit
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.half_open_calls = 0
        elif self.state == CircuitState.CLOSED:
            # Reset failure count on success
            self.failure_count = 0
    
    def record_failure(self):
        """Record failed execution."""
        self.failure_count += 1
        self.last_failure_time = datetime.now(timezone.utc)
        
        if self.state == CircuitState.HALF_OPEN:
            # Failed in half-open, reopen circuit
            self.state = CircuitState.OPEN
            self.half_open_calls = 0
        elif self.state == CircuitState.CLOSED:
            if self.failure_count >= self.failure_threshold:
                # Threshold exceeded, open circuit
                self.state = CircuitState.OPEN
        
        if self.state == CircuitState.HALF_OPEN:
            self.half_open_calls += 1
    
    def get_status(self) -> Dict[str, Any]:
        """Get current circuit breaker status."""
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "can_execute": self.can_execute()
        }


class BaseChannel(ABC):
    """
    Abstract base class for all communication channels.
    
    Provides common interface and utilities for channel implementations
    including error handling, retry logic, and health monitoring.
    """
    
    def __init__(self, channel_type: ChannelType, config: Optional[Dict[str, Any]] = None):
        """
        Initialize base channel.
        
        Args:
            channel_type: Type of channel
            config: Channel-specific configuration
        """
        self.channel_type = channel_type
        self.config = config or {}
        self.status = ChannelStatus.INACTIVE
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=self.config.get("failure_threshold", 5),
            timeout_seconds=self.config.get("circuit_timeout", 60),
            half_open_max_calls=self.config.get("half_open_calls", 3)
        )
        self.last_health_check: Optional[datetime] = None
        self.error_count = 0
        self.success_count = 0
    
    @abstractmethod
    async def send_message(
        self,
        message: Message,
        recipient: str,
        **kwargs
    ) -> bool:
        """
        Send a message through this channel.
        
        Args:
            message: Message to send
            recipient: Recipient identifier (email, slack user ID, etc.)
            **kwargs: Channel-specific parameters
            
        Returns:
            True if message sent successfully
            
        Raises:
            ChannelError: On send failure
            ChannelRateLimitError: On rate limit
        """
        pass
    
    @abstractmethod
    async def request_feedback(
        self,
        feedback_request: FeedbackRequest,
        recipient: str,
        **kwargs
    ) -> bool:
        """
        Send a feedback request through this channel.
        
        Args:
            feedback_request: Feedback request to send
            recipient: Recipient identifier
            **kwargs: Channel-specific parameters
            
        Returns:
            True if request sent successfully
            
        Raises:
            ChannelError: On send failure
        """
        pass
    
    @abstractmethod
    async def check_health(self) -> bool:
        """
        Check channel health and connectivity.
        
        Returns:
            True if channel is healthy
        """
        pass
    
    @abstractmethod
    async def initialize(self, user_id: str) -> bool:
        """
        Initialize channel connection for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            True if initialization successful
        """
        pass
    
    async def execute_with_retry(
        self,
        operation,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        **kwargs
    ) -> Any:
        """
        Execute an operation with exponential backoff retry.
        
        Args:
            operation: Async callable to execute
            max_retries: Maximum retry attempts
            base_delay: Initial delay in seconds
            max_delay: Maximum delay in seconds
            **kwargs: Arguments to pass to operation
            
        Returns:
            Result of operation
            
        Raises:
            ChannelError: After all retries exhausted
        """
        last_error = None
        
        for attempt in range(max_retries + 1):
            # Check circuit breaker
            if not self.circuit_breaker.can_execute():
                raise ChannelError(
                    f"Circuit breaker is {self.circuit_breaker.state.value}, blocking request"
                )
            
            try:
                result = await operation(**kwargs)
                
                # Success
                self.circuit_breaker.record_success()
                self.success_count += 1
                self.status = ChannelStatus.ACTIVE
                return result
                
            except ChannelRateLimitError as e:
                # Don't retry on rate limits, propagate immediately
                self.circuit_breaker.record_failure()
                self.error_count += 1
                raise
                
            except Exception as e:
                last_error = e
                self.circuit_breaker.record_failure()
                self.error_count += 1
                
                if attempt < max_retries:
                    # Calculate exponential backoff delay
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    await asyncio.sleep(delay)
                else:
                    # Final attempt failed
                    self.status = ChannelStatus.ERROR
        
        # All retries exhausted
        raise ChannelError(
            f"Operation failed after {max_retries + 1} attempts: {str(last_error)}"
        )
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Get comprehensive channel health status.
        
        Returns:
            Dictionary with health metrics
        """
        return {
            "channel_type": self.channel_type.value,
            "status": self.status.value,
            "error_count": self.error_count,
            "success_count": self.success_count,
            "last_health_check": self.last_health_check.isoformat() if self.last_health_check else None,
            "circuit_breaker": self.circuit_breaker.get_status(),
            "success_rate": (
                self.success_count / (self.success_count + self.error_count)
                if (self.success_count + self.error_count) > 0
                else 0.0
            )
        }
    
    def update_status(self, status: ChannelStatus):
        """Update channel status."""
        self.status = status
    
    def reset_error_count(self):
        """Reset error counter."""
        self.error_count = 0

