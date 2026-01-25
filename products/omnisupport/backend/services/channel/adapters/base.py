"""Base channel adapter."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass
class UnifiedMessage:
    """Unified message model across all channels."""

    channel: str  # telegram, whatsapp, web
    channel_message_id: str
    channel_user_id: str
    channel_username: str | None = None
    channel_name: str | None = None
    channel_avatar_url: str | None = None

    content_type: str = "text"  # text, image, file, audio, video, location
    content: dict = None

    # Optional customer info from channel profile
    phone: str | None = None
    email: str | None = None

    timestamp: datetime | None = None
    metadata: dict = None

    def __post_init__(self):
        if self.content is None:
            self.content = {}
        if self.metadata is None:
            self.metadata = {}


class BaseChannelAdapter(ABC):
    """Base class for channel adapters."""

    channel_type: str

    @abstractmethod
    async def send_message(
        self,
        channel_user_id: str,
        content_type: str,
        content: dict,
        **kwargs,
    ) -> str | None:
        """
        Send message to user.
        Returns channel_message_id on success, None on failure.
        """
        pass

    @abstractmethod
    async def parse_webhook(self, payload: dict) -> UnifiedMessage | None:
        """
        Parse incoming webhook payload into UnifiedMessage.
        Returns None if message should be ignored.
        """
        pass

    @abstractmethod
    async def validate_credentials(self, credentials: dict) -> bool:
        """Validate channel credentials."""
        pass

    async def setup_webhook(self, webhook_url: str, credentials: dict) -> bool:
        """Set up webhook for this channel. Override if needed."""
        return True

    async def remove_webhook(self, credentials: dict) -> bool:
        """Remove webhook for this channel. Override if needed."""
        return True
