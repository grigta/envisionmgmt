"""Settings endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from shared.auth.dependencies import ActiveUser, CurrentTenant, get_db, require_permissions
from shared.models.tenant import Tenant
from shared.models.user import User
from shared.schemas.tenant import (
    TenantResponse,
    TenantUpdate,
    TenantSettingsUpdate,
    BusinessHoursUpdate,
    NotificationSettingsUpdate,
)

router = APIRouter()


@router.get("/company", response_model=TenantResponse)
async def get_company_settings(
    current_tenant: CurrentTenant,
):
    """Get company settings."""
    return current_tenant


@router.patch("/company", response_model=TenantResponse)
async def update_company_settings(
    data: TenantUpdate,
    current_user: Annotated[User, Depends(require_permissions("settings:manage"))],
    current_tenant: CurrentTenant,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update company settings."""
    update_data = data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        if hasattr(current_tenant, field):
            setattr(current_tenant, field, value)

    await db.commit()
    await db.refresh(current_tenant)

    return current_tenant


@router.get("/general")
async def get_general_settings(
    current_tenant: CurrentTenant,
):
    """Get general settings."""
    return current_tenant.settings


@router.patch("/general")
async def update_general_settings(
    data: TenantSettingsUpdate,
    current_user: Annotated[User, Depends(require_permissions("settings:manage"))],
    current_tenant: CurrentTenant,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update general settings."""
    update_data = data.model_dump(exclude_unset=True)

    current_settings = current_tenant.settings or {}
    current_tenant.settings = {**current_settings, **update_data}

    await db.commit()
    await db.refresh(current_tenant)

    return current_tenant.settings


@router.get("/business-hours")
async def get_business_hours(
    current_tenant: CurrentTenant,
):
    """Get business hours settings."""
    return current_tenant.business_hours


@router.patch("/business-hours")
async def update_business_hours(
    data: BusinessHoursUpdate,
    current_user: Annotated[User, Depends(require_permissions("settings:manage"))],
    current_tenant: CurrentTenant,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update business hours settings."""
    current_tenant.business_hours = data.model_dump()

    await db.commit()
    await db.refresh(current_tenant)

    return current_tenant.business_hours


@router.get("/notifications")
async def get_notification_settings(
    current_tenant: CurrentTenant,
):
    """Get notification settings."""
    return current_tenant.notification_settings


@router.patch("/notifications")
async def update_notification_settings(
    data: NotificationSettingsUpdate,
    current_user: Annotated[User, Depends(require_permissions("settings:manage"))],
    current_tenant: CurrentTenant,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update notification settings."""
    update_data = data.model_dump(exclude_unset=True)

    current_settings = current_tenant.notification_settings or {}
    current_tenant.notification_settings = {**current_settings, **update_data}

    await db.commit()
    await db.refresh(current_tenant)

    return current_tenant.notification_settings
