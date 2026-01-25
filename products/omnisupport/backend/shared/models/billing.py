"""Billing models."""

import enum
import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.models.base import BaseModel

if TYPE_CHECKING:
    from shared.models.tenant import Tenant


class BillingPeriod(str, enum.Enum):
    """Billing period."""

    MONTHLY = "monthly"
    YEARLY = "yearly"


class Plan(BaseModel):
    """Subscription plan."""

    __tablename__ = "plans"

    # Basic info
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    # Pricing
    price_monthly: Mapped[int] = mapped_column(Integer, nullable=False)  # in kopeks/cents
    price_yearly: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="RUB", server_default="RUB")

    # Features and limits
    features: Mapped[list] = mapped_column(JSONB, default=list, server_default="[]")
    # e.g., ["unlimited_conversations", "ai_suggestions", "api_access"]

    limits: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")
    # e.g., {operators: 5, channels: 3, storage_gb: 10, ai_requests: 1000}

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    sort_order: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    # Trial
    trial_days: Mapped[int] = mapped_column(Integer, default=14, server_default="14")

    # Relationships
    subscriptions: Mapped[list["Subscription"]] = relationship(
        "Subscription", back_populates="plan"
    )

    def __repr__(self) -> str:
        return f"<Plan {self.name}>"


class SubscriptionStatus(str, enum.Enum):
    """Subscription status."""

    TRIALING = "trialing"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    EXPIRED = "expired"


class Subscription(BaseModel):
    """Tenant subscription."""

    __tablename__ = "subscriptions"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("plans.id", ondelete="RESTRICT"), nullable=False
    )

    # Status
    status: Mapped[SubscriptionStatus] = mapped_column(
        Enum(SubscriptionStatus), default=SubscriptionStatus.TRIALING, server_default="trialing"
    )

    # Billing period
    billing_period: Mapped[BillingPeriod] = mapped_column(
        Enum(BillingPeriod), default=BillingPeriod.MONTHLY, server_default="monthly"
    )

    # Dates
    trial_start: Mapped[date | None] = mapped_column(Date)
    trial_end: Mapped[date | None] = mapped_column(Date)
    current_period_start: Mapped[date] = mapped_column(Date, nullable=False)
    current_period_end: Mapped[date] = mapped_column(Date, nullable=False)
    canceled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancel_at_period_end: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")

    # External payment reference
    external_subscription_id: Mapped[str | None] = mapped_column(String(255))
    # e.g., Stripe subscription ID

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="subscription")
    plan: Mapped["Plan"] = relationship("Plan", back_populates="subscriptions")
    invoices: Mapped[list["Invoice"]] = relationship(
        "Invoice", back_populates="subscription", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Subscription {self.tenant_id} [{self.status.value}]>"


class InvoiceStatus(str, enum.Enum):
    """Invoice status."""

    DRAFT = "draft"
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    VOID = "void"
    REFUNDED = "refunded"


class Invoice(BaseModel):
    """Invoice for subscription billing."""

    __tablename__ = "invoices"

    subscription_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("subscriptions.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Invoice number
    number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)

    # Status
    status: Mapped[InvoiceStatus] = mapped_column(
        Enum(InvoiceStatus), default=InvoiceStatus.PENDING, server_default="pending"
    )

    # Amounts
    subtotal: Mapped[int] = mapped_column(Integer, nullable=False)  # in kopeks/cents
    tax: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    discount: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    total: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="RUB", server_default="RUB")

    # Period
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)

    # Line items
    items: Mapped[list] = mapped_column(JSONB, default=list, server_default="[]")
    # [{description: str, quantity: int, unit_price: int, total: int}]

    # Dates
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Payment info
    payment_method: Mapped[str | None] = mapped_column(String(50))
    payment_reference: Mapped[str | None] = mapped_column(String(255))

    # PDF
    pdf_url: Mapped[str | None] = mapped_column(String(500))

    # Relationships
    subscription: Mapped["Subscription"] = relationship("Subscription", back_populates="invoices")

    def __repr__(self) -> str:
        return f"<Invoice {self.number}>"


class UsageType(str, enum.Enum):
    """Usage record type."""

    CONVERSATIONS = "conversations"
    MESSAGES = "messages"
    AI_REQUESTS = "ai_requests"
    STORAGE = "storage"
    API_CALLS = "api_calls"


class UsageRecord(BaseModel):
    """Usage tracking for metered billing."""

    __tablename__ = "usage_records"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Period
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)

    # Usage type and value
    usage_type: Mapped[UsageType] = mapped_column(Enum(UsageType), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)

    # Limit for this type
    limit: Mapped[int | None] = mapped_column(Integer)

    # Metadata
    metadata: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")

    def __repr__(self) -> str:
        return f"<UsageRecord {self.usage_type.value}: {self.quantity}>"


class PaymentMethodType(str, enum.Enum):
    """Payment method type."""

    CARD = "card"
    BANK_TRANSFER = "bank_transfer"
    INVOICE = "invoice"


class PaymentMethod(BaseModel):
    """Payment method for tenant."""

    __tablename__ = "payment_methods"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Type
    type: Mapped[PaymentMethodType] = mapped_column(Enum(PaymentMethodType), nullable=False)

    # Card info (masked)
    card_brand: Mapped[str | None] = mapped_column(String(50))
    card_last4: Mapped[str | None] = mapped_column(String(4))
    card_exp_month: Mapped[int | None] = mapped_column(Integer)
    card_exp_year: Mapped[int | None] = mapped_column(Integer)

    # Bank info
    bank_name: Mapped[str | None] = mapped_column(String(255))

    # External reference
    external_id: Mapped[str | None] = mapped_column(String(255))

    # Status
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    def __repr__(self) -> str:
        if self.type == PaymentMethodType.CARD:
            return f"<PaymentMethod {self.card_brand} ****{self.card_last4}>"
        return f"<PaymentMethod {self.type.value}>"
