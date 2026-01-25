"""Channel and Widget settings models."""

import enum
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.models.base import BaseModel
from shared.models.conversation import ChannelType

if TYPE_CHECKING:
    from shared.models.tenant import Tenant


class ChannelStatus(str, enum.Enum):
    """Channel status."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    PENDING = "pending"


class Channel(BaseModel):
    """Channel configuration."""

    __tablename__ = "channels"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Type
    type: Mapped[ChannelType] = mapped_column(Enum(ChannelType), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Status
    status: Mapped[ChannelStatus] = mapped_column(
        Enum(ChannelStatus), default=ChannelStatus.PENDING, server_default="pending"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    # Credentials (encrypted in production)
    credentials: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")
    # Telegram: {bot_token, bot_username, webhook_secret}
    # WhatsApp: {api_key, phone_number_id, business_account_id}
    # Web: {widget_id}

    # Settings
    settings: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")

    # Stats
    messages_sent: Mapped[int] = mapped_column(default=0, server_default="0")
    messages_received: Mapped[int] = mapped_column(default=0, server_default="0")

    # Error info
    last_error: Mapped[str | None] = mapped_column(Text)

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="channels")
    widget_settings: Mapped["WidgetSettings | None"] = relationship(
        "WidgetSettings", back_populates="channel", uselist=False, cascade="all, delete-orphan"
    )

    __table_args__ = (UniqueConstraint("tenant_id", "type", "name", name="uq_channel_tenant_type_name"),)

    def __repr__(self) -> str:
        return f"<Channel {self.type.value}:{self.name}>"


class WidgetPosition(str, enum.Enum):
    """Widget position on page."""

    BOTTOM_RIGHT = "bottom_right"
    BOTTOM_LEFT = "bottom_left"
    TOP_RIGHT = "top_right"
    TOP_LEFT = "top_left"


class WidgetSettings(BaseModel):
    """Web widget settings."""

    __tablename__ = "widget_settings"

    channel_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("channels.id", ondelete="CASCADE"), nullable=False, unique=True
    )

    # Appearance
    primary_color: Mapped[str] = mapped_column(String(7), default="#6366f1", server_default="#6366f1")
    text_color: Mapped[str] = mapped_column(String(7), default="#ffffff", server_default="#ffffff")
    background_color: Mapped[str] = mapped_column(String(7), default="#ffffff", server_default="#ffffff")

    # Position and size
    position: Mapped[WidgetPosition] = mapped_column(
        Enum(WidgetPosition), default=WidgetPosition.BOTTOM_RIGHT, server_default="bottom_right"
    )
    offset_x: Mapped[int] = mapped_column(default=20, server_default="20")
    offset_y: Mapped[int] = mapped_column(default=20, server_default="20")

    # Branding
    logo_url: Mapped[str | None] = mapped_column(String(500))
    company_name: Mapped[str | None] = mapped_column(String(255))
    show_branding: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    # Messages
    welcome_message: Mapped[str | None] = mapped_column(Text)
    placeholder_text: Mapped[str] = mapped_column(String(255), default="Напишите сообщение...", server_default="Напишите сообщение...")
    offline_message: Mapped[str | None] = mapped_column(Text)

    # Behavior
    auto_open: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    auto_open_delay: Mapped[int] = mapped_column(default=5, server_default="5")  # seconds
    require_email: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    require_name: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    show_typing_indicator: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    # Pre-chat form
    prechat_form_enabled: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    prechat_form_fields: Mapped[list] = mapped_column(JSONB, default=list, server_default="[]")
    # [{name: str, label: str, type: str, required: bool}]

    # Allowed domains (empty = all)
    allowed_domains: Mapped[list] = mapped_column(JSONB, default=list, server_default="[]")

    # Relationships
    channel: Mapped["Channel"] = relationship("Channel", back_populates="widget_settings")

    def __repr__(self) -> str:
        return f"<WidgetSettings for channel {self.channel_id}>"
