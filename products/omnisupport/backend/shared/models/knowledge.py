"""Knowledge base models for RAG."""

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.models.base import BaseModel

if TYPE_CHECKING:
    from shared.models.tenant import Tenant


class DocumentSourceType(str, enum.Enum):
    """Document source type."""

    FILE = "file"
    URL = "url"
    TEXT = "text"
    HISTORY = "history"


class DocumentStatus(str, enum.Enum):
    """Document processing status."""

    PENDING = "pending"
    PROCESSING = "processing"
    INDEXED = "indexed"
    FAILED = "failed"


class KnowledgeDocument(BaseModel):
    """Knowledge base document."""

    __tablename__ = "knowledge_documents"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )

    # Source info
    source_type: Mapped[DocumentSourceType] = mapped_column(Enum(DocumentSourceType), nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(1000))
    file_path: Mapped[str | None] = mapped_column(String(500))
    file_name: Mapped[str | None] = mapped_column(String(255))
    file_size: Mapped[int | None] = mapped_column(Integer)
    mime_type: Mapped[str | None] = mapped_column(String(100))

    # Content
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    content: Mapped[str | None] = mapped_column(Text)  # Raw text content
    content_hash: Mapped[str | None] = mapped_column(String(64))  # SHA-256 for dedup

    # Processing status
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus), default=DocumentStatus.PENDING, server_default="pending", index=True
    )
    error_message: Mapped[str | None] = mapped_column(Text)

    # Indexing info
    indexed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    chunks_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    # Metadata
    metadata: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")
    tags: Mapped[list] = mapped_column(JSONB, default=list, server_default="[]")

    # Settings
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="knowledge_documents")
    chunks: Mapped[list["KnowledgeChunk"]] = relationship(
        "KnowledgeChunk", back_populates="document", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<KnowledgeDocument {self.title}>"


class KnowledgeChunk(BaseModel):
    """Knowledge document chunk for RAG."""

    __tablename__ = "knowledge_chunks"

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Chunk info
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    # Token count
    tokens_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    # Vector embedding reference (stored in Qdrant)
    vector_id: Mapped[str | None] = mapped_column(String(100))

    # Metadata for retrieval
    metadata: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")
    # e.g., {heading: "FAQ", page: 5, section: "Возвраты"}

    # Relationships
    document: Mapped["KnowledgeDocument"] = relationship("KnowledgeDocument", back_populates="chunks")

    __table_args__ = (
        UniqueConstraint("document_id", "chunk_index", name="uq_knowledge_chunk_document_index"),
    )

    def __repr__(self) -> str:
        return f"<KnowledgeChunk {self.document_id}:{self.chunk_index}>"


class CrawlerStatus(str, enum.Enum):
    """Crawler status."""

    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"


class CrawlerConfig(BaseModel):
    """Website crawler configuration."""

    __tablename__ = "crawler_configs"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )

    # Basic info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    # URL settings
    start_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    allowed_domains: Mapped[list] = mapped_column(JSONB, default=list, server_default="[]")
    url_patterns: Mapped[list] = mapped_column(JSONB, default=list, server_default="[]")
    # e.g., ["/faq/*", "/help/*"]

    exclude_patterns: Mapped[list] = mapped_column(JSONB, default=list, server_default="[]")
    # e.g., ["/admin/*", "*.pdf"]

    # Crawl settings
    max_depth: Mapped[int] = mapped_column(Integer, default=3, server_default="3")
    max_pages: Mapped[int] = mapped_column(Integer, default=100, server_default="100")
    delay_seconds: Mapped[float] = mapped_column(Float, default=1.0, server_default="1.0")

    # Content extraction
    content_selectors: Mapped[list] = mapped_column(JSONB, default=list, server_default="[]")
    # CSS selectors for content extraction, e.g., ["article", ".content", "#main"]

    exclude_selectors: Mapped[list] = mapped_column(JSONB, default=list, server_default="[]")
    # e.g., [".sidebar", "nav", "footer"]

    # Schedule
    schedule_enabled: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    schedule_cron: Mapped[str | None] = mapped_column(String(100))
    # e.g., "0 0 * * 0" for weekly on Sunday

    # Status
    status: Mapped[CrawlerStatus] = mapped_column(
        Enum(CrawlerStatus), default=CrawlerStatus.IDLE, server_default="idle"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    # Last run info
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_run_pages: Mapped[int | None] = mapped_column(Integer)
    last_run_error: Mapped[str | None] = mapped_column(Text)
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (UniqueConstraint("tenant_id", "name", name="uq_crawler_config_tenant_name"),)

    def __repr__(self) -> str:
        return f"<CrawlerConfig {self.name}>"
