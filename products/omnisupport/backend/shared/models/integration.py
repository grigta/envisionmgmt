"""Integration, Webhook, and API Key models."""

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.models.base import BaseModel

if TYPE_CHECKING:
    from shared.models.tenant import Tenant


class IntegrationType(str, enum.Enum):
    """Integration type."""

    CRM = "crm"
    HELPDESK = "helpdesk"
    ANALYTICS = "analytics"
    PAYMENT = "payment"
    NOTIFICATION = "notification"
    CUSTOM = "custom"


class IntegrationStatus(str, enum.Enum):
    """Integration status."""

    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    PENDING = "pending"


class Integration(BaseModel):
    """External integration configuration."""

    __tablename__ = "integrations"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Type and name
    type: Mapped[IntegrationType] = mapped_column(Enum(IntegrationType), nullable=False)
    provider: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., "bitrix24", "amocrm"
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Status
    status: Mapped[IntegrationStatus] = mapped_column(
        Enum(IntegrationStatus), default=IntegrationStatus.PENDING, server_default="pending"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    # Credentials (encrypted in production)
    credentials: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")

    # Settings and mapping
    settings: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")
    field_mapping: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")

    # Error info
    last_error: Mapped[str | None] = mapped_column(Text)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (UniqueConstraint("tenant_id", "provider", "name", name="uq_integration_tenant_provider_name"),)

    def __repr__(self) -> str:
        return f"<Integration {self.provider}:{self.name}>"


class WebhookEvent(str, enum.Enum):
    """Webhook event types."""

    CONVERSATION_CREATED = "conversation.created"
    CONVERSATION_ASSIGNED = "conversation.assigned"
    CONVERSATION_RESOLVED = "conversation.resolved"
    CONVERSATION_CLOSED = "conversation.closed"
    MESSAGE_RECEIVED = "message.received"
    MESSAGE_SENT = "message.sent"
    CUSTOMER_CREATED = "customer.created"
    CUSTOMER_UPDATED = "customer.updated"
    RATING_RECEIVED = "rating.received"


class Webhook(BaseModel):
    """Outgoing webhook configuration."""

    __tablename__ = "webhooks"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )

    # Basic info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    # Events to trigger
    events: Mapped[list] = mapped_column(ARRAY(String), nullable=False)

    # Authentication
    secret: Mapped[str | None] = mapped_column(String(255))  # For signature verification
    headers: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")

    # Settings
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    retry_count: Mapped[int] = mapped_column(Integer, default=3, server_default="3")
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=30, server_default="30")

    # Stats
    total_deliveries: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    successful_deliveries: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    failed_deliveries: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    # Relationships
    deliveries: Mapped[list["WebhookDelivery"]] = relationship(
        "WebhookDelivery", back_populates="webhook", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Webhook {self.name}>"


class WebhookDeliveryStatus(str, enum.Enum):
    """Webhook delivery status."""

    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"


class WebhookDelivery(BaseModel):
    """Webhook delivery log."""

    __tablename__ = "webhook_deliveries"

    webhook_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("webhooks.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Event info
    event: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # Delivery status
    status: Mapped[WebhookDeliveryStatus] = mapped_column(
        Enum(WebhookDeliveryStatus), default=WebhookDeliveryStatus.PENDING, server_default="pending"
    )
    attempts: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    # Response info
    response_status: Mapped[int | None] = mapped_column(Integer)
    response_body: Mapped[str | None] = mapped_column(Text)
    error_message: Mapped[str | None] = mapped_column(Text)

    # Timing
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    next_retry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships
    webhook: Mapped["Webhook"] = relationship("Webhook", back_populates="deliveries")

    def __repr__(self) -> str:
        return f"<WebhookDelivery {self.id} [{self.status.value}]>"


class ApiKey(BaseModel):
    """API key for external access."""

    __tablename__ = "api_keys"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )

    # Key info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    key_prefix: Mapped[str] = mapped_column(String(10), nullable=False)  # First 8 chars for identification
    key_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    # Permissions
    permissions: Mapped[list] = mapped_column(ARRAY(String), default=list, server_default="{}")
    # e.g., ["conversations:read", "messages:write"]

    # Restrictions
    allowed_ips: Mapped[list] = mapped_column(ARRAY(String), default=list, server_default="{}")
    rate_limit: Mapped[int] = mapped_column(Integer, default=1000, server_default="1000")  # per minute

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Stats
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    usage_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    __table_args__ = (UniqueConstraint("tenant_id", "name", name="uq_api_key_tenant_name"),)

    def __repr__(self) -> str:
        return f"<ApiKey {self.key_prefix}...>"
