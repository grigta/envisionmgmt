"""User endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from shared.auth.dependencies import ActiveUser, get_db, require_permissions
from shared.models.user import User, UserStatus
from shared.schemas.user import (
    UserResponse,
    UserUpdate,
    UserStatusUpdate,
)
from shared.schemas.base import SuccessResponse

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: ActiveUser):
    """Get current user profile."""
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_current_user_profile(
    data: UserUpdate,
    current_user: ActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update current user profile."""
    update_data = data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        if hasattr(current_user, field):
            setattr(current_user, field, value)

    await db.commit()
    await db.refresh(current_user)

    return current_user


@router.patch("/me/status", response_model=UserResponse)
async def update_current_user_status(
    data: UserStatusUpdate,
    current_user: ActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update current user's online status."""
    current_user.status = data.status
    await db.commit()
    await db.refresh(current_user)

    return current_user


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    current_user: Annotated[User, Depends(require_permissions("team:read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get user by ID."""
    result = await db.execute(
        select(User)
        .where(User.id == user_id)
        .where(User.tenant_id == current_user.tenant_id)
        .options(
            selectinload(User.roles),
            selectinload(User.department_memberships),
            selectinload(User.skills),
        )
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
        )

    return user


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    data: UserUpdate,
    current_user: Annotated[User, Depends(require_permissions("team:manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update user by ID."""
    result = await db.execute(
        select(User)
        .where(User.id == user_id)
        .where(User.tenant_id == current_user.tenant_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
        )

    update_data = data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        if hasattr(user, field):
            setattr(user, field, value)

    await db.commit()
    await db.refresh(user)

    return user


@router.delete("/{user_id}", response_model=SuccessResponse)
async def delete_user(
    user_id: UUID,
    current_user: Annotated[User, Depends(require_permissions("team:manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Deactivate user by ID."""
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя деактивировать собственный аккаунт",
        )

    result = await db.execute(
        select(User)
        .where(User.id == user_id)
        .where(User.tenant_id == current_user.tenant_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
        )

    user.is_active = False
    await db.commit()

    return SuccessResponse(message="Пользователь деактивирован")
