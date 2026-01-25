"""Superadmin API endpoints."""

from datetime import date, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from shared.auth.dependencies import get_db, require_superadmin
from shared.models.user import User
from shared.models.billing import SubscriptionStatus, BillingPeriod
from shared.schemas.base import SuccessResponse, PaginatedResponse
from services.superadmin.service import SuperadminService, get_superadmin_service

router = APIRouter()


# ==================== Pydantic Schemas ====================

class TenantSubscriptionResponse(BaseModel):
    """Tenant subscription info."""
    id: UUID
    plan_id: UUID
    plan_name: str | None = None
    status: SubscriptionStatus
    billing_period: BillingPeriod
    current_period_start: date
    current_period_end: date
    trial_end: date | None = None

    model_config = {"from_attributes": True}


class TenantResponse(BaseModel):
    """Tenant response schema."""
    id: UUID
    name: str
    slug: str
    email: str | None = None
    phone: str | None = None
    website: str | None = None
    domain: str | None = None
    is_active: bool
    is_verified: bool
    created_at: datetime
    subscription: TenantSubscriptionResponse | None = None

    model_config = {"from_attributes": True}


class TenantDetailResponse(TenantResponse):
    """Detailed tenant response with stats."""
    settings: dict
    branding: dict
    business_hours: dict
    stats: dict | None = None


class CreateTenantRequest(BaseModel):
    """Create tenant request."""
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-z0-9-]+$")
    email: EmailStr | None = None
    plan_id: UUID | None = None
    settings: dict | None = None


class UpdateTenantRequest(BaseModel):
    """Update tenant request."""
    name: str | None = Field(None, min_length=1, max_length=255)
    email: str | None = None
    phone: str | None = None
    website: str | None = None
    domain: str | None = None
    settings: dict | None = None
    branding: dict | None = None
    business_hours: dict | None = None
    notification_settings: dict | None = None
    is_verified: bool | None = None


class PlatformStatsResponse(BaseModel):
    """Platform stats response."""
    tenants: dict
    users: dict
    customers: dict
    conversations: dict
    messages: dict
    subscriptions: dict
    revenue: dict


class GrowthDataPoint(BaseModel):
    """Growth data point."""
    date: str
    new_tenants: int
    new_users: int
    conversations: int


class PlanResponse(BaseModel):
    """Plan response schema."""
    id: UUID
    name: str
    display_name: str
    description: str | None = None
    price_monthly: int
    price_yearly: int
    currency: str
    features: list[str]
    limits: dict
    is_active: bool
    is_featured: bool
    trial_days: int
    sort_order: int

    model_config = {"from_attributes": True}


class CreatePlanRequest(BaseModel):
    """Create plan request."""
    name: str = Field(..., min_length=1, max_length=100)
    display_name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    price_monthly: int = Field(..., ge=0)
    price_yearly: int = Field(..., ge=0)
    features: list[str] = Field(default_factory=list)
    limits: dict = Field(default_factory=dict)
    trial_days: int = Field(14, ge=0)
    is_featured: bool = False
    sort_order: int = 0


class UpdatePlanRequest(BaseModel):
    """Update plan request."""
    display_name: str | None = None
    description: str | None = None
    price_monthly: int | None = Field(None, ge=0)
    price_yearly: int | None = Field(None, ge=0)
    features: list[str] | None = None
    limits: dict | None = None
    trial_days: int | None = Field(None, ge=0)
    is_featured: bool | None = None
    is_active: bool | None = None
    sort_order: int | None = None


# ==================== Helper functions ====================

def _serialize_tenant(tenant, include_stats: bool = False) -> dict:
    """Serialize tenant to dict."""
    subscription = None
    if tenant.subscription:
        subscription = {
            "id": tenant.subscription.id,
            "plan_id": tenant.subscription.plan_id,
            "plan_name": tenant.subscription.plan.display_name if tenant.subscription.plan else None,
            "status": tenant.subscription.status,
            "billing_period": tenant.subscription.billing_period,
            "current_period_start": tenant.subscription.current_period_start,
            "current_period_end": tenant.subscription.current_period_end,
            "trial_end": tenant.subscription.trial_end,
        }

    data = {
        "id": tenant.id,
        "name": tenant.name,
        "slug": tenant.slug,
        "email": tenant.email,
        "phone": tenant.phone,
        "website": tenant.website,
        "domain": tenant.domain,
        "is_active": tenant.is_active,
        "is_verified": tenant.is_verified,
        "created_at": tenant.created_at,
        "subscription": subscription,
    }

    if include_stats:
        data["settings"] = tenant.settings
        data["branding"] = tenant.branding
        data["business_hours"] = tenant.business_hours

    return data


