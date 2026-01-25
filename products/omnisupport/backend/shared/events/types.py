"""Event types and models."""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class EventType(str, Enum):
    """Event types for pub/sub."""

    # Conversation events
    CONVERSATION_CREATED = "conversation.created"
    CONVERSATION_ASSIGNED = "conversation.assigned"
    CONVERSATION_TRANSFERRED = "conversation.transferred"
    CONVERSATION_RESOLVED = "conversation.resolved"
    CONVERSATION_CLOSED = "conversation.closed"
    CONVERSATION_REOPENED = "conversation.reopened"

    # Message events
    MESSAGE_RECEIVED = "message.received"
    MESSAGE_SENT = "message.sent"
    MESSAGE_READ = "message.read"

    # Typing events
    CUSTOMER_TYPING = "customer.typing"
    OPERATOR_TYPING = "operator.typing"

    # Customer events
    CUSTOMER_CREATED = "customer.created"
    CUSTOMER_UPDATED = "customer.updated"
    CUSTOMER_MERGED = "customer.merged"

    # Operator events
    OPERATOR_STATUS_CHANGED = "operator.status_changed"
    OPERATOR_CONNECTED = "operator.connected"
    OPERATOR_DISCONNECTED = "operator.disconnected"

    # AI events
    AI_SUGGESTION_READY = "ai.suggestion_ready"
    AI_SUMMARY_READY = "ai.summary_ready"

    # Knowledge events
    KNOWLEDGE_DOCUMENT_INDEXED = "knowledge.document_indexed"
    KNOWLEDGE_DOCUMENT_ERROR = "knowledge.document_error"

    # System events
    WEBHOOK_TRIGGERED = "webhook.triggered"
    SCENARIO_TRIGGERED = "scenario.triggered"


class Event(BaseModel):
    """Base event model."""

    type: EventType
    tenant_id: UUID
    timestamp: datetime
    data: dict[str, Any]

    # Optional metadata
    conversation_id: UUID | None = None
    customer_id: UUID | None = None
    user_id: UUID | None = None

    class Config:
        use_enum_values = True


class ConversationEvent(Event):
    """Conversation-related event."""

    conversation_id: UUID


class MessageEvent(Event):
    """Message-related event."""

    conversation_id: UUID
    message_id: UUID


class TypingEvent(Event):
    """Typing indicator event."""

    conversation_id: UUID
    is_typing: bool
