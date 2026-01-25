"""FastAPI authentication dependencies."""

from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from shared.auth.jwt import decode_token, TokenPayload
from shared.database import get_db
from shared.models.user import User
from shared.models.tenant import Tenant

# Security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Get current authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось проверить учётные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = credentials.credentials
    payload = decode_token(token)

    if payload is None:
        raise credentials_exception

    if payload.type != "access":
        raise credentials_exception

    try:
        user_id = UUID(payload.sub)
    except ValueError:
        raise credentials_exception

    # Fetch user from database
    result = await db.execute(
        select(User)
        .where(User.id == user_id)
        .options(
            selectinload(User.roles),
            selectinload(User.department_memberships),
            selectinload(User.skills),
        )
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Get current active user (not disabled)."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Пользователь деактивирован",
        )
    return current_user


async def get_current_tenant(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Tenant:
    """Get tenant for current user."""
    result = await db.execute(
        select(Tenant).where(Tenant.id == current_user.tenant_id)
    )
    tenant = result.scalar_one_or_none()

    if tenant is None or not tenant.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Тенант не найден или деактивирован",
        )

    return tenant


def require_permissions(*required_permissions: str):
    """
    Dependency factory that checks for required permissions.

    Usage:
        @router.get("/admin")
        async def admin_endpoint(
            user: User = Depends(require_permissions("admin:read"))
        ):
            ...
    """

    async def permission_checker(
        current_user: Annotated[User, Depends(get_current_active_user)],
    ) -> User:
        # Collect all user permissions from roles
        user_permissions: set[str] = set()
        for user_role in current_user.roles:
            if user_role.role:
                user_permissions.update(user_role.role.permissions)

        # Check if user has wildcard permission
        if "*" in user_permissions:
            return current_user

        # Check each required permission
        for perm in required_permissions:
            if perm not in user_permissions:
                # Check for wildcard in category (e.g., "conversations:*")
                category = perm.split(":")[0]
                if f"{category}:*" not in user_permissions:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Недостаточно прав: требуется {perm}",
                    )

        return current_user

    return permission_checker


async def require_superadmin(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    """
    Dependency that requires superadmin role.

    Superadmins have role = 'superadmin' and tenant_id = None (platform-level user).
    """
    if current_user.role != "superadmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Требуются права суперадмина",
        )
    return current_user


# Commonly used dependencies
CurrentUser = Annotated[User, Depends(get_current_user)]
ActiveUser = Annotated[User, Depends(get_current_active_user)]
CurrentTenant = Annotated[Tenant, Depends(get_current_tenant)]
SuperAdmin = Annotated[User, Depends(require_superadmin)]
