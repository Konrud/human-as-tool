from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application configuration settings loaded from environment variables."""
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    environment: str = "development"
    debug: bool = True
    
    # Security & JWT
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 25
    refresh_token_expire_days: int = 7
    
    # Rate Limiting
    rate_limit_per_user: int = 30
    rate_limit_window_seconds: int = 60
    rate_limit_per_session: int = 10
    rate_limit_per_channel: int = 20
    
    # Session Configuration
    max_concurrent_sessions: int = 3
    session_timeout_hours: int = 24
    feedback_timeout_hours: int = 48
    
    # Gmail Integration (Optional)
    gmail_client_id: Optional[str] = None
    gmail_client_secret: Optional[str] = None
    gmail_redirect_uri: Optional[str] = None
    
    # Slack Integration (Optional)
    slack_client_id: Optional[str] = None
    slack_client_secret: Optional[str] = None
    slack_signing_secret: Optional[str] = None
    slack_redirect_uri: Optional[str] = None
    
    # BAML Configuration (Optional)
    openai_api_key: Optional[str] = None
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


# Global settings instance
settings = Settings()

