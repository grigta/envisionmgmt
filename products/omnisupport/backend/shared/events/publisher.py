"""Redis event publisher."""

import json
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import redis.asyncio as redis

from shared.config import get_settings
from shared.events.types import Event, EventType

settings = get_settings()


class EventPublisher:
    """Publishes events to Redis pub/sub channels."""

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    async def publish(self, event: Event) -> int:
        """
        Publish an event to Redis.
        Returns number of subscribers that received the message.
        """
        channel = self._get_channel(event)
        message = event.model_dump_json()
        return await self.redis.publish(channel, message)

    async def publish_raw(
        self,
        event_type: EventType,
        tenant_id: UUID,
        data: dict[str, Any],
        conversation_id: UUID | None = None,
        customer_id: UUID | None = None,
        user_id: UUID | None = None,
    ) -> int:
        """Publish an event with raw data."""
        event = Event(
            type=event_type,
            tenant_id=tenant_id,
            timestamp=datetime.now(timezone.utc),
            data=data,
            conversation_id=conversation_id,
            customer_id=customer_id,
            user_id=user_id,
        )
        return await self.publish(event)

    def _get_channel(self, event: Event) -> str:
        """Get Redis channel name for event."""
        # Channel format: omnisupport:{tenant_id}:{event_type}
        return f"omnisupport:{event.tenant_id}:{event.type.value}"

    @staticmethod
    def get_tenant_pattern(tenant_id: UUID) -> str:
        """Get pattern for all events of a tenant."""
        return f"omnisupport:{tenant_id}:*"

    @staticmethod
    def get_conversation_channel(tenant_id: UUID, conversation_id: UUID) -> str:
        """Get channel for conversation-specific events."""
        return f"omnisupport:{tenant_id}:conversation:{conversation_id}"


# Global publisher instance
_publisher: EventPublisher | None = None


async def get_publisher() -> EventPublisher:
    """Get or create the global event publisher."""
    global _publisher
    if _publisher is None:
        redis_client = redis.from_url(str(settings.redis_url))
        _publisher = EventPublisher(redis_client)
    return _publisher


async def close_publisher() -> None:
    """Close the global event publisher."""
    global _publisher
    if _publisher is not None:
        await _publisher.redis.close()
        _publisher = None
