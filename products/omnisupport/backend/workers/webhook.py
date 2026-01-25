"""Webhook delivery worker.

Handles sending webhooks to external services with retry logic.
"""

import asyncio
import json
import logging
import hmac
import hashlib
from datetime import datetime, timezone
from uuid import UUID

import httpx
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_session
from shared.models.integration import Webhook, WebhookDelivery

from workers.base import BaseWorker

logger = logging.getLogger(__name__)

QUEUE_NAME = "queue:webhooks"
MAX_RETRIES = 5
RETRY_DELAYS = [60, 300, 900, 3600, 7200]  # 1m, 5m, 15m, 1h, 2h


class WebhookWorker(BaseWorker):
    """Worker for delivering webhooks."""

    name = "webhook_worker"

    async def process(self):
        """Main processing loop - pop from queue and deliver."""
        while not self._shutdown:
            try:
                item = await self.pop_from_queue(QUEUE_NAME, timeout=5)
                if item:
                    await self.deliver_webhook(item)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in webhook worker: {e}", exc_info=True)
                await asyncio.sleep(1)

    async def deliver_webhook(self, item: dict):
        """Deliver a single webhook."""
        webhook_id = item.get("webhook_id")
        event_type = item.get("event_type")
        payload = item.get("payload")
        attempt = item.get("attempt", 1)

        async with get_session() as session:
            # Get webhook config
            result = await session.execute(
                select(Webhook).where(
                    and_(
                        Webhook.id == UUID(webhook_id),
                        Webhook.is_active == True,
                    )
                )
            )
            webhook = result.scalar_one_or_none()

            if not webhook:
                logger.warning(f"Webhook {webhook_id} not found or inactive")
                return

            # Check if event type is subscribed
            if webhook.events and event_type not in webhook.events:
                return

            # Prepare request
            body = json.dumps({
                "event": event_type,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data": payload,
            })

            headers = {
                "Content-Type": "application/json",
                "User-Agent": "OmniSupport-Webhook/1.0",
                "X-Webhook-Event": event_type,
            }

            # Add signature if secret is configured
            if webhook.secret:
                signature = hmac.new(
                    webhook.secret.encode(),
                    body.encode(),
                    hashlib.sha256,
                ).hexdigest()
                headers["X-Webhook-Signature"] = f"sha256={signature}"

            # Send request
            delivery = WebhookDelivery(
                webhook_id=webhook.id,
                event_type=event_type,
                request_headers=headers,
                request_body=payload,
                attempt=attempt,
            )

            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        webhook.url,
                        content=body,
                        headers=headers,
                    )

                    delivery.response_status = response.status_code
                    delivery.response_body = response.text[:10000]  # Limit size
                    delivery.success = 200 <= response.status_code < 300

                    if delivery.success:
                        logger.info(
                            f"Webhook {webhook_id} delivered successfully "
                            f"(status={response.status_code})"
                        )
                    else:
                        logger.warning(
                            f"Webhook {webhook_id} failed with status {response.status_code}"
                        )

            except Exception as e:
                delivery.success = False
                delivery.error_message = str(e)[:1000]
                logger.error(f"Webhook {webhook_id} delivery error: {e}")

            session.add(delivery)
            await session.commit()

            # Schedule retry if failed
            if not delivery.success and attempt < MAX_RETRIES:
                delay = RETRY_DELAYS[attempt - 1]
                await self.schedule_retry(item, attempt + 1, delay)

    async def schedule_retry(self, item: dict, attempt: int, delay: int):
        """Schedule webhook retry after delay."""
        item["attempt"] = attempt

        # Use Redis sorted set for delayed execution
        if self.redis:
            execute_at = datetime.now(timezone.utc).timestamp() + delay
            await self.redis.zadd(
                "delayed:webhooks",
                {json.dumps(item): execute_at},
            )
            logger.info(f"Scheduled webhook retry in {delay}s (attempt {attempt})")


async def main():
    """Run webhook worker."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    worker = WebhookWorker()
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
