"""Main worker entry point.

Run all background workers or specific ones.
"""

import asyncio
import argparse
import logging
import sys

from workers.router import RouterWorker
from workers.webhook import WebhookWorker
from workers.ai import AIWorker
from workers.analytics import AnalyticsWorker
from workers.notification import NotificationWorker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

WORKERS = {
    "router": RouterWorker,
    "webhook": WebhookWorker,
    "ai": AIWorker,
    "analytics": AnalyticsWorker,
    "notification": NotificationWorker,
}


async def run_workers(worker_names: list[str]):
    """Run specified workers concurrently."""
    workers = []

    for name in worker_names:
        worker_class = WORKERS.get(name)
        if worker_class:
            workers.append(worker_class())
        else:
            logger.warning(f"Unknown worker: {name}")

    if not workers:
        logger.error("No valid workers specified")
        return

    logger.info(f"Starting workers: {[w.name for w in workers]}")

    # Run all workers concurrently
    tasks = [asyncio.create_task(worker.run()) for worker in workers]
    await asyncio.gather(*tasks, return_exceptions=True)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="OmniSupport Background Workers")
    parser.add_argument(
        "workers",
        nargs="*",
        default=["all"],
        help="Workers to run (router, webhook, ai, analytics, notification, or all)",
    )
    args = parser.parse_args()

    worker_names = args.workers
    if "all" in worker_names:
        worker_names = list(WORKERS.keys())

    try:
        asyncio.run(run_workers(worker_names))
    except KeyboardInterrupt:
        logger.info("Workers stopped by user")
        sys.exit(0)


if __name__ == "__main__":
    main()
