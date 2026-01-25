"""Analytics aggregation worker.

Handles periodic aggregation of analytics metrics:
- Conversation statistics
- Operator performance
- Channel metrics
- Response times
- CSAT scores
- AI metrics
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from uuid import UUID

from sqlalchemy import select, func, and_, case, extract
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_session
from shared.models.conversation import Conversation, Message, ConversationStatus
from shared.models.customer import Customer
from shared.models.user import User
from shared.models.analytics import AnalyticsSnapshot, SnapshotPeriod
from shared.models.tenant import Tenant

from workers.base import BaseWorker

logger = logging.getLogger(__name__)


class AnalyticsWorker(BaseWorker):
    """Worker for aggregating analytics."""

    name = "analytics_worker"

    async def process(self):
        """Main processing loop - run aggregation on schedule."""
        while not self._shutdown:
            try:
                await self.aggregate_all_tenants()
                # Run every 5 minutes
                await asyncio.sleep(300)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in analytics worker: {e}", exc_info=True)
                await asyncio.sleep(60)

    async def aggregate_all_tenants(self):
        """Aggregate metrics for all tenants."""
        logger.info("Starting analytics aggregation")

        async with get_session() as session:
            # Get all active tenants
            result = await session.execute(
                select(Tenant.id).where(Tenant.is_active == True)
            )
            tenant_ids = [row[0] for row in result.fetchall()]

            for tenant_id in tenant_ids:
                try:
                    await self.aggregate_tenant_metrics(session, tenant_id)
                except Exception as e:
                    logger.error(f"Error aggregating tenant {tenant_id}: {e}")

        logger.info(f"Analytics aggregation completed for {len(tenant_ids)} tenants")

    async def aggregate_tenant_metrics(
        self, session: AsyncSession, tenant_id: UUID
    ):
        """Aggregate metrics for a single tenant."""
        now = datetime.now(timezone.utc)

        # Aggregate hourly metrics
        await self._aggregate_period(
            session, tenant_id, SnapshotPeriod.HOURLY, now
        )

        # Aggregate daily metrics
        await self._aggregate_period(
            session, tenant_id, SnapshotPeriod.DAILY, now
        )

    async def _aggregate_period(
        self,
        session: AsyncSession,
        tenant_id: UUID,
        period: SnapshotPeriod,
        now: datetime,
    ):
        """Aggregate metrics for a specific period."""
        if period == SnapshotPeriod.HOURLY:
            period_start = now.replace(minute=0, second=0, microsecond=0)
            period_end = period_start + timedelta(hours=1)
        elif period == SnapshotPeriod.DAILY:
            period_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            period_end = period_start + timedelta(days=1)
        elif period == SnapshotPeriod.WEEKLY:
            # Start of week (Monday)
            period_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            period_start = period_start - timedelta(days=period_start.weekday())
            period_end = period_start + timedelta(weeks=1)
        else:  # MONTHLY
            period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            # Next month
            if period_start.month == 12:
                period_end = period_start.replace(year=period_start.year + 1, month=1)
            else:
                period_end = period_start.replace(month=period_start.month + 1)

        # Check if snapshot exists
        existing = await session.execute(
            select(AnalyticsSnapshot).where(
                and_(
                    AnalyticsSnapshot.tenant_id == tenant_id,
                    AnalyticsSnapshot.period == period,
                    AnalyticsSnapshot.period_start == period_start,
                )
            )
        )
        snapshot = existing.scalar_one_or_none()

        if not snapshot:
            snapshot = AnalyticsSnapshot(
                tenant_id=tenant_id,
                period=period,
                period_start=period_start,
                period_end=period_end,
            )
            session.add(snapshot)

        # Aggregate all metrics
        await self._aggregate_conversation_metrics(session, snapshot, period_start, period_end)
        await self._aggregate_message_metrics(session, snapshot, tenant_id, period_start, period_end)
        await self._aggregate_customer_metrics(session, snapshot, tenant_id, period_start, period_end)
        await self._aggregate_operator_metrics(session, snapshot, tenant_id, period_start, period_end)
        await self._aggregate_channel_metrics(session, snapshot, tenant_id, period_start, period_end)
        await self._aggregate_csat_metrics(session, snapshot, tenant_id, period_start, period_end)
        await self._aggregate_tag_metrics(session, snapshot, tenant_id, period_start, period_end)

        await session.commit()
        logger.debug(f"Updated {period.value} analytics for tenant {tenant_id}")

    async def _aggregate_conversation_metrics(
        self,
        session: AsyncSession,
        snapshot: AnalyticsSnapshot,
        period_start: datetime,
        period_end: datetime,
    ):
        """Aggregate conversation metrics."""
        tenant_id = snapshot.tenant_id

        # Total conversations in period
        total_result = await session.execute(
            select(func.count(Conversation.id)).where(
                and_(
                    Conversation.tenant_id == tenant_id,
                    Conversation.created_at >= period_start,
                    Conversation.created_at < period_end,
                )
            )
        )
        snapshot.conversations_new = total_result.scalar() or 0

        # Total conversations (all time up to period end)
        all_result = await session.execute(
            select(func.count(Conversation.id)).where(
                and_(
                    Conversation.tenant_id == tenant_id,
                    Conversation.created_at < period_end,
                )
            )
        )
        snapshot.conversations_total = all_result.scalar() or 0

        # Resolved in period
        resolved_result = await session.execute(
            select(func.count(Conversation.id)).where(
                and_(
                    Conversation.tenant_id == tenant_id,
                    Conversation.resolved_at >= period_start,
                    Conversation.resolved_at < period_end,
                )
            )
        )
        snapshot.conversations_resolved = resolved_result.scalar() or 0

        # Closed in period
        closed_result = await session.execute(
            select(func.count(Conversation.id)).where(
                and_(
                    Conversation.tenant_id == tenant_id,
                    Conversation.closed_at >= period_start,
                    Conversation.closed_at < period_end,
                )
            )
        )
        snapshot.conversations_closed = closed_result.scalar() or 0

        # Average first response time (for conversations with first response in period)
        avg_frt_result = await session.execute(
            select(
                func.avg(
                    extract('epoch', Conversation.first_response_at - Conversation.created_at)
                )
            ).where(
                and_(
                    Conversation.tenant_id == tenant_id,
                    Conversation.first_response_at >= period_start,
                    Conversation.first_response_at < period_end,
                    Conversation.first_response_at.isnot(None),
                )
            )
        )
        avg_frt = avg_frt_result.scalar()
        snapshot.avg_first_response_time = int(avg_frt) if avg_frt else None

        # Average resolution time
        avg_resolution_result = await session.execute(
            select(
                func.avg(
                    extract('epoch', Conversation.resolved_at - Conversation.created_at)
                )
            ).where(
                and_(
                    Conversation.tenant_id == tenant_id,
                    Conversation.resolved_at >= period_start,
                    Conversation.resolved_at < period_end,
                    Conversation.resolved_at.isnot(None),
                )
            )
        )
        avg_resolution = avg_resolution_result.scalar()
        snapshot.avg_resolution_time = int(avg_resolution) if avg_resolution else None

    async def _aggregate_message_metrics(
        self,
        session: AsyncSession,
        snapshot: AnalyticsSnapshot,
        tenant_id: UUID,
        period_start: datetime,
        period_end: datetime,
    ):
        """Aggregate message metrics."""
        # Total messages in period
        total_result = await session.execute(
            select(func.count(Message.id))
            .join(Conversation)
            .where(
                and_(
                    Conversation.tenant_id == tenant_id,
                    Message.created_at >= period_start,
                    Message.created_at < period_end,
                )
            )
        )
        snapshot.messages_total = total_result.scalar() or 0

        # Inbound (customer) messages
        inbound_result = await session.execute(
            select(func.count(Message.id))
            .join(Conversation)
            .where(
                and_(
                    Conversation.tenant_id == tenant_id,
                    Message.created_at >= period_start,
                    Message.created_at < period_end,
                    Message.sender_type == "customer",
                )
            )
        )
        snapshot.messages_inbound = inbound_result.scalar() or 0

        # Outbound (operator/system) messages
        snapshot.messages_outbound = snapshot.messages_total - snapshot.messages_inbound

    async def _aggregate_customer_metrics(
        self,
        session: AsyncSession,
        snapshot: AnalyticsSnapshot,
        tenant_id: UUID,
        period_start: datetime,
        period_end: datetime,
    ):
        """Aggregate customer metrics."""
        # New customers in period
        new_result = await session.execute(
            select(func.count(Customer.id)).where(
                and_(
                    Customer.tenant_id == tenant_id,
                    Customer.created_at >= period_start,
                    Customer.created_at < period_end,
                )
            )
        )
        snapshot.customers_new = new_result.scalar() or 0

        # Active customers (had conversation in period)
        active_result = await session.execute(
            select(func.count(func.distinct(Conversation.customer_id))).where(
                and_(
                    Conversation.tenant_id == tenant_id,
                    Conversation.last_message_at >= period_start,
                    Conversation.last_message_at < period_end,
                )
            )
        )
        snapshot.customers_active = active_result.scalar() or 0

    async def _aggregate_operator_metrics(
        self,
        session: AsyncSession,
        snapshot: AnalyticsSnapshot,
        tenant_id: UUID,
        period_start: datetime,
        period_end: datetime,
    ):
        """Aggregate operator performance metrics."""
        # Conversations handled per operator
        per_operator = await session.execute(
            select(
                Conversation.assigned_to,
                func.count(Conversation.id).label("total"),
                func.count(
                    case((Conversation.status == ConversationStatus.RESOLVED, 1))
                ).label("resolved"),
                func.avg(
                    extract('epoch', Conversation.first_response_at - Conversation.created_at)
                ).label("avg_frt"),
            )
            .where(
                and_(
                    Conversation.tenant_id == tenant_id,
                    Conversation.created_at >= period_start,
                    Conversation.created_at < period_end,
                    Conversation.assigned_to.isnot(None),
                )
            )
            .group_by(Conversation.assigned_to)
        )

        operator_metrics = {}
        for row in per_operator.fetchall():
            if row[0]:
                operator_metrics[str(row[0])] = {
                    "conversations": row[1],
                    "resolved": row[2],
                    "avg_first_response_time": int(row[3]) if row[3] else None,
                }

        snapshot.operator_metrics = operator_metrics

    async def _aggregate_channel_metrics(
        self,
        session: AsyncSession,
        snapshot: AnalyticsSnapshot,
        tenant_id: UUID,
        period_start: datetime,
        period_end: datetime,
    ):
        """Aggregate channel metrics."""
        # Conversations per channel
        per_channel = await session.execute(
            select(
                Conversation.channel,
                func.count(Conversation.id).label("conversations"),
            )
            .where(
                and_(
                    Conversation.tenant_id == tenant_id,
                    Conversation.created_at >= period_start,
                    Conversation.created_at < period_end,
                )
            )
            .group_by(Conversation.channel)
        )

        channel_metrics = {}
        for row in per_channel.fetchall():
            channel_name = row[0].value if hasattr(row[0], 'value') else str(row[0])
            channel_metrics[channel_name] = {
                "conversations": row[1],
            }

        # Messages per channel
        messages_per_channel = await session.execute(
            select(
                Conversation.channel,
                func.count(Message.id).label("messages"),
            )
            .join(Conversation)
            .where(
                and_(
                    Conversation.tenant_id == tenant_id,
                    Message.created_at >= period_start,
                    Message.created_at < period_end,
                )
            )
            .group_by(Conversation.channel)
        )

        for row in messages_per_channel.fetchall():
            channel_name = row[0].value if hasattr(row[0], 'value') else str(row[0])
            if channel_name in channel_metrics:
                channel_metrics[channel_name]["messages"] = row[1]
            else:
                channel_metrics[channel_name] = {"conversations": 0, "messages": row[1]}

        snapshot.channel_metrics = channel_metrics

    async def _aggregate_csat_metrics(
        self,
        session: AsyncSession,
        snapshot: AnalyticsSnapshot,
        tenant_id: UUID,
        period_start: datetime,
        period_end: datetime,
    ):
        """Aggregate CSAT metrics."""
        # Get CSAT scores from conversations with ratings in period
        csat_result = await session.execute(
            select(
                func.count(Conversation.id),
                func.avg(Conversation.metadata['csat_score'].astext.cast(sa.Float)),
            )
            .where(
                and_(
                    Conversation.tenant_id == tenant_id,
                    Conversation.closed_at >= period_start,
                    Conversation.closed_at < period_end,
                    Conversation.metadata['csat_score'].isnot(None),
                )
            )
        )
        row = csat_result.fetchone()

        if row and row[0]:
            snapshot.csat_responses = row[0]
            snapshot.csat_score_avg = float(row[1]) if row[1] else None
        else:
            snapshot.csat_responses = 0
            snapshot.csat_score_avg = None

        # Distribution (1-5 scores)
        distribution = {}
        for score in range(1, 6):
            score_count = await session.execute(
                select(func.count(Conversation.id)).where(
                    and_(
                        Conversation.tenant_id == tenant_id,
                        Conversation.closed_at >= period_start,
                        Conversation.closed_at < period_end,
                        Conversation.metadata['csat_score'].astext == str(score),
                    )
                )
            )
            count = score_count.scalar() or 0
            if count > 0:
                distribution[str(score)] = count

        snapshot.csat_score_distribution = distribution

    async def _aggregate_tag_metrics(
        self,
        session: AsyncSession,
        snapshot: AnalyticsSnapshot,
        tenant_id: UUID,
        period_start: datetime,
        period_end: datetime,
    ):
        """Aggregate tag usage metrics."""
        # Get all conversations with tags in period
        result = await session.execute(
            select(Conversation.tags).where(
                and_(
                    Conversation.tenant_id == tenant_id,
                    Conversation.created_at >= period_start,
                    Conversation.created_at < period_end,
                    Conversation.tags.isnot(None),
                )
            )
        )

        tag_counts = {}
        for row in result.fetchall():
            tags = row[0] or []
            for tag in tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

        snapshot.tag_metrics = tag_counts


# Import for CSAT aggregation
import sqlalchemy as sa


async def main():
    """Run analytics worker."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    worker = AnalyticsWorker()
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
