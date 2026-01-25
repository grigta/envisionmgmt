"""Usage tracking service."""

import uuid
from datetime import date, datetime, timezone, timedelta
from typing import Sequence

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.billing import (
    UsageRecord,
    UsageType,
    Subscription,
)
from shared.models.conversation import Conversation, Message
from shared.models.ai import AIInteraction


class UsageTracker:
    """Service for tracking resource usage."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_current_usage(
        self,
        tenant_id: uuid.UUID,
        usage_type: UsageType | None = None,
    ) -> dict[str, dict]:
        """
        Get current period usage for tenant.

        Returns:
            Dict mapping usage type to {quantity, limit, percentage}
        """
        today = date.today()
        period_start = today.replace(day=1)
        period_end = (period_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)

        query = (
            select(UsageRecord)
            .where(UsageRecord.tenant_id == tenant_id)
            .where(UsageRecord.period_start >= period_start)
            .where(UsageRecord.period_end <= period_end)
        )

        if usage_type:
            query = query.where(UsageRecord.usage_type == usage_type)

        result = await self.session.execute(query)
        records = result.scalars().all()

        usage = {}
        for record in records:
            limit = record.limit or 0
            percentage = (record.quantity / limit * 100) if limit > 0 else 0
            usage[record.usage_type.value] = {
                "quantity": record.quantity,
                "limit": limit,
                "percentage": min(percentage, 100),
                "exceeded": record.quantity > limit if limit > 0 else False,
            }

        return usage

    async def get_usage_history(
        self,
        tenant_id: uuid.UUID,
        usage_type: UsageType | None = None,
        months: int = 6,
    ) -> list[dict]:
        """Get usage history for past months."""
        today = date.today()
        start_date = (today - timedelta(days=30 * months)).replace(day=1)

        query = (
            select(UsageRecord)
            .where(UsageRecord.tenant_id == tenant_id)
            .where(UsageRecord.period_start >= start_date)
            .order_by(UsageRecord.period_start)
        )

        if usage_type:
            query = query.where(UsageRecord.usage_type == usage_type)

        result = await self.session.execute(query)
        records = result.scalars().all()

        history = []
        for record in records:
            history.append({
                "period_start": record.period_start.isoformat(),
                "period_end": record.period_end.isoformat(),
                "usage_type": record.usage_type.value,
                "quantity": record.quantity,
                "limit": record.limit,
            })

        return history

    async def record_usage(
        self,
        tenant_id: uuid.UUID,
        usage_type: UsageType,
        quantity: int,
        limit: int | None = None,
        metadata: dict | None = None,
    ) -> UsageRecord:
        """Record usage for current period."""
        today = date.today()
        period_start = today.replace(day=1)
        period_end = (period_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)

        # Check if record exists
        result = await self.session.execute(
            select(UsageRecord)
            .where(UsageRecord.tenant_id == tenant_id)
            .where(UsageRecord.usage_type == usage_type)
            .where(UsageRecord.period_start == period_start)
        )
        record = result.scalar_one_or_none()

        if record:
            record.quantity = quantity
            if limit is not None:
                record.limit = limit
            if metadata:
                record.metadata = {**record.metadata, **metadata}
        else:
            record = UsageRecord(
                tenant_id=tenant_id,
                usage_type=usage_type,
                period_start=period_start,
                period_end=period_end,
                quantity=quantity,
                limit=limit,
                metadata=metadata or {},
            )
            self.session.add(record)

        await self.session.flush()
        return record

    async def increment_usage(
        self,
        tenant_id: uuid.UUID,
        usage_type: UsageType,
        amount: int = 1,
    ) -> UsageRecord:
        """Increment usage counter."""
        today = date.today()
        period_start = today.replace(day=1)
        period_end = (period_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)

        result = await self.session.execute(
            select(UsageRecord)
            .where(UsageRecord.tenant_id == tenant_id)
            .where(UsageRecord.usage_type == usage_type)
            .where(UsageRecord.period_start == period_start)
        )
        record = result.scalar_one_or_none()

        if record:
            record.quantity += amount
        else:
            # Get limit from subscription
            limit = await self._get_limit_for_type(tenant_id, usage_type)
            record = UsageRecord(
                tenant_id=tenant_id,
                usage_type=usage_type,
                period_start=period_start,
                period_end=period_end,
                quantity=amount,
                limit=limit,
            )
            self.session.add(record)

        await self.session.flush()
        return record

    async def check_limit(
        self,
        tenant_id: uuid.UUID,
        usage_type: UsageType,
    ) -> tuple[bool, int, int]:
        """
        Check if usage is within limits.

        Returns:
            Tuple of (within_limit, current_usage, limit)
        """
        usage = await self.get_current_usage(tenant_id, usage_type)

        if usage_type.value not in usage:
            # No usage recorded yet - get limit from subscription
            limit = await self._get_limit_for_type(tenant_id, usage_type)
            return True, 0, limit or 0

        data = usage[usage_type.value]
        within_limit = not data["exceeded"]
        return within_limit, data["quantity"], data["limit"]

    async def aggregate_usage(self, tenant_id: uuid.UUID) -> dict[str, int]:
        """
        Aggregate actual usage from database.

        This calculates real usage by counting conversations, messages, etc.
        """
        today = date.today()
        period_start = today.replace(day=1)
        period_end = (period_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)

        usage = {}

        # Conversations count
        conv_result = await self.session.execute(
            select(func.count(Conversation.id))
            .where(Conversation.tenant_id == tenant_id)
            .where(Conversation.created_at >= datetime.combine(period_start, datetime.min.time()))
            .where(Conversation.created_at < datetime.combine(period_end + timedelta(days=1), datetime.min.time()))
        )
        usage[UsageType.CONVERSATIONS.value] = conv_result.scalar() or 0

        # Messages count
        msg_result = await self.session.execute(
            select(func.count(Message.id))
            .join(Conversation)
            .where(Conversation.tenant_id == tenant_id)
            .where(Message.created_at >= datetime.combine(period_start, datetime.min.time()))
            .where(Message.created_at < datetime.combine(period_end + timedelta(days=1), datetime.min.time()))
        )
        usage[UsageType.MESSAGES.value] = msg_result.scalar() or 0

        # AI requests count
        ai_result = await self.session.execute(
            select(func.count(AIInteraction.id))
            .where(AIInteraction.tenant_id == tenant_id)
            .where(AIInteraction.created_at >= datetime.combine(period_start, datetime.min.time()))
            .where(AIInteraction.created_at < datetime.combine(period_end + timedelta(days=1), datetime.min.time()))
        )
        usage[UsageType.AI_REQUESTS.value] = ai_result.scalar() or 0

        return usage

    async def sync_usage(self, tenant_id: uuid.UUID) -> dict[str, UsageRecord]:
        """
        Sync usage records with actual database counts.

        Returns dict of usage_type -> UsageRecord
        """
        actual_usage = await self.aggregate_usage(tenant_id)
        records = {}

        for usage_type_value, quantity in actual_usage.items():
            usage_type = UsageType(usage_type_value)
            limit = await self._get_limit_for_type(tenant_id, usage_type)
            record = await self.record_usage(
                tenant_id=tenant_id,
                usage_type=usage_type,
                quantity=quantity,
                limit=limit,
            )
            records[usage_type_value] = record

        return records

    async def _get_limit_for_type(
        self,
        tenant_id: uuid.UUID,
        usage_type: UsageType,
    ) -> int | None:
        """Get limit for usage type from subscription plan."""
        result = await self.session.execute(
            select(Subscription)
            .where(Subscription.tenant_id == tenant_id)
        )
        subscription = result.scalar_one_or_none()

        if not subscription:
            return None

        # Load plan
        from shared.models.billing import Plan
        plan_result = await self.session.execute(
            select(Plan).where(Plan.id == subscription.plan_id)
        )
        plan = plan_result.scalar_one_or_none()

        if not plan or not plan.limits:
            return None

        # Map usage type to limit key
        limit_keys = {
            UsageType.CONVERSATIONS: "conversations",
            UsageType.MESSAGES: "messages",
            UsageType.AI_REQUESTS: "ai_requests",
            UsageType.STORAGE: "storage_gb",
            UsageType.API_CALLS: "api_calls",
        }

        key = limit_keys.get(usage_type)
        return plan.limits.get(key) if key else None

    async def get_usage_summary(
        self,
        tenant_id: uuid.UUID,
    ) -> dict:
        """
        Get comprehensive usage summary for tenant.

        Includes current usage, limits, and historical trends.
        """
        current = await self.get_current_usage(tenant_id)
        history = await self.get_usage_history(tenant_id, months=3)

        # Calculate trends
        trends = {}
        for usage_type in UsageType:
            type_value = usage_type.value
            type_history = [h for h in history if h["usage_type"] == type_value]

            if len(type_history) >= 2:
                prev = type_history[-2]["quantity"] if len(type_history) > 1 else 0
                curr = type_history[-1]["quantity"] if type_history else 0
                if prev > 0:
                    change_pct = ((curr - prev) / prev) * 100
                else:
                    change_pct = 100 if curr > 0 else 0
                trends[type_value] = {
                    "change_percentage": round(change_pct, 1),
                    "direction": "up" if change_pct > 0 else "down" if change_pct < 0 else "stable",
                }
            else:
                trends[type_value] = {
                    "change_percentage": 0,
                    "direction": "stable",
                }

        return {
            "current": current,
            "trends": trends,
            "period": {
                "start": date.today().replace(day=1).isoformat(),
                "end": date.today().isoformat(),
            },
        }


async def get_usage_tracker(session: AsyncSession) -> UsageTracker:
    """Get usage tracker instance."""
    return UsageTracker(session)
