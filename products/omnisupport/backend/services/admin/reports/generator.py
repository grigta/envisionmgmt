"""Report generation service."""

import logging
from datetime import date, datetime, timezone
from uuid import UUID
from typing import Any

from sqlalchemy import select, func, and_, extract
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_session
from shared.models.analytics import Report, ReportType, ReportFormat, AnalyticsSnapshot, SnapshotPeriod
from shared.models.conversation import Conversation, Message, ConversationStatus
from shared.models.user import User
from shared.models.customer import Customer

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Service for generating report data."""

    async def generate_report_data(
        self,
        report_id: UUID,
    ) -> dict:
        """Generate data for a report."""
        async with get_session() as session:
            result = await session.execute(
                select(Report).where(Report.id == report_id)
            )
            report = result.scalar_one_or_none()

            if not report:
                raise ValueError(f"Report {report_id} not found")

            # Generate data based on report type
            if report.type == ReportType.OVERVIEW:
                data = await self._generate_overview_report(session, report)
            elif report.type == ReportType.CONVERSATIONS:
                data = await self._generate_conversations_report(session, report)
            elif report.type == ReportType.OPERATORS:
                data = await self._generate_operators_report(session, report)
            elif report.type == ReportType.CHANNELS:
                data = await self._generate_channels_report(session, report)
            elif report.type == ReportType.CSAT:
                data = await self._generate_csat_report(session, report)
            elif report.type == ReportType.AI:
                data = await self._generate_ai_report(session, report)
            else:
                data = await self._generate_custom_report(session, report)

            # Save report data
            report.data = data
            await session.commit()

            return data

    async def _generate_overview_report(
        self, session: AsyncSession, report: Report
    ) -> dict:
        """Generate overview report data."""
        tenant_id = report.tenant_id
        date_from = datetime.combine(report.date_from, datetime.min.time())
        date_to = datetime.combine(report.date_to, datetime.max.time())

        # Get snapshots for the period
        snapshots = await session.execute(
            select(AnalyticsSnapshot)
            .where(
                and_(
                    AnalyticsSnapshot.tenant_id == tenant_id,
                    AnalyticsSnapshot.period == SnapshotPeriod.DAILY,
                    AnalyticsSnapshot.period_start >= date_from,
                    AnalyticsSnapshot.period_start <= date_to,
                )
            )
            .order_by(AnalyticsSnapshot.period_start)
        )
        snapshot_list = list(snapshots.scalars().all())

        # Aggregate totals
        totals = {
            "conversations_total": sum(s.conversations_total for s in snapshot_list),
            "conversations_new": sum(s.conversations_new for s in snapshot_list),
            "conversations_resolved": sum(s.conversations_resolved for s in snapshot_list),
            "conversations_closed": sum(s.conversations_closed for s in snapshot_list),
            "messages_total": sum(s.messages_total for s in snapshot_list),
            "messages_inbound": sum(s.messages_inbound for s in snapshot_list),
            "messages_outbound": sum(s.messages_outbound for s in snapshot_list),
            "customers_new": sum(s.customers_new for s in snapshot_list),
            "customers_active": sum(s.customers_active for s in snapshot_list),
        }

        # Average response times
        frt_values = [s.avg_first_response_time for s in snapshot_list if s.avg_first_response_time]
        resolution_values = [s.avg_resolution_time for s in snapshot_list if s.avg_resolution_time]

        totals["avg_first_response_time"] = (
            sum(frt_values) / len(frt_values) if frt_values else None
        )
        totals["avg_resolution_time"] = (
            sum(resolution_values) / len(resolution_values) if resolution_values else None
        )

        # CSAT
        csat_values = [s.csat_score_avg for s in snapshot_list if s.csat_score_avg]
        totals["csat_score_avg"] = (
            sum(csat_values) / len(csat_values) if csat_values else None
        )
        totals["csat_responses"] = sum(s.csat_responses for s in snapshot_list)

        # Daily breakdown
        daily_data = [
            {
                "date": s.period_start.strftime("%Y-%m-%d"),
                "conversations_new": s.conversations_new,
                "conversations_resolved": s.conversations_resolved,
                "messages_total": s.messages_total,
                "avg_first_response_time": s.avg_first_response_time,
                "csat_score_avg": s.csat_score_avg,
            }
            for s in snapshot_list
        ]

        return {
            "period": {
                "from": report.date_from.isoformat(),
                "to": report.date_to.isoformat(),
            },
            "totals": totals,
            "daily_breakdown": daily_data,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    async def _generate_conversations_report(
        self, session: AsyncSession, report: Report
    ) -> dict:
        """Generate conversations report data."""
        tenant_id = report.tenant_id
        date_from = datetime.combine(report.date_from, datetime.min.time())
        date_to = datetime.combine(report.date_to, datetime.max.time())
        filters = report.filters or {}

        # Base query
        base_conditions = [
            Conversation.tenant_id == tenant_id,
            Conversation.created_at >= date_from,
            Conversation.created_at <= date_to,
        ]

        # Apply filters
        if "channels" in filters:
            base_conditions.append(Conversation.channel.in_(filters["channels"]))
        if "statuses" in filters:
            base_conditions.append(Conversation.status.in_(filters["statuses"]))

        # Total conversations
        total_result = await session.execute(
            select(func.count(Conversation.id)).where(and_(*base_conditions))
        )
        total_conversations = total_result.scalar() or 0

        # By status
        status_result = await session.execute(
            select(
                Conversation.status,
                func.count(Conversation.id),
            )
            .where(and_(*base_conditions))
            .group_by(Conversation.status)
        )
        by_status = {
            row[0].value: row[1] for row in status_result.fetchall()
        }

        # By channel
        channel_result = await session.execute(
            select(
                Conversation.channel,
                func.count(Conversation.id),
            )
            .where(and_(*base_conditions))
            .group_by(Conversation.channel)
        )
        by_channel = {
            row[0].value: row[1] for row in channel_result.fetchall()
        }

        # By priority
        priority_result = await session.execute(
            select(
                Conversation.priority,
                func.count(Conversation.id),
            )
            .where(and_(*base_conditions))
            .group_by(Conversation.priority)
        )
        by_priority = {
            row[0].value: row[1] for row in priority_result.fetchall()
        }

        # Response time distribution
        frt_result = await session.execute(
            select(
                func.percentile_cont(0.5).within_group(
                    extract('epoch', Conversation.first_response_at - Conversation.created_at)
                ),
                func.percentile_cont(0.9).within_group(
                    extract('epoch', Conversation.first_response_at - Conversation.created_at)
                ),
                func.avg(
                    extract('epoch', Conversation.first_response_at - Conversation.created_at)
                ),
            ).where(
                and_(
                    *base_conditions,
                    Conversation.first_response_at.isnot(None),
                )
            )
        )
        frt_row = frt_result.fetchone()

        # Daily trend
        daily_result = await session.execute(
            select(
                func.date(Conversation.created_at),
                func.count(Conversation.id),
            )
            .where(and_(*base_conditions))
            .group_by(func.date(Conversation.created_at))
            .order_by(func.date(Conversation.created_at))
        )
        daily_trend = [
            {"date": str(row[0]), "count": row[1]}
            for row in daily_result.fetchall()
        ]

        return {
            "period": {
                "from": report.date_from.isoformat(),
                "to": report.date_to.isoformat(),
            },
            "filters": filters,
            "summary": {
                "total": total_conversations,
                "by_status": by_status,
                "by_channel": by_channel,
                "by_priority": by_priority,
            },
            "response_times": {
                "median_first_response": int(frt_row[0]) if frt_row and frt_row[0] else None,
                "p90_first_response": int(frt_row[1]) if frt_row and frt_row[1] else None,
                "avg_first_response": int(frt_row[2]) if frt_row and frt_row[2] else None,
            },
            "daily_trend": daily_trend,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    async def _generate_operators_report(
        self, session: AsyncSession, report: Report
    ) -> dict:
        """Generate operators performance report."""
        tenant_id = report.tenant_id
        date_from = datetime.combine(report.date_from, datetime.min.time())
        date_to = datetime.combine(report.date_to, datetime.max.time())
        filters = report.filters or {}

        # Get all operators for tenant
        operators_result = await session.execute(
            select(User).where(
                and_(
                    User.tenant_id == tenant_id,
                    User.role.in_(["operator", "admin"]),
                )
            )
        )
        operators = {str(u.id): u for u in operators_result.scalars().all()}

        # Operator stats
        operator_conditions = [
            Conversation.tenant_id == tenant_id,
            Conversation.created_at >= date_from,
            Conversation.created_at <= date_to,
            Conversation.assigned_to.isnot(None),
        ]

        if "operator_ids" in filters:
            operator_conditions.append(Conversation.assigned_to.in_(filters["operator_ids"]))

        stats_result = await session.execute(
            select(
                Conversation.assigned_to,
                func.count(Conversation.id).label("total"),
                func.count(
                    func.nullif(Conversation.status == ConversationStatus.RESOLVED, False)
                ).label("resolved"),
                func.avg(
                    extract('epoch', Conversation.first_response_at - Conversation.created_at)
                ).label("avg_frt"),
                func.avg(
                    extract('epoch', Conversation.resolved_at - Conversation.created_at)
                ).label("avg_resolution"),
            )
            .where(and_(*operator_conditions))
            .group_by(Conversation.assigned_to)
        )

        operator_stats = []
        for row in stats_result.fetchall():
            operator_id = str(row[0])
            operator = operators.get(operator_id)
            operator_stats.append({
                "operator_id": operator_id,
                "name": f"{operator.first_name or ''} {operator.last_name or ''}".strip() if operator else "Unknown",
                "email": operator.email if operator else None,
                "conversations_total": row[1],
                "conversations_resolved": row[2] or 0,
                "resolution_rate": round((row[2] or 0) / row[1] * 100, 1) if row[1] > 0 else 0,
                "avg_first_response_time": int(row[3]) if row[3] else None,
                "avg_resolution_time": int(row[4]) if row[4] else None,
            })

        # Sort by conversations handled
        operator_stats.sort(key=lambda x: x["conversations_total"], reverse=True)

        # Team totals
        team_totals = {
            "total_conversations": sum(o["conversations_total"] for o in operator_stats),
            "total_resolved": sum(o["conversations_resolved"] for o in operator_stats),
            "avg_first_response_time": None,
            "avg_resolution_time": None,
        }

        frt_values = [o["avg_first_response_time"] for o in operator_stats if o["avg_first_response_time"]]
        resolution_values = [o["avg_resolution_time"] for o in operator_stats if o["avg_resolution_time"]]

        if frt_values:
            team_totals["avg_first_response_time"] = sum(frt_values) // len(frt_values)
        if resolution_values:
            team_totals["avg_resolution_time"] = sum(resolution_values) // len(resolution_values)

        return {
            "period": {
                "from": report.date_from.isoformat(),
                "to": report.date_to.isoformat(),
            },
            "team_summary": team_totals,
            "operators": operator_stats,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    async def _generate_channels_report(
        self, session: AsyncSession, report: Report
    ) -> dict:
        """Generate channels report."""
        tenant_id = report.tenant_id
        date_from = datetime.combine(report.date_from, datetime.min.time())
        date_to = datetime.combine(report.date_to, datetime.max.time())

        base_conditions = [
            Conversation.tenant_id == tenant_id,
            Conversation.created_at >= date_from,
            Conversation.created_at <= date_to,
        ]

        # Channel stats
        channel_result = await session.execute(
            select(
                Conversation.channel,
                func.count(Conversation.id).label("conversations"),
                func.count(
                    func.nullif(Conversation.status == ConversationStatus.RESOLVED, False)
                ).label("resolved"),
                func.avg(
                    extract('epoch', Conversation.first_response_at - Conversation.created_at)
                ).label("avg_frt"),
            )
            .where(and_(*base_conditions))
            .group_by(Conversation.channel)
        )

        channel_stats = []
        total_conversations = 0

        for row in channel_result.fetchall():
            channel_stats.append({
                "channel": row[0].value,
                "conversations": row[1],
                "resolved": row[2] or 0,
                "resolution_rate": round((row[2] or 0) / row[1] * 100, 1) if row[1] > 0 else 0,
                "avg_first_response_time": int(row[3]) if row[3] else None,
            })
            total_conversations += row[1]

        # Add percentage
        for stat in channel_stats:
            stat["percentage"] = round(stat["conversations"] / total_conversations * 100, 1) if total_conversations > 0 else 0

        # Sort by conversations
        channel_stats.sort(key=lambda x: x["conversations"], reverse=True)

        # Messages per channel
        messages_result = await session.execute(
            select(
                Conversation.channel,
                func.count(Message.id).label("messages"),
            )
            .join(Message)
            .where(
                and_(
                    *base_conditions,
                    Message.created_at >= date_from,
                    Message.created_at <= date_to,
                )
            )
            .group_by(Conversation.channel)
        )

        messages_by_channel = {row[0].value: row[1] for row in messages_result.fetchall()}

        for stat in channel_stats:
            stat["messages"] = messages_by_channel.get(stat["channel"], 0)

        return {
            "period": {
                "from": report.date_from.isoformat(),
                "to": report.date_to.isoformat(),
            },
            "total_conversations": total_conversations,
            "channels": channel_stats,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    async def _generate_csat_report(
        self, session: AsyncSession, report: Report
    ) -> dict:
        """Generate CSAT report."""
        tenant_id = report.tenant_id
        date_from = datetime.combine(report.date_from, datetime.min.time())
        date_to = datetime.combine(report.date_to, datetime.max.time())

        # Get snapshots with CSAT data
        snapshots = await session.execute(
            select(AnalyticsSnapshot)
            .where(
                and_(
                    AnalyticsSnapshot.tenant_id == tenant_id,
                    AnalyticsSnapshot.period == SnapshotPeriod.DAILY,
                    AnalyticsSnapshot.period_start >= date_from,
                    AnalyticsSnapshot.period_start <= date_to,
                    AnalyticsSnapshot.csat_responses > 0,
                )
            )
            .order_by(AnalyticsSnapshot.period_start)
        )
        snapshot_list = list(snapshots.scalars().all())

        # Aggregate CSAT data
        total_responses = sum(s.csat_responses for s in snapshot_list)
        csat_scores = [s.csat_score_avg for s in snapshot_list if s.csat_score_avg]
        avg_score = sum(csat_scores) / len(csat_scores) if csat_scores else None

        # Aggregate distribution
        distribution = {}
        for s in snapshot_list:
            for score, count in (s.csat_score_distribution or {}).items():
                distribution[score] = distribution.get(score, 0) + count

        # Daily trend
        daily_trend = [
            {
                "date": s.period_start.strftime("%Y-%m-%d"),
                "score": s.csat_score_avg,
                "responses": s.csat_responses,
            }
            for s in snapshot_list
        ]

        # NPS-style breakdown
        promoters = distribution.get("5", 0)
        passives = distribution.get("4", 0) + distribution.get("3", 0)
        detractors = distribution.get("2", 0) + distribution.get("1", 0)

        nps = None
        if total_responses > 0:
            nps = round((promoters - detractors) / total_responses * 100, 1)

        return {
            "period": {
                "from": report.date_from.isoformat(),
                "to": report.date_to.isoformat(),
            },
            "summary": {
                "total_responses": total_responses,
                "average_score": round(avg_score, 2) if avg_score else None,
                "nps": nps,
            },
            "distribution": distribution,
            "breakdown": {
                "promoters": promoters,
                "passives": passives,
                "detractors": detractors,
            },
            "daily_trend": daily_trend,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    async def _generate_ai_report(
        self, session: AsyncSession, report: Report
    ) -> dict:
        """Generate AI usage report."""
        tenant_id = report.tenant_id
        date_from = datetime.combine(report.date_from, datetime.min.time())
        date_to = datetime.combine(report.date_to, datetime.max.time())

        # Get snapshots with AI data
        snapshots = await session.execute(
            select(AnalyticsSnapshot)
            .where(
                and_(
                    AnalyticsSnapshot.tenant_id == tenant_id,
                    AnalyticsSnapshot.period == SnapshotPeriod.DAILY,
                    AnalyticsSnapshot.period_start >= date_from,
                    AnalyticsSnapshot.period_start <= date_to,
                )
            )
            .order_by(AnalyticsSnapshot.period_start)
        )
        snapshot_list = list(snapshots.scalars().all())

        # Aggregate AI metrics
        total_suggestions = sum(s.ai_suggestions_total for s in snapshot_list)
        accepted = sum(s.ai_suggestions_accepted for s in snapshot_list)
        modified = sum(s.ai_suggestions_modified for s in snapshot_list)

        acceptance_rate = round(accepted / total_suggestions * 100, 1) if total_suggestions > 0 else 0
        modification_rate = round(modified / total_suggestions * 100, 1) if total_suggestions > 0 else 0

        # Daily trend
        daily_trend = [
            {
                "date": s.period_start.strftime("%Y-%m-%d"),
                "suggestions": s.ai_suggestions_total,
                "accepted": s.ai_suggestions_accepted,
                "modified": s.ai_suggestions_modified,
            }
            for s in snapshot_list
        ]

        return {
            "period": {
                "from": report.date_from.isoformat(),
                "to": report.date_to.isoformat(),
            },
            "summary": {
                "total_suggestions": total_suggestions,
                "accepted": accepted,
                "modified": modified,
                "rejected": total_suggestions - accepted - modified,
                "acceptance_rate": acceptance_rate,
                "modification_rate": modification_rate,
            },
            "daily_trend": daily_trend,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    async def _generate_custom_report(
        self, session: AsyncSession, report: Report
    ) -> dict:
        """Generate custom report based on config."""
        config = report.config or {}
        metrics = config.get("metrics", [])

        data = {
            "period": {
                "from": report.date_from.isoformat(),
                "to": report.date_to.isoformat(),
            },
            "config": config,
            "data": {},
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

        # Generate each requested metric
        for metric in metrics:
            if metric == "conversations":
                data["data"]["conversations"] = await self._generate_conversations_report(session, report)
            elif metric == "operators":
                data["data"]["operators"] = await self._generate_operators_report(session, report)
            elif metric == "channels":
                data["data"]["channels"] = await self._generate_channels_report(session, report)
            elif metric == "csat":
                data["data"]["csat"] = await self._generate_csat_report(session, report)
            elif metric == "ai":
                data["data"]["ai"] = await self._generate_ai_report(session, report)

        return data


# Singleton
_report_generator: ReportGenerator | None = None


def get_report_generator() -> ReportGenerator:
    """Get report generator singleton."""
    global _report_generator
    if _report_generator is None:
        _report_generator = ReportGenerator()
    return _report_generator
