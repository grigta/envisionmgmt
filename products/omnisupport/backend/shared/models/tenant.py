"""Tenant model - SaaS clients (companies)."""

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.models.base import BaseModel

if TYPE_CHECKING:
    from shared.models.user import User
    from shared.models.customer import Customer
    from shared.models.conversation import Conversation
    from shared.models.channel import Channel
    from shared.models.scenario import Scenario
    from shared.models.knowledge import KnowledgeDocument
    from shared.models.billing import Subscription


class Tenant(BaseModel):
    """SaaS tenant (company) model."""

    __tablename__ = "tenants"

    # Basic info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    domain: Mapped[str | None] = mapped_column(String(255), unique=True)

    # Contact
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(50))
    website: Mapped[str | None] = mapped_column(String(500))

    # Settings
    settings: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")
    branding: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")

    # Business hours (JSON with timezone, days, hours)
    business_hours: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")

    # Notification settings
    notification_settings: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")

    # Notes (internal)
    notes: Mapped[str | None] = mapped_column(Text)

    # Relationships
    users: Mapped[list["User"]] = relationship(
        "User", back_populates="tenant", cascade="all, delete-orphan"
    )
    customers: Mapped[list["Customer"]] = relationship(
        "Customer", back_populates="tenant", cascade="all, delete-orphan"
    )
    conversations: Mapped[list["Conversation"]] = relationship(
        "Conversation", back_populates="tenant", cascade="all, delete-orphan"
    )
    channels: Mapped[list["Channel"]] = relationship(
        "Channel", back_populates="tenant", cascade="all, delete-orphan"
    )
    scenarios: Mapped[list["Scenario"]] = relationship(
        "Scenario", back_populates="tenant", cascade="all, delete-orphan"
    )
    knowledge_documents: Mapped[list["KnowledgeDocument"]] = relationship(
        "KnowledgeDocument", back_populates="tenant", cascade="all, delete-orphan"
    )
    subscription: Mapped["Subscription | None"] = relationship(
        "Subscription", back_populates="tenant", uselist=False
    )

    def __repr__(self) -> str:
        return f"<Tenant {self.slug}>"
