"""Attachment schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import Field

from shared.schemas.base import BaseSchema, IDSchema, TimestampSchema


class AttachmentBase(BaseSchema):
    """Base attachment schema."""

    filename: str
    original_filename: str
    mime_type: str
    size: int = Field(description="File size in bytes")
    attachment_type: str


class AttachmentCreate(BaseSchema):
    """Schema for creating attachment (used internally)."""

    filename: str
    original_filename: str
    mime_type: str
    size: int
    storage_key: str
    checksum: str | None = None


class AttachmentResponse(IDSchema, TimestampSchema, AttachmentBase):
    """Attachment response schema."""

    url: str | None = Field(description="Pre-signed URL for file access")
    thumbnail_url: str | None = None
    width: int | None = None
    height: int | None = None
    status: str


class AttachmentUploadResponse(BaseSchema):
    """Response after successful upload."""

    id: UUID
    filename: str
    original_filename: str
    mime_type: str
    size: int
    url: str
    attachment_type: str


class AttachmentListResponse(BaseSchema):
    """Response for batch upload."""

    attachments: list[AttachmentUploadResponse]
    failed: list[dict] = Field(default_factory=list, description="Failed uploads with error messages")
