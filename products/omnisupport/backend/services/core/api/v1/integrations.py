"""Integration endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.auth.dependencies import ActiveUser, get_db, require_permissions
from shared.models.integration import Integration, IntegrationType, IntegrationStatus, ApiKey
from shared.models.user import User
from shared.schemas.base import SuccessResponse

router = APIRouter()


# Available integrations catalog
AVAILABLE_INTEGRATIONS = [
    {
        "type": "crm",
        "provider": "bitrix24",
        "name": "Битрикс24",
        "description": "Интеграция с CRM Битрикс24",
        "logo_url": "/integrations/bitrix24.svg",
    },
    {
        "type": "crm",
        "provider": "amocrm",
        "name": "amoCRM",
        "description": "Интеграция с amoCRM",
        "logo_url": "/integrations/amocrm.svg",
    },
    {
        "type": "helpdesk",
        "provider": "zendesk",
        "name": "Zendesk",
        "description": "Интеграция с Zendesk",
        "logo_url": "/integrations/zendesk.svg",
    },
    {
        "type": "analytics",
        "provider": "yandex_metrica",
        "name": "Яндекс Метрика",
        "description": "Отправка событий в Яндекс Метрику",
        "logo_url": "/integrations/yandex-metrica.svg",
    },
]


@router.get("")
async def list_available_integrations():
    """List all available integrations."""
    return {"items": AVAILABLE_INTEGRATIONS, "total": len(AVAILABLE_INTEGRATIONS)}


@router.get("/connected")
async def list_connected_integrations(
    current_user: Annotated[User, Depends(require_permissions("integrations:read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """List connected integrations for current tenant."""
    result = await db.execute(
        select(Integration)
        .where(Integration.tenant_id == current_user.tenant_id)
        .order_by(Integration.created_at.desc())
    )
    integrations = list(result.scalars().all())

    return {"items": integrations, "total": len(integrations)}


@router.post("/{provider}/connect")
async def connect_integration(
    provider: str,
    current_user: Annotated[User, Depends(require_permissions("integrations:manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    name: str,
    credentials: dict,
    settings: dict | None = None,
):
    """Connect an integration."""
    # Find integration type
    integration_info = next(
        (i for i in AVAILABLE_INTEGRATIONS if i["provider"] == provider), None
    )

    if not integration_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Интеграция не найдена",
        )

    integration = Integration(
        tenant_id=current_user.tenant_id,
        type=IntegrationType(integration_info["type"]),
        provider=provider,
        name=name,
        credentials=credentials,
        settings=settings or {},
        status=IntegrationStatus.PENDING,
    )
    db.add(integration)
    await db.commit()
    await db.refresh(integration)

    # TODO: Validate credentials and connect
    # await validate_integration(integration)

    return integration


@router.get("/{integration_id}")
async def get_integration(
    integration_id: UUID,
    current_user: Annotated[User, Depends(require_permissions("integrations:read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get integration by ID."""
    result = await db.execute(
        select(Integration)
        .where(Integration.id == integration_id)
        .where(Integration.tenant_id == current_user.tenant_id)
    )
    integration = result.scalar_one_or_none()

    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Интеграция не найдена",
        )

    return integration


@router.patch("/{integration_id}")
async def update_integration(
    integration_id: UUID,
    current_user: Annotated[User, Depends(require_permissions("integrations:manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    name: str | None = None,
    settings: dict | None = None,
    field_mapping: dict | None = None,
    is_active: bool | None = None,
):
    """Update integration settings."""
    result = await db.execute(
        select(Integration)
        .where(Integration.id == integration_id)
        .where(Integration.tenant_id == current_user.tenant_id)
    )
    integration = result.scalar_one_or_none()

    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Интеграция не найдена",
        )

    if name is not None:
        integration.name = name
    if settings is not None:
        integration.settings = {**integration.settings, **settings}
    if field_mapping is not None:
        integration.field_mapping = field_mapping
    if is_active is not None:
        integration.is_active = is_active

    await db.commit()
    await db.refresh(integration)

    return integration


@router.delete("/{integration_id}", response_model=SuccessResponse)
async def disconnect_integration(
    integration_id: UUID,
    current_user: Annotated[User, Depends(require_permissions("integrations:manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Disconnect and delete integration."""
    result = await db.execute(
        select(Integration)
        .where(Integration.id == integration_id)
        .where(Integration.tenant_id == current_user.tenant_id)
    )
    integration = result.scalar_one_or_none()

    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Интеграция не найдена",
        )

    await db.delete(integration)
    await db.commit()

    return SuccessResponse(message="Интеграция отключена")


# ==================== API Keys ====================

@router.get("/api-keys")
async def list_api_keys(
    current_user: Annotated[User, Depends(require_permissions("integrations:read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """List API keys."""
    result = await db.execute(
        select(ApiKey)
        .where(ApiKey.tenant_id == current_user.tenant_id)
        .where(ApiKey.is_active == True)
        .order_by(ApiKey.created_at.desc())
    )
    keys = list(result.scalars().all())

    return {"items": keys, "total": len(keys)}


@router.post("/api-keys")
async def create_api_key(
    current_user: Annotated[User, Depends(require_permissions("integrations:manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    name: str,
    permissions: list[str] | None = None,
    rate_limit: int = 1000,
):
    """Create API key."""
    import secrets
    import hashlib

    # Generate key
    raw_key = secrets.token_urlsafe(32)
    key_prefix = raw_key[:8]
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

    api_key = ApiKey(
        tenant_id=current_user.tenant_id,
        created_by=current_user.id,
        name=name,
        key_prefix=key_prefix,
        key_hash=key_hash,
        permissions=permissions or ["*"],
        rate_limit=rate_limit,
    )
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)

    # Return the raw key only once
    return {
        "id": str(api_key.id),
        "name": api_key.name,
        "key": raw_key,  # Only shown once!
        "key_prefix": key_prefix,
        "permissions": api_key.permissions,
        "message": "Сохраните ключ, он больше не будет показан",
    }


@router.delete("/api-keys/{key_id}", response_model=SuccessResponse)
async def delete_api_key(
    key_id: UUID,
    current_user: Annotated[User, Depends(require_permissions("integrations:manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete API key."""
    result = await db.execute(
        select(ApiKey)
        .where(ApiKey.id == key_id)
        .where(ApiKey.tenant_id == current_user.tenant_id)
    )
    api_key = result.scalar_one_or_none()

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API ключ не найден",
        )

    api_key.is_active = False
    await db.commit()

    return SuccessResponse(message="API ключ удалён")
