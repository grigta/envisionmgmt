"""Conversation and Message models."""

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
    from shared.models.customer import Customer
    from shared.models.user import User


class ConversationStatus(str, enum.Enum):
    """Conversation status."""

    PENDING = "pending"
    ASSIGNED = "assigned"
    ACTIVE = "active"
    OPEN = "open"
    RESOLVED = "resolved"
    CLOSED = "closed"


class ConversationPriority(str, enum.Enum):
    """Conversation priority."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class ChannelType(str, enum.Enum):
    """Communication channel type."""

    TELEGRAM = "telegram"
    WHATSAPP = "whatsapp"
    WEB = "web"
    EMAIL = "email"
    API = "api"


class Conversation(BaseModel):
    """Conversation (dialog) model."""

    __tablename__ = "conversations"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    assigned_to_id: Mapped[uuid.UUID | None] = mapped_column(
        "assigned_to", UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    department_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id", ondelete="SET NULL"), index=True
    )

    # Channel
    channel: Mapped[ChannelType] = mapped_column(Enum(ChannelType), nullable=False)
    channel_conversation_id: Mapped[str | None] = mapped_column(String(255))

    # Status and priority
    status: Mapped[ConversationStatus] = mapped_column(
        Enum(ConversationStatus), default=ConversationStatus.OPEN, server_default="open", index=True
    )
    priority: Mapped[ConversationPriority] = mapped_column(
        Enum(ConversationPriority), default=ConversationPriority.NORMAL, server_default="normal"
    )

    # Subject/topic
    subject: Mapped[str | None] = mapped_column(String(500))

    # Tags
    tags: Mapped[list] = mapped_column(ARRAY(String), default=list, server_default="{}")

    # Required skills for routing
    required_skills: Mapped[list] = mapped_column(ARRAY(String), default=list, server_default="{}")

    # Assignment timestamp
    assigned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Metadata
    metadata: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")

    # Stats
    messages_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    first_response_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    first_response_time_seconds: Mapped[int | None] = mapped_column(Integer)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolution_time_seconds: Mapped[int | None] = mapped_column(Integer)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Last message preview
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    last_message_preview: Mapped[str | None] = mapped_column(String(500))

    # Rating / CSAT
    rating: Mapped[int | None] = mapped_column(Integer)  # 1-5
    csat_score: Mapped[int | None] = mapped_column(Integer)  # 1-5 (Customer Satisfaction)
    rating_comment: Mapped[str | None] = mapped_column(Text)

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="conversations")
    customer: Mapped["Customer"] = relationship("Customer", back_populates="conversations")
    assigned_to_user: Mapped["User | None"] = relationship(
        "User", back_populates="assigned_conversations", foreign_keys=[assigned_to_id]
    )
    messages: Mapped[list["Message"]] = relationship(
        "Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at"
    )

    def __repr__(self) -> str:
        return f"<Conversation {self.id} [{self.status.value}]>"


class SenderType(str, enum.Enum):
    """Message sender type."""

    CUSTOMER = "customer"
    OPERATOR = "operator"
    BOT = "bot"
    SYSTEM = "system"


class ContentType(str, enum.Enum):
    """Message content type."""

    TEXT = "text"
    IMAGE = "image"
    FILE = "file"
    AUDIO = "audio"
    VIDEO = "video"
    LOCATION = "location"
    CONTACT = "contact"
    STICKER = "sticker"


class Message(BaseModel):
    """Message model."""

    __tablename__ = "messages"

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Channel (denormalized for analytics)
    channel: Mapped[ChannelType | None] = mapped_column(Enum(ChannelType))

    # Sender
    sender_type: Mapped[SenderType] = mapped_column(Enum(SenderType), nullable=False)
    sender_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))

    # Channel reference
    channel_message_id: Mapped[str | None] = mapped_column(String(255))

    # Content
    content_type: Mapped[ContentType] = mapped_column(
        Enum(ContentType), default=ContentType.TEXT, server_default="text"
    )
    content: Mapped[dict] = mapped_column(JSONB, nullable=False)
    # Content structure:
    # text: {text: str}
    # image: {url: str, thumbnail_url: str, width: int, height: int, caption: str}
    # file: {url: str, filename: str, size: int, mime_type: str}
    # audio: {url: str, duration: int}
    # video: {url: str, thumbnail_url: str, duration: int}
    # location: {latitude: float, longitude: float, title: str}
    # contact: {name: str, phone: str, email: str}

    # Metadata
    metadata: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")

    # Status
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # AI-generated
    is_ai_generated: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    ai_confidence: Mapped[float | None] = mapped_column()

    # Internal note (not visible to customer)
    is_internal: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")

    # Reply to
    reply_to_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("messages.id", ondelete="SET NULL")
    )

    # Relationships
    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="messages")
    reply_to: Mapped["Message | None"] = relationship("Message", remote_side="Message.id")

    @property
    def text(self) -> str | None:
        """Get text content."""
        if self.content_type == ContentType.TEXT:
            return self.content.get("text")
        return None

    def __repr__(self) -> str:
        return f"<Message {self.id} [{self.sender_type.value}]>"


class CannedResponse(BaseModel):
    """Canned (template) response."""

    __tablename__ = "canned_responses"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )

    # Content
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    shortcut: Mapped[str | None] = mapped_column(String(50))  # e.g., "/hello"
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Categorization
    category: Mapped[str | None] = mapped_column(String(100))
    tags: Mapped[list] = mapped_column(ARRAY(String), default=list, server_default="{}")

    # Settings
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    is_shared: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    # Stats
    usage_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    __table_args__ = (
        UniqueConstraint("tenant_id", "shortcut", name="uq_canned_response_shortcut"),
    )

    def __repr__(self) -> str:
        return f"<CannedResponse {self.title}>"
