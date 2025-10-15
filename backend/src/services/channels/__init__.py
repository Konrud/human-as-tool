"""Channel handlers for multi-channel communication."""

from .base_channel import BaseChannel, ChannelError, ChannelConnectionError, ChannelRateLimitError
from .gmail_channel import GmailChannel
from .slack_channel import SlackChannel

__all__ = [
    "BaseChannel",
    "ChannelError",
    "ChannelConnectionError",
    "ChannelRateLimitError",
    "GmailChannel",
    "SlackChannel",
]

