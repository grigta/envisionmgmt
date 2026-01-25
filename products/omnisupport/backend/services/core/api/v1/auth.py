"""Authentication endpoints."""

from datetime import datetime, timedelta, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.auth.dependencies import ActiveUser, get_db
from shared.auth.jwt import (
    create_access_token,
    create_refresh_token,
    decode_token,
    create_email_verification_token,
    create_password_reset_token,
    decode_special_token,
)
from shared.auth.password import hash_password, verify_password
from shared.auth.two_factor import (
    generate_totp_secret,
    verify_totp_code,
    generate_qr_code_url,
    generate_backup_codes,
)
from shared.config import get_settings
from shared.models.tenant import Tenant
from shared.models.user import User, Role, UserRole
from shared.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    RefreshTokenRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    ChangePasswordRequest,
    TwoFactorEnableResponse,
    TwoFactorVerifyRequest,
    TwoFactorDisableRequest,
)
from shared.schemas.base import SuccessResponse

router = APIRouter()
settings = get_settings()


@router.post("/register", response_model=TokenResponse)
async def register(
    data: RegisterRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Register a new user and tenant."""
    # Check if email already exists
    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email уже существует",
        )

    # Create tenant
    slug = data.company_name.lower().replace(" ", "-")[:50]
    # Ensure unique slug
    base_slug = slug
    counter = 1
    while True:
        result = await db.execute(select(Tenant).where(Tenant.slug == slug))
        if not result.scalar_one_or_none():
            break
        slug = f"{base_slug}-{counter}"
        counter += 1

    tenant = Tenant(
        name=data.company_name,
        slug=slug,
        email=data.email,
    )
    db.add(tenant)
    await db.flush()

    # Create default admin role
    admin_role = Role(
        tenant_id=tenant.id,
        name="Администратор",
        description="Полный доступ ко всем функциям",
        is_system=True,
        permissions=["*"],
    )
    db.add(admin_role)
    await db.flush()

    # Create user
    user = User(
        tenant_id=tenant.id,
        email=data.email,
        password_hash=hash_password(data.password),
        first_name=data.first_name,
        last_name=data.last_name,
        email_verified=False,
    )
    db.add(user)
    await db.flush()

    # Assign admin role
    user_role = UserRole(user_id=user.id, role_id=admin_role.id)
    db.add(user_role)

    await db.commit()

    # Generate tokens
    access_token = create_access_token(
        user_id=user.id,
        tenant_id=tenant.id,
        permissions=["*"],
    )
    refresh_token = create_refresh_token(
        user_id=user.id,
        tenant_id=tenant.id,
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Login with email and password."""
    # Find user
    result = await db.execute(
        select(User)
        .join(Tenant)
        .where(User.email == data.email)
        .where(Tenant.is_active == True)
    )
    user = result.scalar_one_or_none()

    if not user or not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
        )

    if not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Аккаунт деактивирован",
        )

    # Check 2FA
    if user.two_factor_enabled:
        if not data.two_factor_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Требуется код двухфакторной аутентификации",
                headers={"X-2FA-Required": "true"},
            )
        if not verify_totp_code(user.two_factor_secret, data.two_factor_code):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный код двухфакторной аутентификации",
            )

    # Get user permissions from roles
    permissions = []
    result = await db.execute(
        select(Role)
        .join(UserRole)
        .where(UserRole.user_id == user.id)
    )
    for role in result.scalars():
        permissions.extend(role.permissions)
    permissions = list(set(permissions))

    # Generate tokens
    access_token = create_access_token(
        user_id=user.id,
        tenant_id=user.tenant_id,
        permissions=permissions,
    )
    refresh_token = create_refresh_token(
        user_id=user.id,
        tenant_id=user.tenant_id,
    )

    # Update last activity
    user.last_activity_at = datetime.now(timezone.utc)
    await db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post("/logout", response_model=SuccessResponse)
