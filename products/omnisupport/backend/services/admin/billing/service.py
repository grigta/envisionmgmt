"""Billing service for subscription management."""

import uuid
from datetime import date, datetime, timezone, timedelta
from typing import Sequence

from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from shared.models.billing import (
    Plan,
    Subscription,
    SubscriptionStatus,
    Invoice,
    InvoiceStatus,
    PaymentMethod,
    PaymentMethodType,
    BillingPeriod,
    UsageRecord,
)


class BillingService:
    """Service for managing subscriptions, invoices, and payments."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # ==================== Plans ====================

    async def list_plans(self, active_only: bool = True) -> Sequence[Plan]:
        """List available plans."""
        query = select(Plan).order_by(Plan.sort_order)
        if active_only:
            query = query.where(Plan.is_active == True)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_plan(self, plan_id: uuid.UUID) -> Plan | None:
        """Get plan by ID."""
        result = await self.session.execute(
            select(Plan).where(Plan.id == plan_id)
        )
        return result.scalar_one_or_none()

    async def get_plan_by_name(self, name: str) -> Plan | None:
        """Get plan by name."""
        result = await self.session.execute(
            select(Plan).where(Plan.name == name)
        )
        return result.scalar_one_or_none()

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
        """Create a new plan."""
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

    async def update_plan(
        self,
        plan_id: uuid.UUID,
        **kwargs,
    ) -> Plan | None:
        """Update plan."""
        plan = await self.get_plan(plan_id)
        if not plan:
            return None

        for key, value in kwargs.items():
            if hasattr(plan, key) and value is not None:
                setattr(plan, key, value)

        await self.session.flush()
        return plan

    # ==================== Subscriptions ====================

    async def get_subscription(
        self,
        tenant_id: uuid.UUID,
        include_plan: bool = True,
    ) -> Subscription | None:
        """Get tenant's subscription."""
        query = select(Subscription).where(Subscription.tenant_id == tenant_id)
        if include_plan:
            query = query.options(selectinload(Subscription.plan))
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def create_subscription(
        self,
        tenant_id: uuid.UUID,
        plan_id: uuid.UUID,
        billing_period: BillingPeriod = BillingPeriod.MONTHLY,
        start_trial: bool = True,
    ) -> Subscription:
        """Create subscription for tenant."""
        plan = await self.get_plan(plan_id)
        if not plan:
            raise ValueError("Plan not found")

        today = date.today()

        if start_trial and plan.trial_days > 0:
            trial_end = today + timedelta(days=plan.trial_days)
            subscription = Subscription(
                tenant_id=tenant_id,
                plan_id=plan_id,
                billing_period=billing_period,
                status=SubscriptionStatus.TRIALING,
                trial_start=today,
                trial_end=trial_end,
                current_period_start=today,
                current_period_end=trial_end,
            )
        else:
            period_end = self._calculate_period_end(today, billing_period)
            subscription = Subscription(
                tenant_id=tenant_id,
                plan_id=plan_id,
                billing_period=billing_period,
                status=SubscriptionStatus.ACTIVE,
                current_period_start=today,
                current_period_end=period_end,
            )

        self.session.add(subscription)
        await self.session.flush()
        return subscription

    async def activate_subscription(
        self,
        tenant_id: uuid.UUID,
    ) -> Subscription | None:
        """Activate subscription after trial or payment."""
        subscription = await self.get_subscription(tenant_id)
        if not subscription:
            return None

        today = date.today()
        period_end = self._calculate_period_end(today, subscription.billing_period)

        subscription.status = SubscriptionStatus.ACTIVE
        subscription.current_period_start = today
        subscription.current_period_end = period_end
        subscription.trial_end = None

        await self.session.flush()
        return subscription

    async def change_plan(
        self,
        tenant_id: uuid.UUID,
        new_plan_id: uuid.UUID,
        immediately: bool = False,
        prorate: bool = True,
    ) -> tuple[Subscription | None, int]:
        """
        Change subscription plan.

        Returns:
            Tuple of (subscription, proration_amount in kopeks)
            Positive proration = customer owes money
            Negative proration = customer gets credit
        """
        subscription = await self.get_subscription(tenant_id)
        if not subscription:
            return None, 0

        new_plan = await self.get_plan(new_plan_id)
        if not new_plan:
            return None, 0

        old_plan = subscription.plan
        proration_amount = 0

        if prorate and subscription.status == SubscriptionStatus.ACTIVE:
            proration_amount = self._calculate_proration(
                subscription,
                old_plan,
                new_plan,
            )

        if immediately:
            subscription.plan_id = new_plan_id
        else:
            # Schedule for end of period
            subscription.plan_id = new_plan_id  # Simplified - in real app would schedule

        await self.session.flush()
        return subscription, proration_amount

    async def cancel_subscription(
        self,
        tenant_id: uuid.UUID,
        immediately: bool = False,
        reason: str | None = None,
    ) -> Subscription | None:
        """Cancel subscription."""
        subscription = await self.get_subscription(tenant_id)
        if not subscription:
            return None

        now = datetime.now(timezone.utc)

        if immediately:
            subscription.status = SubscriptionStatus.CANCELED
            subscription.canceled_at = now
        else:
            subscription.cancel_at_period_end = True
            subscription.canceled_at = now

        await self.session.flush()
        return subscription

    async def reactivate_subscription(
        self,
        tenant_id: uuid.UUID,
    ) -> Subscription | None:
        """Reactivate canceled subscription (before period end)."""
        subscription = await self.get_subscription(tenant_id)
        if not subscription:
            return None

        if subscription.status != SubscriptionStatus.CANCELED:
            subscription.cancel_at_period_end = False
            subscription.canceled_at = None

        await self.session.flush()
        return subscription

    async def process_expired_subscriptions(self) -> int:
        """Process subscriptions that need status updates. Returns count of updated."""
        today = date.today()
        count = 0

        # End trials
        result = await self.session.execute(
            select(Subscription).where(
                and_(
                    Subscription.status == SubscriptionStatus.TRIALING,
                    Subscription.trial_end <= today,
                )
            )
        )
        for sub in result.scalars():
            sub.status = SubscriptionStatus.EXPIRED
            count += 1

        # Cancel at period end
        result = await self.session.execute(
            select(Subscription).where(
                and_(
                    Subscription.cancel_at_period_end == True,
                    Subscription.current_period_end <= today,
                )
            )
        )
        for sub in result.scalars():
            sub.status = SubscriptionStatus.CANCELED
            count += 1

        # Expire past due subscriptions (after grace period)
        grace_period = timedelta(days=7)
        result = await self.session.execute(
            select(Subscription).where(
                and_(
                    Subscription.status == SubscriptionStatus.PAST_DUE,
                    Subscription.current_period_end <= today - grace_period,
                )
            )
        )
        for sub in result.scalars():
            sub.status = SubscriptionStatus.EXPIRED
            count += 1

        await self.session.flush()
        return count

    def _calculate_period_end(self, start: date, period: BillingPeriod) -> date:
        """Calculate end of billing period."""
        if period == BillingPeriod.MONTHLY:
            # Add one month
            month = start.month + 1
            year = start.year
            if month > 12:
                month = 1
                year += 1
            day = min(start.day, 28)  # Safe for all months
            return date(year, month, day)
        else:  # YEARLY
            return date(start.year + 1, start.month, start.day)

    def _calculate_proration(
        self,
        subscription: Subscription,
        old_plan: Plan,
        new_plan: Plan,
    ) -> int:
        """Calculate proration amount for plan change."""
        today = date.today()
        period_start = subscription.current_period_start
        period_end = subscription.current_period_end

        total_days = (period_end - period_start).days
        remaining_days = (period_end - today).days

        if total_days <= 0:
            return 0

        # Get prices based on billing period
        if subscription.billing_period == BillingPeriod.MONTHLY:
            old_price = old_plan.price_monthly
            new_price = new_plan.price_monthly
        else:
            old_price = old_plan.price_yearly
            new_price = new_plan.price_yearly

        # Calculate unused value from old plan
        daily_old = old_price / total_days
        unused_credit = int(daily_old * remaining_days)

        # Calculate cost for remaining days on new plan
        daily_new = new_price / total_days
        new_cost = int(daily_new * remaining_days)

        # Proration: positive = customer owes, negative = credit
        return new_cost - unused_credit

    # ==================== Invoices ====================

    async def list_invoices(
        self,
        tenant_id: uuid.UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[Sequence[Invoice], int]:
        """List invoices for tenant."""
        base_query = (
            select(Invoice)
            .join(Subscription)
            .where(Subscription.tenant_id == tenant_id)
        )

        # Count
        from sqlalchemy import func
        count_result = await self.session.execute(
            select(func.count()).select_from(base_query.subquery())
        )
        total = count_result.scalar() or 0

        # Get items
        result = await self.session.execute(
            base_query.order_by(Invoice.issued_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return result.scalars().all(), total

    async def get_invoice(
        self,
        invoice_id: uuid.UUID,
        tenant_id: uuid.UUID | None = None,
    ) -> Invoice | None:
        """Get invoice by ID."""
        query = select(Invoice).where(Invoice.id == invoice_id)
        if tenant_id:
            query = query.join(Subscription).where(Subscription.tenant_id == tenant_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def create_invoice(
        self,
        subscription: Subscription,
        items: list[dict] | None = None,
        period_start: date | None = None,
        period_end: date | None = None,
    ) -> Invoice:
        """Create invoice for subscription."""
        plan = subscription.plan
        period_start = period_start or subscription.current_period_start
        period_end = period_end or subscription.current_period_end

        # Calculate amount
        if subscription.billing_period == BillingPeriod.MONTHLY:
            amount = plan.price_monthly
        else:
            amount = plan.price_yearly

        # Generate invoice number
        number = await self._generate_invoice_number()

        # Create line items
        if items is None:
            items = [
                {
                    "description": f"{plan.display_name} ({subscription.billing_period.value})",
                    "quantity": 1,
                    "unit_price": amount,
                    "total": amount,
                }
            ]

        subtotal = sum(item["total"] for item in items)
        tax = int(subtotal * 0.20)  # 20% VAT
        total = subtotal + tax

        now = datetime.now(timezone.utc)
        due_at = now + timedelta(days=14)

        invoice = Invoice(
            subscription_id=subscription.id,
            number=number,
            status=InvoiceStatus.PENDING,
            subtotal=subtotal,
            tax=tax,
            total=total,
            currency=plan.currency,
            period_start=period_start,
            period_end=period_end,
            items=items,
            issued_at=now,
            due_at=due_at,
        )

        self.session.add(invoice)
        await self.session.flush()
        return invoice

    async def pay_invoice(
        self,
        invoice_id: uuid.UUID,
        payment_method_id: uuid.UUID | None = None,
        payment_reference: str | None = None,
    ) -> Invoice | None:
        """Mark invoice as paid."""
        invoice = await self.get_invoice(invoice_id)
        if not invoice:
            return None

        invoice.status = InvoiceStatus.PAID
        invoice.paid_at = datetime.now(timezone.utc)
        invoice.payment_reference = payment_reference

        # Get payment method info
        if payment_method_id:
            result = await self.session.execute(
                select(PaymentMethod).where(PaymentMethod.id == payment_method_id)
            )
            method = result.scalar_one_or_none()
            if method:
                invoice.payment_method = method.type.value

        await self.session.flush()
        return invoice

    async def void_invoice(self, invoice_id: uuid.UUID) -> Invoice | None:
        """Void an invoice."""
        invoice = await self.get_invoice(invoice_id)
        if not invoice or invoice.status == InvoiceStatus.PAID:
            return None

        invoice.status = InvoiceStatus.VOID
        await self.session.flush()
        return invoice

    async def refund_invoice(
        self,
        invoice_id: uuid.UUID,
        reason: str | None = None,
    ) -> Invoice | None:
        """Refund a paid invoice."""
        invoice = await self.get_invoice(invoice_id)
        if not invoice or invoice.status != InvoiceStatus.PAID:
            return None

        invoice.status = InvoiceStatus.REFUNDED
        await self.session.flush()
        return invoice

    async def _generate_invoice_number(self) -> str:
        """Generate unique invoice number."""
        now = datetime.now(timezone.utc)
        prefix = now.strftime("INV-%Y%m")

        # Get latest invoice number for this month
        result = await self.session.execute(
            select(Invoice)
            .where(Invoice.number.like(f"{prefix}%"))
            .order_by(Invoice.number.desc())
            .limit(1)
        )
        last_invoice = result.scalar_one_or_none()

        if last_invoice:
            # Extract sequence number and increment
            seq = int(last_invoice.number.split("-")[-1]) + 1
        else:
            seq = 1

        return f"{prefix}-{seq:04d}"

    # ==================== Payment Methods ====================

    async def list_payment_methods(
        self,
        tenant_id: uuid.UUID,
        active_only: bool = True,
    ) -> Sequence[PaymentMethod]:
        """List payment methods for tenant."""
        query = select(PaymentMethod).where(PaymentMethod.tenant_id == tenant_id)
        if active_only:
            query = query.where(PaymentMethod.is_active == True)
        query = query.order_by(PaymentMethod.is_default.desc())
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_payment_method(
        self,
        method_id: uuid.UUID,
        tenant_id: uuid.UUID | None = None,
    ) -> PaymentMethod | None:
        """Get payment method by ID."""
        query = select(PaymentMethod).where(PaymentMethod.id == method_id)
        if tenant_id:
            query = query.where(PaymentMethod.tenant_id == tenant_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_default_payment_method(
        self,
        tenant_id: uuid.UUID,
    ) -> PaymentMethod | None:
        """Get default payment method."""
        result = await self.session.execute(
            select(PaymentMethod)
            .where(PaymentMethod.tenant_id == tenant_id)
            .where(PaymentMethod.is_default == True)
            .where(PaymentMethod.is_active == True)
        )
        return result.scalar_one_or_none()

    async def add_payment_method(
        self,
        tenant_id: uuid.UUID,
        method_type: PaymentMethodType,
        card_brand: str | None = None,
        card_last4: str | None = None,
        card_exp_month: int | None = None,
        card_exp_year: int | None = None,
        bank_name: str | None = None,
        external_id: str | None = None,
        set_default: bool = False,
    ) -> PaymentMethod:
        """Add payment method."""
        # If setting as default, unset other defaults
        if set_default:
            await self.session.execute(
                update(PaymentMethod)
                .where(PaymentMethod.tenant_id == tenant_id)
                .values(is_default=False)
            )

        method = PaymentMethod(
            tenant_id=tenant_id,
            type=method_type,
            card_brand=card_brand,
            card_last4=card_last4,
            card_exp_month=card_exp_month,
            card_exp_year=card_exp_year,
            bank_name=bank_name,
            external_id=external_id,
            is_default=set_default,
        )

        self.session.add(method)
        await self.session.flush()
        return method

    async def set_default_payment_method(
        self,
        method_id: uuid.UUID,
        tenant_id: uuid.UUID,
    ) -> PaymentMethod | None:
        """Set payment method as default."""
        method = await self.get_payment_method(method_id, tenant_id)
        if not method:
            return None

        # Unset other defaults
        await self.session.execute(
            update(PaymentMethod)
            .where(PaymentMethod.tenant_id == tenant_id)
            .values(is_default=False)
        )

        method.is_default = True
        await self.session.flush()
        return method

    async def delete_payment_method(
        self,
        method_id: uuid.UUID,
        tenant_id: uuid.UUID,
    ) -> bool:
        """Delete (deactivate) payment method."""
        method = await self.get_payment_method(method_id, tenant_id)
        if not method:
            return False

        method.is_active = False
        await self.session.flush()
        return True


async def get_billing_service(session: AsyncSession) -> BillingService:
    """Get billing service instance."""
    return BillingService(session)
