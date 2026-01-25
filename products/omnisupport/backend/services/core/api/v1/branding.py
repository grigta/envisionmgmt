"""Branding endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from shared.auth.dependencies import CurrentTenant, get_db, require_permissions
from shared.models.user import User
from shared.schemas.tenant import BrandingUpdate
from shared.schemas.base import SuccessResponse

router = APIRouter()


@router.get("")
async def get_branding(
    current_tenant: CurrentTenant,
):
    """Get branding settings."""
    return current_tenant.branding


@router.patch("")
async def update_branding(
    data: BrandingUpdate,
    current_user: Annotated[User, Depends(require_permissions("settings:manage"))],
    current_tenant: CurrentTenant,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update branding settings."""
    update_data = data.model_dump(exclude_unset=True)

    current_branding = current_tenant.branding or {}
    current_tenant.branding = {**current_branding, **update_data}

    await db.commit()
    await db.refresh(current_tenant)

    return current_tenant.branding


@router.post("/logo")
async def upload_logo(
    current_user: Annotated[User, Depends(require_permissions("settings:manage"))],
    current_tenant: CurrentTenant,
    db: Annotated[AsyncSession, Depends(get_db)],
    file: UploadFile = File(...),
):
    """Upload company logo."""
    # Validate file type
    allowed_types = ["image/png", "image/jpeg", "image/svg+xml", "image/webp"]

    if file.content_type not in allowed_types:
        from fastapi import HTTPException, status

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неподдерживаемый формат изображения",
        )

    # TODO: Upload to S3 and get URL
    # logo_url = await upload_to_storage(file, f"logos/{current_tenant.id}")

    logo_url = f"/uploads/logos/{current_tenant.id}/{file.filename}"

    current_branding = current_tenant.branding or {}
    current_tenant.branding = {**current_branding, "logo_url": logo_url}

    await db.commit()
    await db.refresh(current_tenant)

    return {"logo_url": logo_url}


@router.get("/emails")
async def get_email_branding(
    current_tenant: CurrentTenant,
):
    """Get email template branding."""
    branding = current_tenant.branding or {}
    return {
        "header_logo_url": branding.get("email_header_logo_url"),
        "footer_text": branding.get("email_footer_text"),
        "primary_color": branding.get("primary_color", "#6366f1"),
    }


@router.patch("/emails")
async def update_email_branding(
    current_user: Annotated[User, Depends(require_permissions("settings:manage"))],
    current_tenant: CurrentTenant,
    db: Annotated[AsyncSession, Depends(get_db)],
    header_logo_url: str | None = None,
    footer_text: str | None = None,
):
    """Update email template branding."""
    current_branding = current_tenant.branding or {}

    if header_logo_url is not None:
        current_branding["email_header_logo_url"] = header_logo_url
    if footer_text is not None:
        current_branding["email_footer_text"] = footer_text

    current_tenant.branding = current_branding

    await db.commit()
    await db.refresh(current_tenant)

    return {
        "header_logo_url": current_branding.get("email_header_logo_url"),
        "footer_text": current_branding.get("email_footer_text"),
    }


@router.get("/domain")
async def get_domain_settings(
    current_tenant: CurrentTenant,
):
    """Get custom domain settings."""
    return {
        "domain": current_tenant.domain,
        "verified": current_tenant.is_verified,
    }


@router.patch("/domain")
async def update_domain(
    current_user: Annotated[User, Depends(require_permissions("settings:manage"))],
    current_tenant: CurrentTenant,
    db: Annotated[AsyncSession, Depends(get_db)],
    domain: str,
):
    """Set custom domain."""
    # TODO: Validate domain ownership via DNS

    current_tenant.domain = domain
    current_tenant.is_verified = False  # Will be verified after DNS check

    await db.commit()
    await db.refresh(current_tenant)

    return {
        "domain": current_tenant.domain,
        "verified": current_tenant.is_verified,
        "dns_records": [
            {"type": "CNAME", "name": domain, "value": "app.omnisupport.ru"},
            {"type": "TXT", "name": f"_omnisupport.{domain}", "value": f"verify={current_tenant.id}"},
        ],
    }


@router.post("/domain/verify", response_model=SuccessResponse)
async def verify_domain(
    current_user: Annotated[User, Depends(require_permissions("settings:manage"))],
    current_tenant: CurrentTenant,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Verify custom domain ownership."""
    if not current_tenant.domain:
        from fastapi import HTTPException, status

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Домен не установлен",
        )

    # TODO: Check DNS records
    # is_verified = await verify_dns_records(current_tenant.domain, current_tenant.id)

    is_verified = True  # Placeholder

    if is_verified:
        current_tenant.is_verified = True
        await db.commit()
        return SuccessResponse(message="Домен подтверждён")

    return SuccessResponse(success=False, message="DNS записи не найдены")
