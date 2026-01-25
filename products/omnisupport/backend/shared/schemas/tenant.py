"""Tenant schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import EmailStr, Field, HttpUrl

from shared.schemas.base import BaseSchema


class TenantBase(BaseSchema):
    """Base tenant schema."""

    name: str = Field(min_length=1, max_length=255)
    slug: str = Field(min_length=1, max_length=100, pattern=r"^[a-z0-9-]+$")


class TenantCreate(TenantBase):
    """Create tenant schema."""

    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)
    website: str | None = Field(default=None, max_length=500)


class TenantUpdate(BaseSchema):
    """Update tenant schema."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)
    website: str | None = Field(default=None, max_length=500)
    domain: str | None = Field(default=None, max_length=255)


class TenantResponse(TenantBase):
    """Tenant response schema."""

    id: UUID
    email: str | None
    phone: str | None
    website: str | None
    domain: str | None
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime

    # Settings (flattened)
    settings: dict
    branding: dict
    business_hours: dict


class TenantSettingsUpdate(BaseSchema):
    """Update tenant settings."""

    timezone: str | None = Field(default=None, max_length=50)
    language: str | None = Field(default=None, max_length=10)
    date_format: str | None = Field(default=None, max_length=20)
    time_format: str | None = Field(default=None, max_length=20)

    # Notifications
    email_notifications: bool | None = None
    browser_notifications: bool | None = None
    sound_notifications: bool | None = None

    # Routing
    routing_strategy: str | None = Field(default=None, pattern=r"^(round_robin|skill_based|manual)$")
    auto_assign: bool | None = None
    auto_close_hours: int | None = Field(default=None, ge=0, le=720)


class BusinessHoursUpdate(BaseSchema):
    """Update business hours."""

    timezone: str = Field(max_length=50)
    enabled: bool = True
    schedule: dict
    # Example schedule:
    # {
    #   "monday": {"start": "09:00", "end": "18:00", "enabled": true},
    #   "tuesday": {"start": "09:00", "end": "18:00", "enabled": true},
    #   ...
    # }
    holidays: list[str] = []  # List of dates in ISO format


class BrandingUpdate(BaseSchema):
    """Update branding settings."""

    logo_url: str | None = Field(default=None, max_length=500)
    favicon_url: str | None = Field(default=None, max_length=500)
    primary_color: str | None = Field(default=None, max_length=7, pattern=r"^#[0-9a-fA-F]{6}$")
    secondary_color: str | None = Field(default=None, max_length=7, pattern=r"^#[0-9a-fA-F]{6}$")
    company_name: str | None = Field(default=None, max_length=255)
    support_email: EmailStr | None = None
    support_phone: str | None = Field(default=None, max_length=50)


class NotificationSettingsUpdate(BaseSchema):
    """Update notification settings."""

    # Email notifications
    email_new_conversation: bool | None = None
    email_conversation_assigned: bool | None = None
    email_daily_summary: bool | None = None

    # Push notifications
    push_new_message: bool | None = None
    push_conversation_assigned: bool | None = None

    # Sound
    sound_enabled: bool | None = None
    sound_new_message: str | None = Field(default=None, max_length=50)
