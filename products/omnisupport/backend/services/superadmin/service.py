"""Superadmin service for platform management."""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Sequence

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from shared.models.tenant import Tenant
from shared.models.user import User
from shared.models.conversation import Conversation, Message
from shared.models.customer import Customer
from shared.models.billing import Subscription, Plan, SubscriptionStatus, Invoice
from shared.models.ai import AIInteraction


class SuperadminService:
    """Service for superadmin platform management."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # ==================== Tenants ====================

    async def list_tenants(
        self,
        search: str | None = None,
        is_active: bool | None = None,
        subscription_status: SubscriptionStatus | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[Sequence[Tenant], int]:
        """List all tenants with filters."""
        query = select(Tenant)

        if search:
            query = query.where(
                or_(
                    Tenant.name.ilike(f"%{search}%"),
                    Tenant.slug.ilike(f"%{search}%"),
                    Tenant.email.ilike(f"%{search}%"),
                )
            )

        if is_active is not None:
            query = query.where(Tenant.is_active == is_active)

        # Count
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.session.execute(count_query)).scalar() or 0

        # Get items with subscription
        query = (
            query.options(selectinload(Tenant.subscription).selectinload(Subscription.plan))
            .order_by(Tenant.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        result = await self.session.execute(query)
        tenants = result.scalars().all()

        # Filter by subscription status if needed
        if subscription_status:
            tenants = [
                t for t in tenants
                if t.subscription and t.subscription.status == subscription_status
            ]

        return tenants, total

    async def get_tenant(self, tenant_id: uuid.UUID) -> Tenant | None:
        """Get tenant by ID with all relations."""
        result = await self.session.execute(
            select(Tenant)
            .where(Tenant.id == tenant_id)
            .options(
                selectinload(Tenant.subscription).selectinload(Subscription.plan),
                selectinload(Tenant.users),
            )
        )
        return result.scalar_one_or_none()

    async def get_tenant_by_slug(self, slug: str) -> Tenant | None:
        """Get tenant by slug."""
        result = await self.session.execute(
            select(Tenant).where(Tenant.slug == slug)
        )
        return result.scalar_one_or_none()

    async def create_tenant(
        self,
        name: str,
        slug: str,
        email: str | None = None,
        plan_id: uuid.UUID | None = None,
        settings: dict | None = None,
    ) -> Tenant:
        """Create new tenant."""
        tenant = Tenant(
            name=name,
            slug=slug,
            email=email,
            settings=settings or {},
        )
        self.session.add(tenant)
        await self.session.flush()

        # Create subscription if plan provided
        if plan_id:
            from services.admin.billing.service import BillingService
            billing = BillingService(self.session)
            await billing.create_subscription(
                tenant_id=tenant.id,
                plan_id=plan_id,
            )

        return tenant

    async def update_tenant(
        self,
        tenant_id: uuid.UUID,
        **kwargs,
    ) -> Tenant | None:
        """Update tenant."""
        tenant = await self.get_tenant(tenant_id)
        if not tenant:
            return None

        for key, value in kwargs.items():
            if hasattr(tenant, key) and value is not None:
                setattr(tenant, key, value)

        await self.session.flush()
        return tenant

    async def deactivate_tenant(self, tenant_id: uuid.UUID) -> Tenant | None:
        """Deactivate tenant."""
        tenant = await self.get_tenant(tenant_id)
        if not tenant:
            return None

        tenant.is_active = False
        await self.session.flush()
        return tenant

    async def activate_tenant(self, tenant_id: uuid.UUID) -> Tenant | None:
        """Activate tenant."""
        tenant = await self.get_tenant(tenant_id)
        if not tenant:
            return None

        tenant.is_active = True
        await self.session.flush()
        return tenant

    async def delete_tenant(self, tenant_id: uuid.UUID) -> bool:
        """Delete tenant (hard delete). Use with caution."""
        tenant = await self.get_tenant(tenant_id)
        if not tenant:
            return False

        await self.session.delete(tenant)
        await self.session.flush()
        return True

    async def get_tenant_stats(self, tenant_id: uuid.UUID) -> dict:
        """Get detailed stats for a tenant."""
        # Users count
        users_result = await self.session.execute(
            select(func.count(User.id)).where(User.tenant_id == tenant_id)
        )
        users_count = users_result.scalar() or 0

        # Customers count
        customers_result = await self.session.execute(
            select(func.count(Customer.id)).where(Customer.tenant_id == tenant_id)
        )
        customers_count = customers_result.scalar() or 0

        # Conversations count
        conversations_result = await self.session.execute(
            select(func.count(Conversation.id)).where(Conversation.tenant_id == tenant_id)
        )
        conversations_count = conversations_result.scalar() or 0

        # Messages count
        messages_result = await self.session.execute(
            select(func.count(Message.id))
            .join(Conversation)
            .where(Conversation.tenant_id == tenant_id)
        )
        messages_count = messages_result.scalar() or 0

        # AI interactions count (this month)
        today = datetime.now(timezone.utc).date()
        month_start = today.replace(day=1)
        ai_result = await self.session.execute(
            select(func.count(AIInteraction.id))
            .where(AIInteraction.tenant_id == tenant_id)
            .where(AIInteraction.created_at >= datetime.combine(month_start, datetime.min.time()))
        )
        ai_interactions = ai_result.scalar() or 0

        return {
            "users": users_count,
            "customers": customers_count,
            "conversations": conversations_count,
            "messages": messages_count,
            "ai_interactions_this_month": ai_interactions,
        }

    # ==================== Platform Stats ====================

    async def get_platform_stats(self) -> dict:
        """Get overall platform statistics."""
        # Tenants
        tenants_result = await self.session.execute(
            select(func.count(Tenant.id))
        )
        total_tenants = tenants_result.scalar() or 0

        active_tenants_result = await self.session.execute(
            select(func.count(Tenant.id)).where(Tenant.is_active == True)
        )
        active_tenants = active_tenants_result.scalar() or 0

        # Users
        users_result = await self.session.execute(
            select(func.count(User.id))
        )
        total_users = users_result.scalar() or 0

        # Customers
        customers_result = await self.session.execute(
            select(func.count(Customer.id))
        )
        total_customers = customers_result.scalar() or 0

        # Conversations
        conversations_result = await self.session.execute(
            select(func.count(Conversation.id))
        )
        total_conversations = conversations_result.scalar() or 0

        # Messages
        messages_result = await self.session.execute(
            select(func.count(Message.id))
        )
        total_messages = messages_result.scalar() or 0

        # Subscriptions by status
        subscriptions_result = await self.session.execute(
            select(Subscription.status, func.count(Subscription.id))
            .group_by(Subscription.status)
        )
        subscriptions_by_status = {
            row[0].value if hasattr(row[0], 'value') else row[0]: row[1]
            for row in subscriptions_result
        }

        # Revenue (paid invoices)
        revenue_result = await self.session.execute(
            select(func.sum(Invoice.total))
            .where(Invoice.status == "paid")
        )
        total_revenue = revenue_result.scalar() or 0

        # New tenants this month
        today = datetime.now(timezone.utc).date()
        month_start = today.replace(day=1)
        new_tenants_result = await self.session.execute(
            select(func.count(Tenant.id))
            .where(Tenant.created_at >= datetime.combine(month_start, datetime.min.time()))
        )
        new_tenants_this_month = new_tenants_result.scalar() or 0

        return {
            "tenants": {
                "total": total_tenants,
                "active": active_tenants,
                "new_this_month": new_tenants_this_month,
            },
            "users": {
                "total": total_users,
            },
            "customers": {
                "total": total_customers,
            },
            "conversations": {
                "total": total_conversations,
            },
            "messages": {
                "total": total_messages,
            },
            "subscriptions": subscriptions_by_status,
            "revenue": {
                "total": total_revenue,
                "currency": "RUB",
            },
        }

    async def get_platform_growth(self, days: int = 30) -> list[dict]:
        """Get platform growth data for the last N days."""
        end_date = datetime.now(timezone.utc).date()
        start_date = end_date - timedelta(days=days)

        growth_data = []
        current_date = start_date

        while current_date <= end_date:
            next_date = current_date + timedelta(days=1)

            # New tenants on this day
            tenants_result = await self.session.execute(
                select(func.count(Tenant.id))
                .where(
                    and_(
                        Tenant.created_at >= datetime.combine(current_date, datetime.min.time()),
                        Tenant.created_at < datetime.combine(next_date, datetime.min.time()),
                    )
                )
            )
            new_tenants = tenants_result.scalar() or 0

            # New users on this day
            users_result = await self.session.execute(
                select(func.count(User.id))
                .where(
                    and_(
                        User.created_at >= datetime.combine(current_date, datetime.min.time()),
                        User.created_at < datetime.combine(next_date, datetime.min.time()),
                    )
                )
            )
            new_users = users_result.scalar() or 0

            # Conversations on this day
            conversations_result = await self.session.execute(
                select(func.count(Conversation.id))
                .where(
                    and_(
                        Conversation.created_at >= datetime.combine(current_date, datetime.min.time()),
                        Conversation.created_at < datetime.combine(next_date, datetime.min.time()),
                    )
                )
            )
            conversations = conversations_result.scalar() or 0

            growth_data.append({
                "date": current_date.isoformat(),
                "new_tenants": new_tenants,
                "new_users": new_users,
                "conversations": conversations,
            })

            current_date = next_date

        return growth_data

    # ==================== Plans Management ====================

    async def list_plans(self, include_inactive: bool = False) -> Sequence[Plan]:
        """List all plans."""
        query = select(Plan).order_by(Plan.sort_order)
        if not include_inactive:
            query = query.where(Plan.is_active == True)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def create_plan(
        self,
        name: str,
        display_name: str,
        price_monthly: int,
        price_yearly: int,
        features: list[str] | None = None,
        limits: dict | None = None,
        description: str | None = None,
        trial_days: int = 14,
        is_featured: bool = False,
        sort_order: int = 0,
    ) -> Plan:
        """Create new plan."""
        plan = Plan(
            name=name,
            display_name=display_name,
            price_monthly=price_monthly,
            price_yearly=price_yearly,
            features=features or [],
            limits=limits or {},
            description=description,
            trial_days=trial_days,
            is_featured=is_featured,
            sort_order=sort_order,
        )
        self.session.add(plan)
        await self.session.flush()
        return plan

    async def update_plan(self, plan_id: uuid.UUID, **kwargs) -> Plan | None:
        """Update plan."""
        result = await self.session.execute(
            select(Plan).where(Plan.id == plan_id)
        )
        plan = result.scalar_one_or_none()
        if not plan:
            return None

        for key, value in kwargs.items():
            if hasattr(plan, key) and value is not None:
                setattr(plan, key, value)

        await self.session.flush()
        return plan


async def get_superadmin_service(session: AsyncSession) -> SuperadminService:
    """Get superadmin service instance."""
    return SuperadminService(session)
