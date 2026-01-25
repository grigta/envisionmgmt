"""Scenario and Trigger models for no-code automation."""

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.models.base import BaseModel

if TYPE_CHECKING:
    from shared.models.tenant import Tenant


class ScenarioStatus(str, enum.Enum):
    """Scenario status."""

    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class ExecutionStatus(str, enum.Enum):
    """Scenario execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Scenario(BaseModel):
    """No-code scenario for automation."""

    __tablename__ = "scenarios"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )

    # Basic info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    icon: Mapped[str | None] = mapped_column(String(50))
    color: Mapped[str | None] = mapped_column(String(7))

    # Status
    status: Mapped[ScenarioStatus] = mapped_column(
        Enum(ScenarioStatus), default=ScenarioStatus.DRAFT, server_default="draft"
    )
    is_template: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")

    # Industry template category
    template_category: Mapped[str | None] = mapped_column(String(100))
    # e.g., "ecommerce", "saas", "finance", "realestate"

    # Nodes (array of node definitions)
    nodes: Mapped[list] = mapped_column(JSONB, nullable=False, default=list, server_default="[]")
    # Structure: [{id, type, position, data: {config}}]

    # Edges (connections between nodes)
    edges: Mapped[list] = mapped_column(JSONB, nullable=False, default=list, server_default="[]")
    # Structure: [{id, source, target, sourceHandle}]

    # Variables (key-value defaults)
    variables: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")

    # Active flag (separate from status for quick filtering)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")

    # Version control
    version: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    published_version: Mapped[int | None] = mapped_column(Integer)

    # Stats
    executions_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    successful_executions: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="scenarios")
    triggers: Mapped[list["Trigger"]] = relationship(
        "Trigger", back_populates="scenario", cascade="all, delete-orphan"
    )
    variable_definitions: Mapped[list["ScenarioVariable"]] = relationship(
        "ScenarioVariable", back_populates="scenario", cascade="all, delete-orphan"
    )
    executions: Mapped[list["ScenarioExecution"]] = relationship(
        "ScenarioExecution", back_populates="scenario", cascade="all, delete-orphan"
    )

    __table_args__ = (UniqueConstraint("tenant_id", "name", name="uq_scenario_tenant_name"),)

    def __repr__(self) -> str:
        return f"<Scenario {self.name}>"


class TriggerType(str, enum.Enum):
    """Trigger type."""

    NEW_CONVERSATION = "new_conversation"
    MESSAGE_RECEIVED = "message_received"
    KEYWORD = "keyword"
    SCHEDULE = "schedule"
    WEBHOOK = "webhook"
    EVENT = "event"
    MANUAL = "manual"


class Trigger(BaseModel):
    """Scenario trigger."""

    __tablename__ = "triggers"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    scenario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Type and name
    type: Mapped[TriggerType] = mapped_column(Enum(TriggerType), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Event type for event-based triggers
    event_type: Mapped[str | None] = mapped_column(String(100), index=True)
    # e.g., "conversation.created", "message.received"

    # Conditions for trigger (all must match)
    conditions: Mapped[list] = mapped_column(JSONB, nullable=False, default=list, server_default="[]")
    # [{field: str, operator: str, value: any}]

    # Logic for combining conditions
    condition_logic: Mapped[str] = mapped_column(String(10), default="and", server_default="and")
    # "and" or "or"

    # Configuration (legacy + extra config)
    config: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")

    # Filters
    channel_filter: Mapped[list] = mapped_column(ARRAY(String), default=list, server_default="{}")

    # Priority (higher = checked first)
    priority: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    # Relationships
    scenario: Mapped["Scenario"] = relationship("Scenario", back_populates="triggers")

    def __repr__(self) -> str:
        return f"<Trigger {self.type.value}:{self.name}>"


class ScenarioExecution(BaseModel):
    """Scenario execution record."""

    __tablename__ = "scenario_executions"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    scenario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Status
    status: Mapped[ExecutionStatus] = mapped_column(
        Enum(ExecutionStatus), default=ExecutionStatus.PENDING, server_default="pending"
    )

    # Trigger info
    trigger_event: Mapped[str | None] = mapped_column(String(100))
    trigger_data: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")

    # Timing
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Result
    result: Mapped[dict | None] = mapped_column(JSONB)
    error_message: Mapped[str | None] = mapped_column(Text)

    # Execution log
    execution_log: Mapped[dict | None] = mapped_column(JSONB)
    # {visited_nodes: [], final_variables: {}}

    # Relationships
    scenario: Mapped["Scenario"] = relationship("Scenario", back_populates="executions")

    def __repr__(self) -> str:
        return f"<ScenarioExecution {self.id} [{self.status.value}]>"


class ScenarioVariable(BaseModel):
    """Scenario variable definition."""

    __tablename__ = "scenario_variables"

    scenario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Variable info
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    # Type
    var_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # e.g., "string", "number", "boolean", "date", "array", "object"

    # Default value
    default_value: Mapped[dict | None] = mapped_column(JSONB)
    # Stored as {value: ...}

    # Validation
    required: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    validation: Mapped[dict | None] = mapped_column(JSONB)
    # e.g., {min: 0, max: 100} for numbers, {pattern: "^[A-Z]+"} for strings

    # Relationships
    scenario: Mapped["Scenario"] = relationship("Scenario", back_populates="variables")

    __table_args__ = (UniqueConstraint("scenario_id", "name", name="uq_scenario_variable_name"),)

    def __repr__(self) -> str:
        return f"<ScenarioVariable {self.name}>"
