"""Attachment model for uploaded files."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from shared.models.base import BaseModel


class AttachmentType(str, enum.Enum):
    """Attachment type."""

    IMAGE = "image"
    DOCUMENT = "document"
    AUDIO = "audio"
    VIDEO = "video"


class AttachmentStatus(str, enum.Enum):
    """Attachment status."""

    PENDING = "pending"  # Uploaded but not yet attached to message
    ATTACHED = "attached"  # Attached to a message
    ORPHANED = "orphaned"  # Not attached, marked for cleanup
    DELETED = "deleted"  # Soft deleted


class Attachment(BaseModel):
    """Uploaded file attachment."""

    __tablename__ = "attachments"

    # Owner
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    uploaded_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), index=True
    )

    # Message relationship (nullable - file may be uploaded before message is sent)
    message_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("messages.id", ondelete="SET NULL"), index=True
    )
    conversation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="SET NULL"), index=True
    )

    # File info
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(255), nullable=False)
    size: Mapped[int] = mapped_column(Integer, nullable=False)  # in bytes

    # Storage
    storage_key: Mapped[str] = mapped_column(String(1000), nullable=False, unique=True)
    storage_url: Mapped[str | None] = mapped_column(Text)  # Cached URL (regenerated on access)
    checksum: Mapped[str | None] = mapped_column(String(64))  # MD5 hash

    # Type classification
    attachment_type: Mapped[AttachmentType] = mapped_column(
        Enum(AttachmentType), nullable=False
    )

    # Image-specific
    width: Mapped[int | None] = mapped_column(Integer)
    height: Mapped[int | None] = mapped_column(Integer)
    thumbnail_key: Mapped[str | None] = mapped_column(String(1000))

    # Status
    status: Mapped[AttachmentStatus] = mapped_column(
        Enum(AttachmentStatus),
        default=AttachmentStatus.PENDING,
        server_default="pending",
        index=True,
    )

    # Timestamps
    attached_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))  # For pending files

    # Soft delete
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    def __repr__(self) -> str:
        return f"<Attachment {self.filename} ({self.attachment_type.value})>"

    @classmethod
    def determine_type(cls, mime_type: str) -> AttachmentType:
        """Determine attachment type from MIME type."""
        if mime_type.startswith("image/"):
            return AttachmentType.IMAGE
        elif mime_type.startswith("audio/"):
            return AttachmentType.AUDIO
        elif mime_type.startswith("video/"):
            return AttachmentType.VIDEO
        else:
            return AttachmentType.DOCUMENT
