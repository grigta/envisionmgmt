"""Customer model - end users who contact support."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.models.base import BaseModel

if TYPE_CHECKING:
    from shared.models.tenant import Tenant
    from shared.models.conversation import Conversation
    from shared.models.user import User


class Customer(BaseModel):
    """Customer model - end users contacting support."""

    __tablename__ = "customers"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Contact info
    email: Mapped[str | None] = mapped_column(String(255), index=True)
    phone: Mapped[str | None] = mapped_column(String(50), index=True)
    name: Mapped[str | None] = mapped_column(String(255))
    avatar_url: Mapped[str | None] = mapped_column(String(500))

    # Additional info
    company: Mapped[str | None] = mapped_column(String(255))
    position: Mapped[str | None] = mapped_column(String(255))
    location: Mapped[str | None] = mapped_column(String(255))
    timezone: Mapped[str | None] = mapped_column(String(50))

    # Tags for segmentation
    tags: Mapped[list] = mapped_column(ARRAY(String), default=list, server_default="{}")

    # Custom fields
    metadata: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")
    custom_fields: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")

    # Stats
    first_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    conversations_count: Mapped[int] = mapped_column(default=0, server_default="0")

    # Preferred channel
    preferred_channel: Mapped[str | None] = mapped_column(String(50))

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="customers")
    identities: Mapped[list["CustomerIdentity"]] = relationship(
        "CustomerIdentity", back_populates="customer", cascade="all, delete-orphan"
    )
    conversations: Mapped[list["Conversation"]] = relationship(
        "Conversation", back_populates="customer", cascade="all, delete-orphan"
    )
    notes: Mapped[list["CustomerNote"]] = relationship(
        "CustomerNote", back_populates="customer", cascade="all, delete-orphan"
    )

    @property
    def display_name(self) -> str:
        """Get display name for customer."""
        if self.name:
            return self.name
        if self.email:
            return self.email
        if self.phone:
            return self.phone
        return "Неизвестный"

    def __repr__(self) -> str:
        return f"<Customer {self.display_name}>"


class CustomerIdentity(BaseModel):
    """Customer identity in a specific channel."""

    __tablename__ = "customer_identities"

    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False
    )

    # Channel info
    channel: Mapped[str] = mapped_column(String(50), nullable=False)  # telegram, whatsapp, web
    channel_user_id: Mapped[str] = mapped_column(String(255), nullable=False)

    # Channel-specific profile data
    channel_username: Mapped[str | None] = mapped_column(String(255))
    channel_name: Mapped[str | None] = mapped_column(String(255))
    channel_avatar_url: Mapped[str | None] = mapped_column(String(500))

    # Additional metadata
    metadata: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")

    # Relationships
    customer: Mapped["Customer"] = relationship("Customer", back_populates="identities")

    __table_args__ = (
        UniqueConstraint("channel", "channel_user_id", name="uq_customer_identity_channel"),
    )

    def __repr__(self) -> str:
        return f"<CustomerIdentity {self.channel}:{self.channel_user_id}>"


class CustomerNote(BaseModel):
    """Internal notes about customer."""

    __tablename__ = "customer_notes"

    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False
    )
    author_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )

    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Relationships
    customer: Mapped["Customer"] = relationship("Customer", back_populates="notes")
    author: Mapped["User | None"] = relationship("User")

    def __repr__(self) -> str:
        return f"<CustomerNote {self.id}>"


class CustomerTag(BaseModel):
    """Predefined customer tags."""

    __tablename__ = "customer_tags"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    color: Mapped[str | None] = mapped_column(String(7))
    description: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (UniqueConstraint("tenant_id", "name", name="uq_customer_tag_tenant_name"),)

    def __repr__(self) -> str:
        return f"<CustomerTag {self.name}>"