async def logout(current_user: ActiveUser):
    """Logout current user."""
    # In a more complete implementation, we would invalidate the refresh token
    return SuccessResponse(message="Выход выполнен успешно")


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    data: RefreshTokenRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Refresh access token using refresh token."""
    payload = decode_token(data.refresh_token)

    if payload is None or payload.type != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный refresh token",
        )

    user_id = UUID(payload.sub)
    tenant_id = UUID(payload.tenant_id)

    # Verify user still exists and is active
    result = await db.execute(
        select(User)
        .join(Tenant)
        .where(User.id == user_id)
        .where(User.is_active == True)
        .where(Tenant.is_active == True)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден или деактивирован",
        )

    # Get permissions
    permissions = []
    result = await db.execute(
        select(Role)
        .join(UserRole)
        .where(UserRole.user_id == user.id)
    )
    for role in result.scalars():
        permissions.extend(role.permissions)
    permissions = list(set(permissions))

    # Generate new tokens
    access_token = create_access_token(
        user_id=user.id,
        tenant_id=tenant_id,
        permissions=permissions,
    )
    new_refresh_token = create_refresh_token(
        user_id=user.id,
        tenant_id=tenant_id,
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post("/forgot-password", response_model=SuccessResponse)
async def forgot_password(
    data: ForgotPasswordRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Request password reset."""
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    # Always return success to prevent email enumeration
    if user:
        token = create_password_reset_token(user.id, user.email)
        user.password_reset_token = token
        user.password_reset_expires = datetime.now(timezone.utc) + timedelta(hours=1)
        await db.commit()

        # TODO: Send password reset email
        # await send_password_reset_email(user.email, token)

    return SuccessResponse(
        message="Если email зарегистрирован, на него отправлена ссылка для сброса пароля"
    )


@router.post("/reset-password", response_model=SuccessResponse)
async def reset_password(
    data: ResetPasswordRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Reset password using token."""
    payload = decode_special_token(data.token, "password_reset")

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Недействительный или истекший токен",
        )

    user_id = UUID(payload["sub"])

    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user or user.password_reset_token != data.token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Недействительный или истекший токен",
        )

    # Update password
    user.password_hash = hash_password(data.password)
    user.password_reset_token = None
    user.password_reset_expires = None
    await db.commit()

    return SuccessResponse(message="Пароль успешно изменён")


@router.get("/verify-email/{token}", response_model=SuccessResponse)
async def verify_email(
    token: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Verify email address."""
    payload = decode_special_token(token, "email_verification")

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Недействительный или истекший токен",
        )

    user_id = UUID(payload["sub"])

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь не найден",
        )

    user.email_verified = True
    user.email_verification_token = None
    user.email_verification_expires = None
    await db.commit()

    return SuccessResponse(message="Email успешно подтверждён")


@router.post("/change-password", response_model=SuccessResponse)
async def change_password(
    data: ChangePasswordRequest,
    current_user: ActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Change current user's password."""
    if not verify_password(data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный текущий пароль",
        )

    current_user.password_hash = hash_password(data.new_password)
    await db.commit()

    return SuccessResponse(message="Пароль успешно изменён")


@router.post("/two-factor/enable", response_model=TwoFactorEnableResponse)
async def enable_two_factor(
    current_user: ActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Enable two-factor authentication."""
    if current_user.two_factor_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Двухфакторная аутентификация уже включена",
        )

    secret = generate_totp_secret()
    qr_code_url = generate_qr_code_url(secret, current_user.email)
    backup_codes = generate_backup_codes()

    # Store secret temporarily (will be confirmed in verify step)
    current_user.two_factor_secret = secret
    await db.commit()

    return TwoFactorEnableResponse(
        secret=secret,
        qr_code_url=qr_code_url,
        backup_codes=backup_codes,
    )


@router.post("/two-factor/verify", response_model=SuccessResponse)
async def verify_two_factor(
    data: TwoFactorVerifyRequest,
    current_user: ActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Verify and confirm two-factor authentication setup."""
    if not current_user.two_factor_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Сначала начните настройку 2FA",
        )

    if not verify_totp_code(current_user.two_factor_secret, data.code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный код",
        )

    current_user.two_factor_enabled = True
    await db.commit()

    return SuccessResponse(message="Двухфакторная аутентификация включена")


@router.post("/two-factor/disable", response_model=SuccessResponse)
async def disable_two_factor(
    data: TwoFactorDisableRequest,
    current_user: ActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Disable two-factor authentication."""
    if not current_user.two_factor_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Двухфакторная аутентификация не включена",
        )

    if not verify_password(data.password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный пароль",
        )

    if not verify_totp_code(current_user.two_factor_secret, data.code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный код",
        )

    current_user.two_factor_enabled = False
    current_user.two_factor_secret = None
    await db.commit()

    return SuccessResponse(message="Двухфакторная аутентификация отключена")
