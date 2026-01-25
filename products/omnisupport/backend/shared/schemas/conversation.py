"""Conversation and Message schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import Field

from shared.models.conversation import (
    ChannelType,
    ContentType,
    ConversationPriority,
    ConversationStatus,
    SenderType,
)
from shared.schemas.base import BaseSchema, PaginatedResponse


class ConversationBase(BaseSchema):
    """Base conversation schema."""

    channel: ChannelType
    subject: str | None = Field(default=None, max_length=500)
    tags: list[str] = []


class ConversationCreate(ConversationBase):
    """Create conversation schema."""

    customer_id: UUID
    assigned_to: UUID | None = None
    priority: ConversationPriority = ConversationPriority.NORMAL
    metadata: dict = {}


class ConversationUpdate(BaseSchema):
    """Update conversation schema."""

    subject: str | None = Field(default=None, max_length=500)
    tags: list[str] | None = None
    priority: ConversationPriority | None = None
    metadata: dict | None = None


class CustomerBriefResponse(BaseSchema):
    """Brief customer info for conversation."""

    id: UUID
    name: str | None
    email: str | None
    phone: str | None
    avatar_url: str | None
    display_name: str


class UserBriefResponse(BaseSchema):
    """Brief user info for conversation."""

    id: UUID
    email: str
    first_name: str | None
    last_name: str | None
    avatar_url: str | None
    full_name: str
    status: str


class ConversationResponse(ConversationBase):
    """Conversation response schema."""

    id: UUID
    tenant_id: UUID
    customer_id: UUID
    assigned_to: UUID | None
    status: ConversationStatus
    priority: ConversationPriority
    channel_conversation_id: str | None
    messages_count: int
    first_response_at: datetime | None
    resolved_at: datetime | None
    closed_at: datetime | None
    last_message_at: datetime | None
    last_message_preview: str | None
    rating: int | None
    rating_comment: str | None
    metadata: dict
    created_at: datetime
    updated_at: datetime

    # Related
    customer: CustomerBriefResponse | None = None
    assigned_to_user: UserBriefResponse | None = None


class ConversationListResponse(PaginatedResponse[ConversationResponse]):
    """Paginated conversation list response."""

    pass


class MessageContent(BaseSchema):
    """Message content structure."""

    text: str | None = None
    url: str | None = None
    filename: str | None = None
    caption: str | None = None
    # ... other content fields


class MessageCreate(BaseSchema):
    """Create message schema."""

    content_type: ContentType = ContentType.TEXT
    content: dict
    is_internal: bool = False
    reply_to_id: UUID | None = None


class MessageResponse(BaseSchema):
    """Message response schema."""

    id: UUID
    conversation_id: UUID
    sender_type: SenderType
    sender_id: UUID | None
    channel_message_id: str | None
    content_type: ContentType
    content: dict
    metadata: dict
    is_read: bool
    read_at: datetime | None
    is_ai_generated: bool
    ai_confidence: float | None
    is_internal: bool
    reply_to_id: UUID | None
    created_at: datetime

    # Sender info (populated for operators)
    sender_name: str | None = None
    sender_avatar: str | None = None


class MessageListResponse(PaginatedResponse[MessageResponse]):
    """Paginated message list response."""

    pass


class AssignConversationRequest(BaseSchema):
    """Assign conversation request."""

    operator_id: UUID


class TransferConversationRequest(BaseSchema):
    """Transfer conversation request."""

    operator_id: UUID
    note: str | None = Field(default=None, max_length=1000)


class ResolveConversationRequest(BaseSchema):
    """Resolve conversation request."""

    resolution_note: str | None = Field(default=None, max_length=2000)


class RateConversationRequest(BaseSchema):
    """Rate conversation request."""

    rating: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=1000)


class ConversationFilters(BaseSchema):
    """Conversation list filters."""

    status: list[ConversationStatus] | None = None
    channel: list[ChannelType] | None = None
    assigned_to: UUID | None = None
    unassigned: bool | None = None
    customer_id: UUID | None = None
    tags: list[str] | None = None
    priority: list[ConversationPriority] | None = None
    search: str | None = Field(default=None, max_length=255)
    date_from: datetime | None = None
    date_to: datetime | None = None
