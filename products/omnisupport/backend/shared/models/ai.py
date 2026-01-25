"""AI interaction models."""

import enum
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import (
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.models.base import BaseModel

if TYPE_CHECKING:
    from shared.models.tenant import Tenant
    from shared.models.conversation import Conversation
    from shared.models.user import User


class InteractionType(str, enum.Enum):
    """AI interaction type."""

    SUGGESTION = "suggestion"
    SUMMARIZE = "summarize"
    SENTIMENT = "sentiment"
    RAG_QUERY = "rag_query"
    TRANSLATION = "translation"
    CLASSIFICATION = "classification"


class InteractionStatus(str, enum.Enum):
    """Interaction status."""

    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class InteractionFeedback(str, enum.Enum):
    """Feedback on AI interaction."""

    ACCEPTED = "accepted"
    MODIFIED = "modified"
    REJECTED = "rejected"


class AIInteraction(BaseModel):
    """AI interaction tracking for analytics and billing."""

    __tablename__ = "ai_interactions"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Context
    conversation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="SET NULL")
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )

    # Interaction details
    interaction_type: Mapped[str] = mapped_column(String(50), nullable=False)
    model: Mapped[str | None] = mapped_column(String(100))

    # Request/Response
    prompt: Mapped[str | None] = mapped_column(Text)
    response: Mapped[str | None] = mapped_column(Text)

    # Tokens & performance
    input_tokens: Mapped[int | None] = mapped_column(Integer)
    output_tokens: Mapped[int | None] = mapped_column(Integer)
    duration_ms: Mapped[int | None] = mapped_column(Integer)

    # Status
    status: Mapped[str] = mapped_column(String(50), default="completed", server_default="completed")

    # Feedback
    feedback: Mapped[str | None] = mapped_column(String(50))

    # Additional metadata
    metadata: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant")
    conversation: Mapped["Conversation | None"] = relationship("Conversation")
    user: Mapped["User | None"] = relationship("User")

    @property
    def total_tokens(self) -> int:
        """Total tokens used."""
        return (self.input_tokens or 0) + (self.output_tokens or 0)

    def __repr__(self) -> str:
        return f"<AIInteraction {self.interaction_type} [{self.status}]>"
