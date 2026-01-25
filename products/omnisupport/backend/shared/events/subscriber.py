"""Redis event subscriber."""

import asyncio
from collections.abc import AsyncGenerator, Callable, Awaitable
from typing import Any

import redis.asyncio as redis

from shared.config import get_settings
from shared.events.types import Event

settings = get_settings()


class EventSubscriber:
    """Subscribes to Redis pub/sub channels."""

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.pubsub = redis_client.pubsub()
        self._handlers: dict[str, list[Callable[[Event], Awaitable[None]]]] = {}
        self._running = False

    async def subscribe(self, *patterns: str) -> None:
        """Subscribe to channel patterns."""
        await self.pubsub.psubscribe(*patterns)

    async def unsubscribe(self, *patterns: str) -> None:
        """Unsubscribe from channel patterns."""
        await self.pubsub.punsubscribe(*patterns)

    def add_handler(
        self,
        pattern: str,
        handler: Callable[[Event], Awaitable[None]],
    ) -> None:
        """Add a handler for events matching a pattern."""
        if pattern not in self._handlers:
            self._handlers[pattern] = []
        self._handlers[pattern].append(handler)

    async def listen(self) -> AsyncGenerator[Event, None]:
        """Listen for events and yield them."""
        async for message in self.pubsub.listen():
            if message["type"] == "pmessage":
                try:
                    event = Event.model_validate_json(message["data"])
                    yield event
                except Exception:
                    # Skip invalid messages
                    continue

    async def run(self) -> None:
        """Run the subscriber event loop."""
        self._running = True
        try:
            async for event in self.listen():
                if not self._running:
                    break
                await self._dispatch_event(event)
        finally:
            self._running = False

    async def stop(self) -> None:
        """Stop the subscriber."""
        self._running = False
        await self.pubsub.close()

    async def _dispatch_event(self, event: Event) -> None:
        """Dispatch event to registered handlers."""
        channel = f"omnisupport:{event.tenant_id}:{event.type.value}"

        for pattern, handlers in self._handlers.items():
            if self._matches_pattern(channel, pattern):
                for handler in handlers:
                    try:
                        await handler(event)
                    except Exception as e:
                        # Log error but continue processing
                        print(f"Error in event handler: {e}")

    @staticmethod
    def _matches_pattern(channel: str, pattern: str) -> bool:
        """Check if channel matches pattern (simple glob matching)."""
        import fnmatch

        return fnmatch.fnmatch(channel, pattern)


async def create_subscriber() -> EventSubscriber:
    """Create a new event subscriber."""
    redis_client = redis.from_url(str(settings.redis_url))
    return EventSubscriber(redis_client)
