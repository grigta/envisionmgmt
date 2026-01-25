"""Base worker class for background task processing."""

import asyncio
import signal
import logging
from abc import ABC, abstractmethod
from typing import Any

import redis.asyncio as redis

from shared.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class BaseWorker(ABC):
    """Base class for background workers."""

    name: str = "base_worker"

    def __init__(self):
        self.redis: redis.Redis | None = None
        self._shutdown = False
        self._tasks: list[asyncio.Task] = []

    async def setup(self):
        """Initialize worker resources."""
        self.redis = redis.from_url(settings.redis_url)
        logger.info(f"Worker {self.name} initialized")

    async def cleanup(self):
        """Cleanup worker resources."""
        if self.redis:
            await self.redis.close()
        logger.info(f"Worker {self.name} cleaned up")

    @abstractmethod
    async def process(self):
        """Main processing loop. Override in subclasses."""
        pass

    async def run(self):
        """Run the worker."""
        # Setup signal handlers
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, self._signal_handler)

        try:
            await self.setup()
            logger.info(f"Worker {self.name} starting")
            await self.process()
        except asyncio.CancelledError:
            logger.info(f"Worker {self.name} cancelled")
        except Exception as e:
            logger.error(f"Worker {self.name} error: {e}", exc_info=True)
        finally:
            await self.cleanup()

    def _signal_handler(self):
        """Handle shutdown signals."""
        logger.info(f"Worker {self.name} received shutdown signal")
        self._shutdown = True
        for task in self._tasks:
            task.cancel()

    async def subscribe_to_channel(self, channel: str, handler: callable):
        """Subscribe to Redis pub/sub channel."""
        if not self.redis:
            raise RuntimeError("Redis not initialized")

        pubsub = self.redis.pubsub()
        await pubsub.subscribe(channel)
        logger.info(f"Subscribed to channel: {channel}")

        async for message in pubsub.listen():
            if self._shutdown:
                break
            if message["type"] == "message":
                try:
                    await handler(message["data"])
                except Exception as e:
                    logger.error(f"Error handling message: {e}", exc_info=True)

        await pubsub.unsubscribe(channel)

    async def pop_from_queue(
        self, queue_name: str, timeout: int = 5
    ) -> dict[str, Any] | None:
        """Pop item from Redis list queue (blocking)."""
        if not self.redis:
            raise RuntimeError("Redis not initialized")

        result = await self.redis.blpop(queue_name, timeout=timeout)
        if result:
            import json

            _, data = result
            return json.loads(data)
        return None

    async def push_to_queue(self, queue_name: str, data: dict[str, Any]):
        """Push item to Redis list queue."""
        if not self.redis:
            raise RuntimeError("Redis not initialized")

        import json

        await self.redis.rpush(queue_name, json.dumps(data))
