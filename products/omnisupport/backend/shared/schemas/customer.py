"""Customer schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import EmailStr, Field

from shared.schemas.base import BaseSchema, PaginatedResponse


class CustomerBase(BaseSchema):
    """Base customer schema."""

    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)
    name: str | None = Field(default=None, max_length=255)


class CustomerCreate(CustomerBase):
    """Create customer schema."""

    company: str | None = Field(default=None, max_length=255)
    position: str | None = Field(default=None, max_length=255)
    location: str | None = Field(default=None, max_length=255)
    timezone: str | None = Field(default=None, max_length=50)
    tags: list[str] = []
    custom_fields: dict = {}


class CustomerUpdate(BaseSchema):
    """Update customer schema."""

    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)
    name: str | None = Field(default=None, max_length=255)
    company: str | None = Field(default=None, max_length=255)
    position: str | None = Field(default=None, max_length=255)
    location: str | None = Field(default=None, max_length=255)
    timezone: str | None = Field(default=None, max_length=50)
    tags: list[str] | None = None
    custom_fields: dict | None = None


class CustomerIdentityResponse(BaseSchema):
    """Customer identity response."""

    id: UUID
    channel: str
    channel_user_id: str
    channel_username: str | None
    channel_name: str | None
    channel_avatar_url: str | None
    created_at: datetime


class CustomerResponse(CustomerBase):
    """Customer response schema."""

    id: UUID
    tenant_id: UUID
    avatar_url: str | None
    company: str | None
    position: str | None
    location: str | None
    timezone: str | None
    tags: list[str]
    custom_fields: dict
    preferred_channel: str | None
    first_seen_at: datetime | None
    last_seen_at: datetime | None
    conversations_count: int
    created_at: datetime
    updated_at: datetime

    # Computed
    display_name: str

    # Related
    identities: list[CustomerIdentityResponse] = []


class CustomerListResponse(PaginatedResponse[CustomerResponse]):
    """Paginated customer list response."""

    pass


class CustomerNoteCreate(BaseSchema):
    """Create customer note."""

    content: str = Field(min_length=1, max_length=5000)


class CustomerNoteResponse(BaseSchema):
    """Customer note response."""

    id: UUID
    content: str
    author_id: UUID | None
    author_name: str | None
    created_at: datetime


class CustomerMergeRequest(BaseSchema):
    """Merge customers request."""

    source_customer_ids: list[UUID] = Field(min_length=1, max_length=10)
    # Target customer is the one receiving the merge request


class CustomerExportRequest(BaseSchema):
    """Export customers request."""

    format: str = Field(pattern=r"^(csv|excel)$")
    filters: dict = {}
    columns: list[str] | None = None
