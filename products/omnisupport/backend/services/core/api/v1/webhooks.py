"""Webhook endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from shared.auth.dependencies import ActiveUser, get_db, require_permissions
from shared.models.integration import Webhook, WebhookDelivery, WebhookEvent
from shared.models.user import User
from shared.schemas.base import SuccessResponse, PaginatedResponse

router = APIRouter()


@router.get("")
async def list_webhooks(
    current_user: Annotated[User, Depends(require_permissions("webhooks:read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """List webhooks."""
    result = await db.execute(
        select(Webhook)
        .where(Webhook.tenant_id == current_user.tenant_id)
        .order_by(Webhook.created_at.desc())
    )
    webhooks = list(result.scalars().all())

    return {"items": webhooks, "total": len(webhooks)}


@router.post("")
async def create_webhook(
    current_user: Annotated[User, Depends(require_permissions("webhooks:manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    name: str,
    url: str,
    events: list[str],
    description: str | None = None,
    headers: dict | None = None,
):
    """Create webhook."""
    import secrets

    webhook = Webhook(
        tenant_id=current_user.tenant_id,
        created_by=current_user.id,
        name=name,
        url=url,
        events=events,
        description=description,
        secret=secrets.token_urlsafe(32),
        headers=headers or {},
    )
    db.add(webhook)
    await db.commit()
    await db.refresh(webhook)

    return webhook


@router.get("/{webhook_id}")
async def get_webhook(
    webhook_id: UUID,
    current_user: Annotated[User, Depends(require_permissions("webhooks:read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get webhook by ID."""
    result = await db.execute(
        select(Webhook)
        .where(Webhook.id == webhook_id)
        .where(Webhook.tenant_id == current_user.tenant_id)
    )
    webhook = result.scalar_one_or_none()

    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Вебхук не найден",
        )

    return webhook


@router.patch("/{webhook_id}")
async def update_webhook(
    webhook_id: UUID,
    current_user: Annotated[User, Depends(require_permissions("webhooks:manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    name: str | None = None,
    url: str | None = None,
    events: list[str] | None = None,
    description: str | None = None,
    headers: dict | None = None,
    is_active: bool | None = None,
):
    """Update webhook."""
    result = await db.execute(
        select(Webhook)
        .where(Webhook.id == webhook_id)
        .where(Webhook.tenant_id == current_user.tenant_id)
    )
    webhook = result.scalar_one_or_none()

    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Вебхук не найден",
        )

    if name is not None:
        webhook.name = name
    if url is not None:
        webhook.url = url
    if events is not None:
        webhook.events = events
    if description is not None:
        webhook.description = description
    if headers is not None:
        webhook.headers = headers
    if is_active is not None:
        webhook.is_active = is_active

    await db.commit()
    await db.refresh(webhook)

    return webhook


@router.delete("/{webhook_id}", response_model=SuccessResponse)
async def delete_webhook(
    webhook_id: UUID,
    current_user: Annotated[User, Depends(require_permissions("webhooks:manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete webhook."""
    result = await db.execute(
        select(Webhook)
        .where(Webhook.id == webhook_id)
        .where(Webhook.tenant_id == current_user.tenant_id)
    )
    webhook = result.scalar_one_or_none()

    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Вебхук не найден",
        )

    await db.delete(webhook)
    await db.commit()

    return SuccessResponse(message="Вебхук удалён")


@router.get("/{webhook_id}/deliveries")
async def get_webhook_deliveries(
    webhook_id: UUID,
    current_user: Annotated[User, Depends(require_permissions("webhooks:read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """Get webhook delivery history."""
    # Verify webhook exists
    result = await db.execute(
        select(Webhook)
        .where(Webhook.id == webhook_id)
        .where(Webhook.tenant_id == current_user.tenant_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Вебхук не найден",
        )

    query = (
        select(WebhookDelivery)
        .where(WebhookDelivery.webhook_id == webhook_id)
        .order_by(WebhookDelivery.created_at.desc())
    )

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    deliveries = list(result.scalars().all())

    return PaginatedResponse.create(
        items=deliveries,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/{webhook_id}/test", response_model=SuccessResponse)
async def test_webhook(
    webhook_id: UUID,
    current_user: Annotated[User, Depends(require_permissions("webhooks:manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Send test webhook."""
    result = await db.execute(
        select(Webhook)
        .where(Webhook.id == webhook_id)
        .where(Webhook.tenant_id == current_user.tenant_id)
    )
    webhook = result.scalar_one_or_none()

    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Вебхук не найден",
        )

    # Create test delivery
    import httpx

    test_payload = {
        "event": "test",
        "timestamp": "2024-01-01T00:00:00Z",
        "data": {"message": "Test webhook delivery"},
    }

    delivery = WebhookDelivery(
        webhook_id=webhook_id,
        event="test",
        payload=test_payload,
    )
    db.add(delivery)

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                webhook.url,
                json=test_payload,
                headers=webhook.headers,
                timeout=webhook.timeout_seconds,
            )

            delivery.response_status = response.status_code
            delivery.response_body = response.text[:1000] if response.text else None
            delivery.status = "success" if response.is_success else "failed"

    except Exception as e:
        delivery.status = "failed"
        delivery.error_message = str(e)

    from datetime import datetime, timezone

    delivery.delivered_at = datetime.now(timezone.utc)
    delivery.attempts = 1

    await db.commit()

    if delivery.status == "success":
        return SuccessResponse(message="Тестовый вебхук успешно доставлен")
    else:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Ошибка доставки: {delivery.error_message or delivery.response_body}",
        )


@router.post("/{webhook_id}/rotate-secret")
async def rotate_webhook_secret(
    webhook_id: UUID,
    current_user: Annotated[User, Depends(require_permissions("webhooks:manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Rotate webhook secret."""
    import secrets

    result = await db.execute(
        select(Webhook)
        .where(Webhook.id == webhook_id)
        .where(Webhook.tenant_id == current_user.tenant_id)
    )
    webhook = result.scalar_one_or_none()

    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Вебхук не найден",
        )

    webhook.secret = secrets.token_urlsafe(32)
    await db.commit()
    await db.refresh(webhook)

    return {"secret": webhook.secret, "message": "Секретный ключ обновлён"}
