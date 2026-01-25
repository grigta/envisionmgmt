"""Billing endpoints."""

from datetime import date, datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from shared.auth.dependencies import ActiveUser, CurrentTenant, get_db, require_permissions
from shared.models.billing import (
    Plan,
    Subscription,
    SubscriptionStatus,
    Invoice,
    InvoiceStatus,
    UsageRecord,
    UsageType,
    PaymentMethod,
    PaymentMethodType,
    BillingPeriod,
)
from shared.models.user import User
from shared.schemas.base import SuccessResponse, PaginatedResponse
from services.admin.billing.service import BillingService, get_billing_service
from services.admin.billing.usage import UsageTracker, get_usage_tracker

router = APIRouter()


# ==================== Pydantic Schemas ====================

class PlanLimits(BaseModel):
    """Plan limits schema."""
    operators: int | None = None
    channels: int | None = None
    storage_gb: int | None = None
    ai_requests: int | None = None
    conversations: int | None = None
    messages: int | None = None
    api_calls: int | None = None


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
    is_featured: bool
    trial_days: int
    sort_order: int

    model_config = {"from_attributes": True}


class SubscriptionResponse(BaseModel):
    """Subscription response schema."""
    id: UUID
    tenant_id: UUID
    plan_id: UUID
    status: SubscriptionStatus
    billing_period: BillingPeriod
    trial_start: date | None = None
    trial_end: date | None = None
    current_period_start: date
    current_period_end: date
    canceled_at: datetime | None = None
    cancel_at_period_end: bool
    plan: PlanResponse | None = None

    model_config = {"from_attributes": True}


class SubscribeRequest(BaseModel):
    """Subscribe request schema."""
    plan_id: UUID
    billing_period: BillingPeriod = BillingPeriod.MONTHLY


class ChangePlanRequest(BaseModel):
    """Change plan request schema."""
    plan_id: UUID
    immediately: bool = False


class CancelSubscriptionRequest(BaseModel):
    """Cancel subscription request."""
    immediately: bool = False
    reason: str | None = None


class InvoiceItemResponse(BaseModel):
    """Invoice line item."""
    description: str
    quantity: int
    unit_price: int
    total: int


class InvoiceResponse(BaseModel):
    """Invoice response schema."""
    id: UUID
    number: str
    status: InvoiceStatus
    subtotal: int
    tax: int
    discount: int
    total: int
    currency: str
    period_start: date
    period_end: date
    items: list[dict]
    issued_at: datetime
    due_at: datetime
    paid_at: datetime | None = None
    payment_method: str | None = None
    payment_reference: str | None = None
    pdf_url: str | None = None

    model_config = {"from_attributes": True}


class PaymentMethodResponse(BaseModel):
    """Payment method response schema."""
    id: UUID
    type: PaymentMethodType
    card_brand: str | None = None
    card_last4: str | None = None
    card_exp_month: int | None = None
    card_exp_year: int | None = None
    bank_name: str | None = None
    is_default: bool

    model_config = {"from_attributes": True}


class AddPaymentMethodRequest(BaseModel):
    """Add payment method request."""
    type: PaymentMethodType
    card_token: str | None = None  # From payment gateway
    set_default: bool = True


class UsageItemResponse(BaseModel):
    """Usage item response."""
    quantity: int
    limit: int | None
    percentage: float
    exceeded: bool


class UsageResponse(BaseModel):
    """Usage response schema."""
    usage: dict[str, UsageItemResponse]
    period: dict[str, str]


class UsageSummaryResponse(BaseModel):
    """Usage summary response."""
    current: dict[str, UsageItemResponse]
    trends: dict[str, dict]
    period: dict[str, str]


# ==================== Plans ====================

@router.get("/plans", response_model=dict)
async def list_plans(
    db: Annotated[AsyncSession, Depends(get_db)],
    include_inactive: bool = Query(False),
):
    """List available subscription plans."""
    service = await get_billing_service(db)
    plans = await service.list_plans(active_only=not include_inactive)

    return {
        "items": [PlanResponse.model_validate(p) for p in plans],
        "total": len(plans),
    }


