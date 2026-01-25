"""Analytics endpoints."""

from datetime import date, datetime, timedelta, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from shared.auth.dependencies import ActiveUser, get_db, require_permissions
from shared.models.analytics import AnalyticsSnapshot, Report, ReportType, ReportFormat, SnapshotPeriod
from shared.models.conversation import Conversation, ConversationStatus
from shared.models.user import User
from shared.schemas.base import SuccessResponse, PaginatedResponse

from services.admin.reports.generator import get_report_generator
from services.admin.reports.exporters import get_exporter

router = APIRouter()


# ==================== Schemas ====================

class ReportCreate(BaseModel):
    """Report creation request."""
    name: str
    type: ReportType
    date_from: date
    date_to: date
    description: str | None = None
    filters: dict | None = None
    config: dict | None = None


class ReportSchedule(BaseModel):
    """Report schedule configuration."""
    schedule_cron: str
    recipients: list[str]


# ==================== Dashboard ====================

@router.get("/dashboard")
async def get_dashboard(
    current_user: Annotated[User, Depends(require_permissions("analytics:read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    date_from: date | None = None,
    date_to: date | None = None,
):
    """Get dashboard metrics."""
    if not date_from:
        date_from = date.today() - timedelta(days=30)
    if not date_to:
        date_to = date.today()

    # Get latest daily snapshot
    result = await db.execute(
        select(AnalyticsSnapshot)
        .where(AnalyticsSnapshot.tenant_id == current_user.tenant_id)
        .where(AnalyticsSnapshot.period == SnapshotPeriod.DAILY)
        .where(AnalyticsSnapshot.period_start >= datetime.combine(date_from, datetime.min.time()))
        .order_by(AnalyticsSnapshot.period_start.desc())
        .limit(1)
    )
    snapshot = result.scalar_one_or_none()

    # Calculate comparison with previous period
    period_days = (date_to - date_from).days
    prev_date_to = date_from - timedelta(days=1)
    prev_date_from = prev_date_to - timedelta(days=period_days)

    prev_result = await db.execute(
        select(AnalyticsSnapshot)
        .where(AnalyticsSnapshot.tenant_id == current_user.tenant_id)
        .where(AnalyticsSnapshot.period == SnapshotPeriod.DAILY)
        .where(AnalyticsSnapshot.period_start >= datetime.combine(prev_date_from, datetime.min.time()))
        .where(AnalyticsSnapshot.period_start <= datetime.combine(prev_date_to, datetime.max.time()))
        .order_by(AnalyticsSnapshot.period_start.desc())
        .limit(1)
    )
    prev_snapshot = prev_result.scalar_one_or_none()

    # Calculate live stats if no snapshot
    if not snapshot:
        conv_count = await db.execute(
            select(func.count())
            .select_from(Conversation)
            .where(Conversation.tenant_id == current_user.tenant_id)
            .where(Conversation.created_at >= datetime.combine(date_from, datetime.min.time()))
        )
        current_conversations = conv_count.scalar() or 0

        # Open conversations
        open_count = await db.execute(
            select(func.count())
            .select_from(Conversation)
            .where(Conversation.tenant_id == current_user.tenant_id)
            .where(Conversation.status == ConversationStatus.OPEN)
        )

        return {
            "conversations_total": current_conversations,
            "conversations_open": open_count.scalar() or 0,
            "conversations_new": 0,
            "conversations_resolved": 0,
            "avg_first_response_time": None,
            "avg_resolution_time": None,
            "csat_score": None,
            "period": {"from": date_from.isoformat(), "to": date_to.isoformat()},
            "changes": {},
        }

    # Calculate changes
    changes = {}
    if prev_snapshot:
        if prev_snapshot.conversations_new > 0:
            changes["conversations_new"] = round(
                (snapshot.conversations_new - prev_snapshot.conversations_new) / prev_snapshot.conversations_new * 100, 1
            )
        if prev_snapshot.avg_first_response_time and snapshot.avg_first_response_time:
            changes["avg_first_response_time"] = round(
                (snapshot.avg_first_response_time - prev_snapshot.avg_first_response_time) / prev_snapshot.avg_first_response_time * 100, 1
            )
        if prev_snapshot.csat_score_avg and snapshot.csat_score_avg:
            changes["csat_score"] = round(snapshot.csat_score_avg - prev_snapshot.csat_score_avg, 2)

    # Get open conversations count
    open_count = await db.execute(
        select(func.count())
        .select_from(Conversation)
        .where(Conversation.tenant_id == current_user.tenant_id)
        .where(Conversation.status == ConversationStatus.OPEN)
    )

    return {
        "conversations_total": snapshot.conversations_total,
        "conversations_open": open_count.scalar() or 0,
        "conversations_new": snapshot.conversations_new,
        "conversations_resolved": snapshot.conversations_resolved,
        "avg_first_response_time": snapshot.avg_first_response_time,
        "avg_resolution_time": snapshot.avg_resolution_time,
        "csat_score": snapshot.csat_score_avg,
        "messages_total": snapshot.messages_total,
        "customers_active": snapshot.customers_active,
        "period": {"from": date_from.isoformat(), "to": date_to.isoformat()},
        "changes": changes,
    }


@router.get("/realtime")
async def get_realtime_stats(
    current_user: Annotated[User, Depends(require_permissions("analytics:read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get real-time statistics."""
    tenant_id = current_user.tenant_id

    # Open conversations
    open_result = await db.execute(
        select(func.count())
        .select_from(Conversation)
        .where(Conversation.tenant_id == tenant_id)
        .where(Conversation.status == ConversationStatus.OPEN)
    )

    # Pending conversations (no response yet)
    pending_result = await db.execute(
        select(func.count())
        .select_from(Conversation)
        .where(
            and_(
                Conversation.tenant_id == tenant_id,
                Conversation.status == ConversationStatus.OPEN,
                Conversation.first_response_at.is_(None),
            )
        )
    )

    # Online operators
    online_result = await db.execute(
        select(func.count())
        .select_from(User)
        .where(
            and_(
                User.tenant_id == tenant_id,
                User.status == "online",
            )
        )
    )

    # Today's conversations
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    today_result = await db.execute(
        select(func.count())
        .select_from(Conversation)
        .where(
            and_(
                Conversation.tenant_id == tenant_id,
                Conversation.created_at >= today,
            )
        )
    )

    return {
        "open_conversations": open_result.scalar() or 0,
        "pending_response": pending_result.scalar() or 0,
        "online_operators": online_result.scalar() or 0,
        "today_conversations": today_result.scalar() or 0,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ==================== Conversations Analytics ====================

@router.get("/conversations")
async def get_conversation_analytics(
    current_user: Annotated[User, Depends(require_permissions("analytics:read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    date_from: date | None = None,
    date_to: date | None = None,
    group_by: str = Query("day", pattern="^(hour|day|week|month)$"),
):
    """Get conversation analytics over time."""
    if not date_from:
        date_from = date.today() - timedelta(days=30)
    if not date_to:
        date_to = date.today()

    period = SnapshotPeriod.DAILY if group_by == "day" else SnapshotPeriod.HOURLY

    result = await db.execute(
        select(AnalyticsSnapshot)
        .where(AnalyticsSnapshot.tenant_id == current_user.tenant_id)
        .where(AnalyticsSnapshot.period == period)
        .where(AnalyticsSnapshot.period_start >= datetime.combine(date_from, datetime.min.time()))
        .where(AnalyticsSnapshot.period_start <= datetime.combine(date_to, datetime.max.time()))
        .order_by(AnalyticsSnapshot.period_start)
    )
    snapshots = list(result.scalars().all())

    data_points = [
        {
            "date": s.period_start.isoformat(),
            "total": s.conversations_total,
            "new": s.conversations_new,
            "resolved": s.conversations_resolved,
            "closed": s.conversations_closed,
        }
        for s in snapshots
    ]

    # Summary
    summary = {
        "total_new": sum(s.conversations_new for s in snapshots),
        "total_resolved": sum(s.conversations_resolved for s in snapshots),
        "total_closed": sum(s.conversations_closed for s in snapshots),
    }

    return {
        "data": data_points,
        "summary": summary,
        "period": {"from": date_from.isoformat(), "to": date_to.isoformat()},
    }


@router.get("/conversations/by-status")
async def get_conversations_by_status(
    current_user: Annotated[User, Depends(require_permissions("analytics:read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get current conversation distribution by status."""
    result = await db.execute(
        select(
            Conversation.status,
            func.count(Conversation.id),
        )
        .where(Conversation.tenant_id == current_user.tenant_id)
        .group_by(Conversation.status)
    )

    by_status = {row[0].value: row[1] for row in result.fetchall()}
    total = sum(by_status.values())

    return {
        "by_status": by_status,
        "total": total,
    }


# ==================== Operators Analytics ====================

@router.get("/operators")
async def get_operator_analytics(
    current_user: Annotated[User, Depends(require_permissions("analytics:read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    date_from: date | None = None,
    date_to: date | None = None,
):
    """Get operator performance analytics."""
    if not date_from:
        date_from = date.today() - timedelta(days=30)
    if not date_to:
        date_to = date.today()

    result = await db.execute(
        select(AnalyticsSnapshot)
        .where(AnalyticsSnapshot.tenant_id == current_user.tenant_id)
        .where(AnalyticsSnapshot.period == SnapshotPeriod.DAILY)
        .order_by(AnalyticsSnapshot.period_start.desc())
        .limit(1)
    )
    snapshot = result.scalar_one_or_none()

    if snapshot and snapshot.operator_metrics:
        # Enrich with user data
        operators = []
        for operator_id, metrics in snapshot.operator_metrics.items():
            user_result = await db.execute(
                select(User).where(User.id == operator_id)
            )
            user = user_result.scalar_one_or_none()

            operators.append({
                "id": operator_id,
                "name": f"{user.first_name or ''} {user.last_name or ''}".strip() if user else "Unknown",
                "email": user.email if user else None,
                "avatar_url": user.avatar_url if user else None,
                **metrics,
            })

        return {"operators": operators}

    return {"operators": []}


@router.get("/operators/online")
async def get_online_operators(
    current_user: Annotated[User, Depends(require_permissions("analytics:read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get currently online operators."""
    result = await db.execute(
        select(User)
        .where(User.tenant_id == current_user.tenant_id)
        .where(User.status == "online")
        .where(User.role.in_(["operator", "admin"]))
    )
    users = list(result.scalars().all())

    return {
        "operators": [
            {
                "id": str(u.id),
                "name": f"{u.first_name or ''} {u.last_name or ''}".strip(),
                "email": u.email,
                "avatar_url": u.avatar_url,
                "last_seen_at": u.last_seen_at.isoformat() if u.last_seen_at else None,
            }
            for u in users
        ],
        "count": len(users),
    }


# ==================== Channels Analytics ====================

@router.get("/channels")
async def get_channel_analytics(
    current_user: Annotated[User, Depends(require_permissions("analytics:read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    date_from: date | None = None,
    date_to: date | None = None,
):
    """Get channel analytics."""
    if not date_from:
        date_from = date.today() - timedelta(days=30)

    result = await db.execute(
        select(AnalyticsSnapshot)
        .where(AnalyticsSnapshot.tenant_id == current_user.tenant_id)
        .where(AnalyticsSnapshot.period == SnapshotPeriod.DAILY)
        .order_by(AnalyticsSnapshot.period_start.desc())
        .limit(1)
    )
    snapshot = result.scalar_one_or_none()

    if snapshot and snapshot.channel_metrics:
        channels = []
        total = sum(m.get("conversations", 0) for m in snapshot.channel_metrics.values())

        for channel_name, metrics in snapshot.channel_metrics.items():
            channels.append({
                "channel": channel_name,
                "conversations": metrics.get("conversations", 0),
                "messages": metrics.get("messages", 0),
                "percentage": round(metrics.get("conversations", 0) / total * 100, 1) if total > 0 else 0,
            })

        channels.sort(key=lambda x: x["conversations"], reverse=True)
        return {"channels": channels, "total": total}

    return {"channels": [], "total": 0}


# ==================== CSAT Analytics ====================

@router.get("/csat")
async def get_csat_analytics(
    current_user: Annotated[User, Depends(require_permissions("analytics:read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    date_from: date | None = None,
    date_to: date | None = None,
):
    """Get CSAT (customer satisfaction) analytics."""
    if not date_from:
        date_from = date.today() - timedelta(days=30)

    result = await db.execute(
        select(AnalyticsSnapshot)
        .where(AnalyticsSnapshot.tenant_id == current_user.tenant_id)
        .where(AnalyticsSnapshot.period == SnapshotPeriod.DAILY)
        .where(AnalyticsSnapshot.period_start >= datetime.combine(date_from, datetime.min.time()))
        .order_by(AnalyticsSnapshot.period_start)
    )
    snapshots = list(result.scalars().all())

    if snapshots:
        total_responses = sum(s.csat_responses for s in snapshots)
        csat_values = [s.csat_score_avg for s in snapshots if s.csat_score_avg]
        avg_score = sum(csat_values) / len(csat_values) if csat_values else None

        # Aggregate distribution
        distribution = {}
        for s in snapshots:
            for score, count in (s.csat_score_distribution or {}).items():
                distribution[score] = distribution.get(score, 0) + count

        # Trend data
        trend = [
            {
                "date": s.period_start.strftime("%Y-%m-%d"),
                "score": s.csat_score_avg,
                "responses": s.csat_responses,
            }
            for s in snapshots if s.csat_responses > 0
        ]

        return {
            "score": round(avg_score, 2) if avg_score else None,
            "responses": total_responses,
            "distribution": distribution,
            "trend": trend,
        }

    return {"score": None, "responses": 0, "distribution": {}, "trend": []}


# ==================== AI Analytics ====================

@router.get("/ai")
async def get_ai_analytics(
    current_user: Annotated[User, Depends(require_permissions("analytics:read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    date_from: date | None = None,
    date_to: date | None = None,
):
    """Get AI suggestions analytics."""
    if not date_from:
        date_from = date.today() - timedelta(days=30)

    result = await db.execute(
        select(AnalyticsSnapshot)
        .where(AnalyticsSnapshot.tenant_id == current_user.tenant_id)
        .where(AnalyticsSnapshot.period == SnapshotPeriod.DAILY)
        .where(AnalyticsSnapshot.period_start >= datetime.combine(date_from, datetime.min.time()))
        .order_by(AnalyticsSnapshot.period_start)
    )
    snapshots = list(result.scalars().all())

    if snapshots:
        total = sum(s.ai_suggestions_total for s in snapshots)
        accepted = sum(s.ai_suggestions_accepted for s in snapshots)
        modified = sum(s.ai_suggestions_modified for s in snapshots)

        trend = [
            {
                "date": s.period_start.strftime("%Y-%m-%d"),
                "suggestions": s.ai_suggestions_total,
                "accepted": s.ai_suggestions_accepted,
                "modified": s.ai_suggestions_modified,
            }
            for s in snapshots if s.ai_suggestions_total > 0
        ]

        return {
            "total_suggestions": total,
            "accepted": accepted,
            "modified": modified,
            "rejected": total - accepted - modified,
            "acceptance_rate": round(accepted / total * 100, 1) if total > 0 else 0,
            "modification_rate": round(modified / total * 100, 1) if total > 0 else 0,
            "trend": trend,
        }

    return {
        "total_suggestions": 0,
        "accepted": 0,
        "modified": 0,
        "rejected": 0,
        "acceptance_rate": 0,
        "modification_rate": 0,
        "trend": [],
    }


# ==================== Tags Analytics ====================

@router.get("/tags")
async def get_tag_analytics(
    current_user: Annotated[User, Depends(require_permissions("analytics:read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(20, ge=1, le=100),
):
    """Get tag usage analytics."""
    result = await db.execute(
        select(AnalyticsSnapshot)
        .where(AnalyticsSnapshot.tenant_id == current_user.tenant_id)
        .where(AnalyticsSnapshot.period == SnapshotPeriod.DAILY)
        .order_by(AnalyticsSnapshot.period_start.desc())
        .limit(1)
    )
    snapshot = result.scalar_one_or_none()

    if snapshot and snapshot.tag_metrics:
        tags = [
            {"tag": tag, "count": count}
            for tag, count in sorted(snapshot.tag_metrics.items(), key=lambda x: x[1], reverse=True)
        ][:limit]
        return {"tags": tags, "total": sum(t["count"] for t in tags)}

    return {"tags": [], "total": 0}


# ==================== Reports ====================

@router.get("/reports")
async def list_reports(
    current_user: Annotated[User, Depends(require_permissions("analytics:read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    type: ReportType | None = None,
):
    """List saved reports."""
    query = (
        select(Report)
        .where(Report.tenant_id == current_user.tenant_id)
        .order_by(Report.created_at.desc())
    )

    if type:
        query = query.where(Report.type == type)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    reports = list(result.scalars().all())

    return PaginatedResponse.create(
        items=[
            {
                "id": str(r.id),
                "name": r.name,
                "description": r.description,
                "type": r.type.value,
                "date_from": r.date_from.isoformat(),
                "date_to": r.date_to.isoformat(),
                "is_scheduled": r.is_scheduled,
                "export_format": r.export_format.value if r.export_format else None,
                "export_url": r.export_url,
                "exported_at": r.exported_at.isoformat() if r.exported_at else None,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in reports
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/reports")
async def create_report(
    data: ReportCreate,
    current_user: Annotated[User, Depends(require_permissions("analytics:read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    background_tasks: BackgroundTasks,
):
    """Create and generate a report."""
    report = Report(
        tenant_id=current_user.tenant_id,
        created_by=current_user.id,
        name=data.name,
        description=data.description,
        type=data.type,
        date_from=data.date_from,
        date_to=data.date_to,
        filters=data.filters or {},
        config=data.config or {},
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)

    # Generate report data in background
    async def generate():
        generator = get_report_generator()
        await generator.generate_report_data(report.id)

    background_tasks.add_task(generate)

    return {
        "id": str(report.id),
        "name": report.name,
        "type": report.type.value,
        "status": "generating",
        "message": "Отчёт генерируется",
    }


@router.get("/reports/{report_id}")
async def get_report(
    report_id: UUID,
    current_user: Annotated[User, Depends(require_permissions("analytics:read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get report by ID."""
    result = await db.execute(
        select(Report)
        .where(Report.id == report_id)
        .where(Report.tenant_id == current_user.tenant_id)
    )
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Отчёт не найден",
        )

    return {
        "id": str(report.id),
        "name": report.name,
        "description": report.description,
        "type": report.type.value,
        "date_from": report.date_from.isoformat(),
        "date_to": report.date_to.isoformat(),
        "filters": report.filters,
        "config": report.config,
        "data": report.data,
        "export_format": report.export_format.value if report.export_format else None,
        "export_url": report.export_url,
        "exported_at": report.exported_at.isoformat() if report.exported_at else None,
        "is_scheduled": report.is_scheduled,
        "schedule_cron": report.schedule_cron,
        "schedule_recipients": report.schedule_recipients,
        "created_at": report.created_at.isoformat() if report.created_at else None,
    }


@router.post("/reports/{report_id}/generate")
async def regenerate_report(
    report_id: UUID,
    current_user: Annotated[User, Depends(require_permissions("analytics:read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    background_tasks: BackgroundTasks,
):
    """Regenerate report data."""
    result = await db.execute(
        select(Report)
        .where(Report.id == report_id)
        .where(Report.tenant_id == current_user.tenant_id)
    )
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Отчёт не найден",
        )

    async def generate():
        generator = get_report_generator()
        await generator.generate_report_data(report_id)

    background_tasks.add_task(generate)

    return {"message": "Генерация отчёта запущена", "report_id": str(report_id)}


@router.post("/reports/{report_id}/export")
async def export_report(
    report_id: UUID,
    current_user: Annotated[User, Depends(require_permissions("analytics:read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    format: ReportFormat = Query(ReportFormat.PDF),
):
    """Export report to file format."""
    result = await db.execute(
        select(Report)
        .where(Report.id == report_id)
        .where(Report.tenant_id == current_user.tenant_id)
    )
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Отчёт не найден",
        )

    if not report.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Отчёт ещё не сгенерирован",
        )

    # Export to format
    exporter = get_exporter(format.value)
    file_bytes, content_type = await exporter.export(report.data, report.name)

    # Determine filename
    ext = {"pdf": "pdf", "excel": "xlsx", "csv": "csv"}.get(format.value, "bin")
    filename = f"{report.name}_{report.date_from}_{report.date_to}.{ext}"

    # Update report
    report.export_format = format
    report.exported_at = datetime.now(timezone.utc)
    await db.commit()

    return Response(
        content=file_bytes,
        media_type=content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.patch("/reports/{report_id}/schedule")
async def update_report_schedule(
    report_id: UUID,
    data: ReportSchedule,
    current_user: Annotated[User, Depends(require_permissions("analytics:read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update report schedule."""
    result = await db.execute(
        select(Report)
        .where(Report.id == report_id)
        .where(Report.tenant_id == current_user.tenant_id)
    )
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Отчёт не найден",
        )

    report.is_scheduled = True
    report.schedule_cron = data.schedule_cron
    report.schedule_recipients = data.recipients
    await db.commit()

    return {"message": "Расписание обновлено", "report_id": str(report_id)}


@router.delete("/reports/{report_id}/schedule", response_model=SuccessResponse)
async def remove_report_schedule(
    report_id: UUID,
    current_user: Annotated[User, Depends(require_permissions("analytics:read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Remove report schedule."""
    result = await db.execute(
        select(Report)
        .where(Report.id == report_id)
        .where(Report.tenant_id == current_user.tenant_id)
    )
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Отчёт не найден",
        )

    report.is_scheduled = False
    report.schedule_cron = None
    report.schedule_recipients = []
    await db.commit()

    return SuccessResponse(message="Расписание удалено")


@router.delete("/reports/{report_id}", response_model=SuccessResponse)
async def delete_report(
    report_id: UUID,
    current_user: Annotated[User, Depends(require_permissions("analytics:read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete report."""
    result = await db.execute(
        select(Report)
        .where(Report.id == report_id)
        .where(Report.tenant_id == current_user.tenant_id)
    )
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Отчёт не найден",
        )

    await db.delete(report)
    await db.commit()

    return SuccessResponse(message="Отчёт удалён")
