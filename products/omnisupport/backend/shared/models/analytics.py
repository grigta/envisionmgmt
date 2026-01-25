"""Analytics models."""

import enum
import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from shared.models.base import BaseModel

if TYPE_CHECKING:
    from shared.models.tenant import Tenant


class SnapshotPeriod(str, enum.Enum):
    """Analytics snapshot period."""

    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class AnalyticsSnapshot(BaseModel):
    """Aggregated analytics snapshot."""

    __tablename__ = "analytics_snapshots"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Period
    period: Mapped[SnapshotPeriod] = mapped_column(Enum(SnapshotPeriod), nullable=False)
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Conversation metrics
    conversations_total: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    conversations_new: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    conversations_resolved: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    conversations_closed: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    # Message metrics
    messages_total: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    messages_inbound: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    messages_outbound: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    # Response time metrics (in seconds)
    avg_first_response_time: Mapped[int | None] = mapped_column(Integer)
    avg_resolution_time: Mapped[int | None] = mapped_column(Integer)
    median_first_response_time: Mapped[int | None] = mapped_column(Integer)
    median_resolution_time: Mapped[int | None] = mapped_column(Integer)

    # Customer metrics
    customers_active: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    customers_new: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    # CSAT metrics
    csat_responses: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    csat_score_avg: Mapped[float | None] = mapped_column()
    csat_score_distribution: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")
    # e.g., {1: 5, 2: 10, 3: 20, 4: 40, 5: 25}

    # Channel breakdown
    channel_metrics: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")
    # e.g., {"telegram": {conversations: 100, messages: 500}, "web": {...}}

    # Operator metrics
    operator_metrics: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")
    # e.g., {"user_id": {conversations: 50, avg_response_time: 120}}

    # AI metrics
    ai_suggestions_total: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    ai_suggestions_accepted: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    ai_suggestions_modified: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    # Tag breakdown
    tag_metrics: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")
    # e.g., {"billing": 50, "technical": 100}

    def __repr__(self) -> str:
        return f"<AnalyticsSnapshot {self.period.value} {self.period_start}>"


class ReportType(str, enum.Enum):
    """Report type."""

    OVERVIEW = "overview"
    CONVERSATIONS = "conversations"
    OPERATORS = "operators"
    CHANNELS = "channels"
    CSAT = "csat"
    AI = "ai"
    CUSTOM = "custom"


class ReportFormat(str, enum.Enum):
    """Report export format."""

    PDF = "pdf"
    EXCEL = "excel"
    CSV = "csv"


class Report(BaseModel):
    """Saved or generated report."""

    __tablename__ = "reports"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )

    # Basic info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    type: Mapped[ReportType] = mapped_column(Enum(ReportType), nullable=False)

    # Date range
    date_from: Mapped[date] = mapped_column(Date, nullable=False)
    date_to: Mapped[date] = mapped_column(Date, nullable=False)

    # Filters and configuration
    filters: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")
    # e.g., {channels: ["telegram"], operators: ["uuid1", "uuid2"]}

    config: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")
    # e.g., {metrics: ["conversations", "response_time"], groupBy: "day"}

    # Generated data
    data: Mapped[dict | None] = mapped_column(JSONB)

    # Export info
    export_format: Mapped[ReportFormat | None] = mapped_column(Enum(ReportFormat))
    export_url: Mapped[str | None] = mapped_column(String(500))
    exported_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Schedule (for recurring reports)
    is_scheduled: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    schedule_cron: Mapped[str | None] = mapped_column(String(100))
    schedule_recipients: Mapped[list] = mapped_column(JSONB, default=list, server_default="[]")
    # List of email addresses

    def __repr__(self) -> str:
        return f"<Report {self.name}>"