# ==================== Tenants ====================

@router.get("/tenants")
async def list_tenants(
    current_user: Annotated[User, Depends(require_superadmin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    search: str | None = Query(None),
    is_active: bool | None = Query(None),
    subscription_status: SubscriptionStatus | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """List all tenants."""
    service = await get_superadmin_service(db)

    tenants, total = await service.list_tenants(
        search=search,
        is_active=is_active,
        subscription_status=subscription_status,
        limit=page_size,
        offset=(page - 1) * page_size,
    )

    return PaginatedResponse.create(
        items=[_serialize_tenant(t) for t in tenants],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/tenants/{tenant_id}")
async def get_tenant(
    tenant_id: UUID,
    current_user: Annotated[User, Depends(require_superadmin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get tenant details."""
    service = await get_superadmin_service(db)

    tenant = await service.get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Тенант не найден",
        )

    # Get stats
    stats = await service.get_tenant_stats(tenant_id)

    data = _serialize_tenant(tenant, include_stats=True)
    data["stats"] = stats

    return data


@router.post("/tenants", status_code=status.HTTP_201_CREATED)
async def create_tenant(
    request: CreateTenantRequest,
    current_user: Annotated[User, Depends(require_superadmin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create new tenant."""
    service = await get_superadmin_service(db)

    # Check slug uniqueness
    existing = await service.get_tenant_by_slug(request.slug)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Slug уже используется",
        )

    tenant = await service.create_tenant(
        name=request.name,
        slug=request.slug,
        email=request.email,
        plan_id=request.plan_id,
        settings=request.settings,
    )

    await db.commit()
    await db.refresh(tenant)

    return _serialize_tenant(tenant)


@router.patch("/tenants/{tenant_id}")
async def update_tenant(
    tenant_id: UUID,
    request: UpdateTenantRequest,
    current_user: Annotated[User, Depends(require_superadmin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update tenant."""
    service = await get_superadmin_service(db)

    tenant = await service.update_tenant(
        tenant_id=tenant_id,
        **request.model_dump(exclude_unset=True),
    )

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Тенант не найден",
        )

    await db.commit()
    await db.refresh(tenant)

    return _serialize_tenant(tenant, include_stats=True)


@router.post("/tenants/{tenant_id}/activate", response_model=SuccessResponse)
async def activate_tenant(
    tenant_id: UUID,
    current_user: Annotated[User, Depends(require_superadmin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Activate tenant."""
    service = await get_superadmin_service(db)

    tenant = await service.activate_tenant(tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Тенант не найден",
        )

    await db.commit()
    return SuccessResponse(message="Тенант активирован")


@router.post("/tenants/{tenant_id}/deactivate", response_model=SuccessResponse)
async def deactivate_tenant(
    tenant_id: UUID,
    current_user: Annotated[User, Depends(require_superadmin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Deactivate tenant."""
    service = await get_superadmin_service(db)

    tenant = await service.deactivate_tenant(tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Тенант не найден",
        )

    await db.commit()
    return SuccessResponse(message="Тенант деактивирован")


@router.delete("/tenants/{tenant_id}", response_model=SuccessResponse)
async def delete_tenant(
    tenant_id: UUID,
    current_user: Annotated[User, Depends(require_superadmin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    confirm: bool = Query(False, description="Confirm deletion"),
):
    """Delete tenant (hard delete). Use with extreme caution."""
    if not confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Подтвердите удаление параметром confirm=true",
        )

    service = await get_superadmin_service(db)

    deleted = await service.delete_tenant(tenant_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Тенант не найден",
        )

    await db.commit()
    return SuccessResponse(message="Тенант удалён")


@router.get("/tenants/{tenant_id}/stats")
async def get_tenant_stats(
    tenant_id: UUID,
    current_user: Annotated[User, Depends(require_superadmin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get tenant statistics."""
    service = await get_superadmin_service(db)

    # Check tenant exists
    tenant = await service.get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Тенант не найден",
        )

    stats = await service.get_tenant_stats(tenant_id)
    return stats


# ==================== Platform Stats ====================

@router.get("/stats", response_model=PlatformStatsResponse)
async def get_platform_stats(
    current_user: Annotated[User, Depends(require_superadmin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get overall platform statistics."""
    service = await get_superadmin_service(db)
    stats = await service.get_platform_stats()
    return stats


@router.get("/stats/growth")
async def get_platform_growth(
    current_user: Annotated[User, Depends(require_superadmin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    days: int = Query(30, ge=1, le=365),
):
    """Get platform growth data."""
    service = await get_superadmin_service(db)
    growth = await service.get_platform_growth(days=days)
    return {"items": growth, "days": days}


# ==================== Plans Management ====================

@router.get("/plans")
async def list_plans(
    current_user: Annotated[User, Depends(require_superadmin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    include_inactive: bool = Query(False),
):
    """List all plans."""
    service = await get_superadmin_service(db)
    plans = await service.list_plans(include_inactive=include_inactive)

    return {
        "items": [PlanResponse.model_validate(p) for p in plans],
        "total": len(plans),
    }


@router.post("/plans", status_code=status.HTTP_201_CREATED, response_model=PlanResponse)
async def create_plan(
    request: CreatePlanRequest,
    current_user: Annotated[User, Depends(require_superadmin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create new plan."""
    service = await get_superadmin_service(db)

    plan = await service.create_plan(
        name=request.name,
        display_name=request.display_name,
        price_monthly=request.price_monthly,
        price_yearly=request.price_yearly,
        features=request.features,
        limits=request.limits,
        description=request.description,
        trial_days=request.trial_days,
        is_featured=request.is_featured,
        sort_order=request.sort_order,
    )

    await db.commit()
    await db.refresh(plan)
    return PlanResponse.model_validate(plan)


@router.patch("/plans/{plan_id}", response_model=PlanResponse)
async def update_plan(
    plan_id: UUID,
    request: UpdatePlanRequest,
    current_user: Annotated[User, Depends(require_superadmin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update plan."""
    service = await get_superadmin_service(db)

    plan = await service.update_plan(
        plan_id=plan_id,
        **request.model_dump(exclude_unset=True),
    )

    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Тарифный план не найден",
        )

    await db.commit()
    await db.refresh(plan)
    return PlanResponse.model_validate(plan)


# ==================== System Settings ====================

@router.get("/settings")
async def get_system_settings(
    current_user: Annotated[User, Depends(require_superadmin)],
):
    """Get system-wide settings."""
    # In a real app, these would come from a config store
    return {
        "maintenance_mode": False,
        "registration_enabled": True,
        "default_plan": "starter",
        "email_verification_required": True,
        "supported_channels": ["telegram", "whatsapp", "widget"],
        "ai_models": {
            "suggestion": "yandexgpt",
            "summarize": "yandexgpt",
            "rag": "yandexgpt",
        },
    }


@router.patch("/settings")
async def update_system_settings(
    current_user: Annotated[User, Depends(require_superadmin)],
    settings: dict,
):
    """Update system-wide settings."""
    # In a real app, this would update a config store
    # For now, just return success
    return SuccessResponse(message="Настройки обновлены")


# ==================== Health & Logs ====================

@router.get("/health")
async def health_check(
    current_user: Annotated[User, Depends(require_superadmin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Check system health."""
    from sqlalchemy import text

    # Database check
    try:
        await db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    # In a real app, would also check Redis, Qdrant, etc.
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "components": {
            "database": db_status,
            "redis": "healthy",  # Placeholder
            "qdrant": "healthy",  # Placeholder
        },
        "version": "1.0.0",
    }


@router.get("/logs")
async def get_system_logs(
    current_user: Annotated[User, Depends(require_superadmin)],
    level: str = Query("info", regex="^(debug|info|warning|error)$"),
    limit: int = Query(100, ge=1, le=1000),
):
    """Get system logs."""
    # In a real app, this would fetch from a logging service
    # For now, return placeholder
    return {
        "items": [],
        "level": level,
        "limit": limit,
        "message": "Логирование в разработке",
    }