@router.get("/plans/{plan_id}", response_model=PlanResponse)
async def get_plan(
    plan_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get plan by ID."""
    service = await get_billing_service(db)
    plan = await service.get_plan(plan_id)

    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Тарифный план не найден",
        )

    return PlanResponse.model_validate(plan)


# ==================== Subscription ====================

@router.get("/subscription")
async def get_subscription(
    current_user: Annotated[User, Depends(require_permissions("billing:read"))],
    current_tenant: CurrentTenant,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get current subscription."""
    service = await get_billing_service(db)
    subscription = await service.get_subscription(current_tenant.id)

    if not subscription:
        return {"status": "no_subscription"}

    return SubscriptionResponse.model_validate(subscription)


@router.post("/subscribe", response_model=SubscriptionResponse)
async def subscribe(
    request: SubscribeRequest,
    current_user: Annotated[User, Depends(require_permissions("billing:manage"))],
    current_tenant: CurrentTenant,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Subscribe to a plan."""
    service = await get_billing_service(db)

    # Check if already subscribed
    existing = await service.get_subscription(current_tenant.id)
    if existing and existing.status in [SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Уже есть активная подписка",
        )

    try:
        subscription = await service.create_subscription(
            tenant_id=current_tenant.id,
            plan_id=request.plan_id,
            billing_period=request.billing_period,
        )
        await db.commit()
        await db.refresh(subscription)
        return SubscriptionResponse.model_validate(subscription)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post("/activate", response_model=SubscriptionResponse)
async def activate_subscription(
    current_user: Annotated[User, Depends(require_permissions("billing:manage"))],
    current_tenant: CurrentTenant,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Activate subscription after trial (requires payment)."""
    service = await get_billing_service(db)

    subscription = await service.activate_subscription(current_tenant.id)

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нет подписки для активации",
        )

    await db.commit()
    await db.refresh(subscription)
    return SubscriptionResponse.model_validate(subscription)


@router.post("/change-plan")
async def change_plan(
    request: ChangePlanRequest,
    current_user: Annotated[User, Depends(require_permissions("billing:manage"))],
    current_tenant: CurrentTenant,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Change subscription plan."""
    service = await get_billing_service(db)

    subscription, proration = await service.change_plan(
        tenant_id=current_tenant.id,
        new_plan_id=request.plan_id,
        immediately=request.immediately,
    )

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нет активной подписки",
        )

    await db.commit()
    await db.refresh(subscription)

    return {
        "subscription": SubscriptionResponse.model_validate(subscription),
        "proration_amount": proration,
        "proration_description": (
            f"Доплата за смену тарифа: {proration / 100:.2f} ₽"
            if proration > 0
            else f"Кредит: {abs(proration) / 100:.2f} ₽"
            if proration < 0
            else "Без доплаты"
        ),
    }


@router.post("/cancel", response_model=SuccessResponse)
async def cancel_subscription(
    current_user: Annotated[User, Depends(require_permissions("billing:manage"))],
    current_tenant: CurrentTenant,
    db: Annotated[AsyncSession, Depends(get_db)],
    request: CancelSubscriptionRequest | None = None,
):
    """Cancel subscription."""
    service = await get_billing_service(db)

    immediately = request.immediately if request else False
    reason = request.reason if request else None

    subscription = await service.cancel_subscription(
        tenant_id=current_tenant.id,
        immediately=immediately,
        reason=reason,
    )

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нет активной подписки",
        )

    await db.commit()

    return SuccessResponse(
        message="Подписка отменена" if immediately else "Подписка будет отменена в конце периода"
    )


@router.post("/reactivate", response_model=SubscriptionResponse)
async def reactivate_subscription(
    current_user: Annotated[User, Depends(require_permissions("billing:manage"))],
    current_tenant: CurrentTenant,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Reactivate canceled subscription (before period end)."""
    service = await get_billing_service(db)

    subscription = await service.reactivate_subscription(current_tenant.id)

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нет подписки для реактивации",
        )

    await db.commit()
    await db.refresh(subscription)
    return SubscriptionResponse.model_validate(subscription)


# ==================== Invoices ====================

@router.get("/invoices")
async def list_invoices(
    current_user: Annotated[User, Depends(require_permissions("billing:read"))],
    current_tenant: CurrentTenant,
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """List invoices."""
    service = await get_billing_service(db)

    invoices, total = await service.list_invoices(
        tenant_id=current_tenant.id,
        limit=page_size,
        offset=(page - 1) * page_size,
    )

    return PaginatedResponse.create(
        items=[InvoiceResponse.model_validate(inv) for inv in invoices],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: UUID,
    current_user: Annotated[User, Depends(require_permissions("billing:read"))],
    current_tenant: CurrentTenant,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get invoice by ID."""
    service = await get_billing_service(db)

    invoice = await service.get_invoice(invoice_id, current_tenant.id)

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Счёт не найден",
        )

    return InvoiceResponse.model_validate(invoice)


@router.post("/invoices/{invoice_id}/pay", response_model=InvoiceResponse)
async def pay_invoice(
    invoice_id: UUID,
    current_user: Annotated[User, Depends(require_permissions("billing:manage"))],
    current_tenant: CurrentTenant,
    db: Annotated[AsyncSession, Depends(get_db)],
    payment_method_id: UUID | None = None,
):
    """Pay invoice."""
    service = await get_billing_service(db)

    # Verify invoice belongs to tenant
    invoice = await service.get_invoice(invoice_id, current_tenant.id)
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Счёт не найден",
        )

    if invoice.status == InvoiceStatus.PAID:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Счёт уже оплачен",
        )

    # Get payment method
    if not payment_method_id:
        default_method = await service.get_default_payment_method(current_tenant.id)
        if default_method:
            payment_method_id = default_method.id

    # TODO: Process actual payment through payment gateway

    invoice = await service.pay_invoice(
        invoice_id=invoice_id,
        payment_method_id=payment_method_id,
        payment_reference=f"PAY-{invoice.number}",
    )

    await db.commit()
    await db.refresh(invoice)
    return InvoiceResponse.model_validate(invoice)


@router.get("/invoices/{invoice_id}/download")
async def download_invoice(
    invoice_id: UUID,
    current_user: Annotated[User, Depends(require_permissions("billing:read"))],
    current_tenant: CurrentTenant,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Download invoice as PDF."""
    service = await get_billing_service(db)

    invoice = await service.get_invoice(invoice_id, current_tenant.id)
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Счёт не найден",
        )

    if invoice.pdf_url:
        return {"pdf_url": invoice.pdf_url}

    # TODO: Generate PDF on-demand
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Генерация PDF в разработке",
    )


# ==================== Usage ====================

@router.get("/usage", response_model=UsageResponse)
async def get_usage(
    current_user: Annotated[User, Depends(require_permissions("billing:read"))],
    current_tenant: CurrentTenant,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get current usage stats."""
    tracker = await get_usage_tracker(db)

    usage = await tracker.get_current_usage(current_tenant.id)

    today = date.today()
    period_start = today.replace(day=1)

    return UsageResponse(
        usage={
            k: UsageItemResponse(**v)
            for k, v in usage.items()
        },
        period={
            "from": period_start.isoformat(),
            "to": today.isoformat(),
        },
    )


@router.get("/usage/summary", response_model=UsageSummaryResponse)
async def get_usage_summary(
    current_user: Annotated[User, Depends(require_permissions("billing:read"))],
    current_tenant: CurrentTenant,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get comprehensive usage summary with trends."""
    tracker = await get_usage_tracker(db)

    summary = await tracker.get_usage_summary(current_tenant.id)

    return UsageSummaryResponse(
        current={
            k: UsageItemResponse(**v) if isinstance(v, dict) else v
            for k, v in summary["current"].items()
        },
        trends=summary["trends"],
        period=summary["period"],
    )


@router.get("/usage/history")
async def get_usage_history(
    current_user: Annotated[User, Depends(require_permissions("billing:read"))],
    current_tenant: CurrentTenant,
    db: Annotated[AsyncSession, Depends(get_db)],
    usage_type: UsageType | None = Query(None),
    months: int = Query(6, ge=1, le=12),
):
    """Get usage history."""
    tracker = await get_usage_tracker(db)

    history = await tracker.get_usage_history(
        tenant_id=current_tenant.id,
        usage_type=usage_type,
        months=months,
    )

    return {"items": history, "total": len(history)}


@router.post("/usage/sync", response_model=SuccessResponse)
async def sync_usage(
    current_user: Annotated[User, Depends(require_permissions("billing:manage"))],
    current_tenant: CurrentTenant,
    db: Annotated[AsyncSession, Depends(get_db)],
    background_tasks: BackgroundTasks,
):
    """Manually sync usage records with actual database counts."""
    tracker = await get_usage_tracker(db)

    await tracker.sync_usage(current_tenant.id)
    await db.commit()

    return SuccessResponse(message="Использование синхронизировано")


@router.get("/usage/check/{usage_type}")
async def check_usage_limit(
    usage_type: UsageType,
    current_user: Annotated[User, Depends(require_permissions("billing:read"))],
    current_tenant: CurrentTenant,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Check if usage is within limits."""
    tracker = await get_usage_tracker(db)

    within_limit, current, limit = await tracker.check_limit(
        tenant_id=current_tenant.id,
        usage_type=usage_type,
    )

    return {
        "within_limit": within_limit,
        "current": current,
        "limit": limit,
        "usage_type": usage_type.value,
    }


# ==================== Payment Methods ====================

@router.get("/payment-methods")
async def list_payment_methods(
    current_user: Annotated[User, Depends(require_permissions("billing:read"))],
    current_tenant: CurrentTenant,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """List payment methods."""
    service = await get_billing_service(db)

    methods = await service.list_payment_methods(current_tenant.id)

    return {
        "items": [PaymentMethodResponse.model_validate(m) for m in methods],
        "total": len(methods),
    }


@router.post("/payment-methods", response_model=PaymentMethodResponse)
async def add_payment_method(
    request: AddPaymentMethodRequest,
    current_user: Annotated[User, Depends(require_permissions("billing:manage"))],
    current_tenant: CurrentTenant,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Add payment method."""
    service = await get_billing_service(db)

    # TODO: Process card token through payment gateway
    # payment_data = await payment_gateway.create_method(request.card_token)

    # Mock data for now
    method = await service.add_payment_method(
        tenant_id=current_tenant.id,
        method_type=request.type,
        card_brand="visa",  # From payment gateway
        card_last4="4242",  # From payment gateway
        card_exp_month=12,
        card_exp_year=2026,
        set_default=request.set_default,
    )

    await db.commit()
    await db.refresh(method)
    return PaymentMethodResponse.model_validate(method)


@router.patch("/payment-methods/{method_id}/default", response_model=PaymentMethodResponse)
async def set_default_payment_method(
    method_id: UUID,
    current_user: Annotated[User, Depends(require_permissions("billing:manage"))],
    current_tenant: CurrentTenant,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Set payment method as default."""
    service = await get_billing_service(db)

    method = await service.set_default_payment_method(method_id, current_tenant.id)

    if not method:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Способ оплаты не найден",
        )

    await db.commit()
    await db.refresh(method)
    return PaymentMethodResponse.model_validate(method)


@router.delete("/payment-methods/{method_id}", response_model=SuccessResponse)
async def delete_payment_method(
    method_id: UUID,
    current_user: Annotated[User, Depends(require_permissions("billing:manage"))],
    current_tenant: CurrentTenant,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete payment method."""
    service = await get_billing_service(db)

    deleted = await service.delete_payment_method(method_id, current_tenant.id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Способ оплаты не найден",
        )

    await db.commit()
    return SuccessResponse(message="Способ оплаты удалён")


# ==================== Billing Portal ====================

@router.get("/portal-url")
async def get_billing_portal_url(
    current_user: Annotated[User, Depends(require_permissions("billing:manage"))],
    current_tenant: CurrentTenant,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Get URL for external billing portal (e.g., Stripe Customer Portal).

    Returns a URL where users can manage their subscription, payment methods,
    and view invoices in a hosted billing portal.
    """
    # TODO: Integrate with payment gateway's billing portal
    # portal_session = await payment_gateway.create_portal_session(
    #     customer_id=current_tenant.external_customer_id,
    #     return_url="https://app.omnisupport.ru/settings/billing"
    # )

    return {
        "url": None,
        "message": "Портал биллинга в разработке",
    }
