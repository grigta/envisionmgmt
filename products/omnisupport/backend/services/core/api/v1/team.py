"""Team management endpoints (members, departments, skills, roles)."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from shared.auth.dependencies import ActiveUser, get_db, require_permissions
from shared.auth.jwt import create_invite_token, decode_special_token
from shared.auth.password import hash_password
from shared.models.user import User, Role, UserRole
from shared.models.department import Department, DepartmentMember
from shared.models.skill import Skill, UserSkill
from shared.schemas.user import (
    UserCreate,
    UserResponse,
    UserListResponse,
    InviteUserRequest,
    AcceptInviteRequest,
)
from shared.schemas.base import SuccessResponse, PaginatedResponse

router = APIRouter()


# ==================== Members ====================

@router.get("/members", response_model=UserListResponse)
async def list_members(
    current_user: Annotated[User, Depends(require_permissions("team:read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = None,
    department_id: UUID | None = None,
    is_active: bool | None = None,
):
    """List team members."""
    query = (
        select(User)
        .where(User.tenant_id == current_user.tenant_id)
        .options(
            selectinload(User.roles),
            selectinload(User.department_memberships),
            selectinload(User.skills),
        )
    )

    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            (User.email.ilike(search_pattern))
            | (User.first_name.ilike(search_pattern))
            | (User.last_name.ilike(search_pattern))
        )

    if department_id:
        query = query.join(DepartmentMember).where(
            DepartmentMember.department_id == department_id
        )

    if is_active is not None:
        query = query.where(User.is_active == is_active)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Apply pagination
    query = query.offset((page - 1) * page_size).limit(page_size)
    query = query.order_by(User.created_at.desc())

    result = await db.execute(query)
    users = list(result.scalars().all())

    return PaginatedResponse.create(
        items=users,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/invite", response_model=SuccessResponse)
async def invite_member(
    data: InviteUserRequest,
    current_user: Annotated[User, Depends(require_permissions("team:manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Invite a new team member."""
    # Check if email already exists in tenant
    result = await db.execute(
        select(User)
        .where(User.email == data.email)
        .where(User.tenant_id == current_user.tenant_id)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email уже существует",
        )

    # Create invite token
    role_ids = [str(r) for r in (data.role_ids or [])]
    token = create_invite_token(
        email=data.email,
        tenant_id=current_user.tenant_id,
        role_ids=role_ids,
    )

    # TODO: Send invite email with token
    # await send_invite_email(data.email, token, current_user.tenant.name)

    return SuccessResponse(message="Приглашение отправлено")


@router.post("/invite/{token}/accept", response_model=UserResponse)
async def accept_invite(
    token: str,
    data: AcceptInviteRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Accept team invitation."""
    payload = decode_special_token(token, "invite")

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Недействительное или истёкшее приглашение",
        )

    tenant_id = UUID(payload["tenant_id"])
    email = payload["email"]
    role_ids = [UUID(r) for r in payload.get("role_ids", [])]

    # Check if user already exists
    result = await db.execute(
        select(User)
        .where(User.email == email)
        .where(User.tenant_id == tenant_id)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь уже зарегистрирован",
        )

    # Create user
    user = User(
        tenant_id=tenant_id,
        email=email,
        password_hash=hash_password(data.password),
        first_name=data.first_name,
        last_name=data.last_name,
        email_verified=True,
    )
    db.add(user)
    await db.flush()

    # Assign roles
    for role_id in role_ids:
        user_role = UserRole(user_id=user.id, role_id=role_id)
        db.add(user_role)

    await db.commit()
    await db.refresh(user)

    return user


# ==================== Departments ====================

@router.get("/departments")
async def list_departments(
    current_user: Annotated[User, Depends(require_permissions("team:read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """List all departments."""
    result = await db.execute(
        select(Department)
        .where(Department.tenant_id == current_user.tenant_id)
        .options(selectinload(Department.members))
        .order_by(Department.name)
    )
    departments = list(result.scalars().all())

    return {"items": departments, "total": len(departments)}


@router.post("/departments")
async def create_department(
    current_user: Annotated[User, Depends(require_permissions("team:manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    name: str,
    description: str | None = None,
    color: str | None = None,
    parent_id: UUID | None = None,
):
    """Create a new department."""
    department = Department(
        tenant_id=current_user.tenant_id,
        name=name,
        description=description,
        color=color,
        parent_id=parent_id,
    )
    db.add(department)
    await db.commit()
    await db.refresh(department)

    return department


@router.patch("/departments/{department_id}")
async def update_department(
    department_id: UUID,
    current_user: Annotated[User, Depends(require_permissions("team:manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    name: str | None = None,
    description: str | None = None,
    color: str | None = None,
    is_active: bool | None = None,
):
    """Update a department."""
    result = await db.execute(
        select(Department)
        .where(Department.id == department_id)
        .where(Department.tenant_id == current_user.tenant_id)
    )
    department = result.scalar_one_or_none()

    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Отдел не найден",
        )

    if name is not None:
        department.name = name
    if description is not None:
        department.description = description
    if color is not None:
        department.color = color
    if is_active is not None:
        department.is_active = is_active

    await db.commit()
    await db.refresh(department)

    return department


@router.delete("/departments/{department_id}", response_model=SuccessResponse)
async def delete_department(
    department_id: UUID,
    current_user: Annotated[User, Depends(require_permissions("team:manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete a department."""
    result = await db.execute(
        select(Department)
        .where(Department.id == department_id)
        .where(Department.tenant_id == current_user.tenant_id)
    )
    department = result.scalar_one_or_none()

    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Отдел не найден",
        )

    await db.delete(department)
    await db.commit()

    return SuccessResponse(message="Отдел удалён")


# ==================== Skills ====================

@router.get("/skills")
async def list_skills(
    current_user: Annotated[User, Depends(require_permissions("team:read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """List all skills."""
    result = await db.execute(
        select(Skill)
        .where(Skill.tenant_id == current_user.tenant_id)
        .order_by(Skill.name)
    )
    skills = list(result.scalars().all())

    return {"items": skills, "total": len(skills)}


@router.post("/skills")
async def create_skill(
    current_user: Annotated[User, Depends(require_permissions("team:manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    name: str,
    description: str | None = None,
    color: str | None = None,
):
    """Create a new skill."""
    skill = Skill(
        tenant_id=current_user.tenant_id,
        name=name,
        description=description,
        color=color,
    )
    db.add(skill)
    await db.commit()
    await db.refresh(skill)

    return skill


@router.delete("/skills/{skill_id}", response_model=SuccessResponse)
async def delete_skill(
    skill_id: UUID,
    current_user: Annotated[User, Depends(require_permissions("team:manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete a skill."""
    result = await db.execute(
        select(Skill)
        .where(Skill.id == skill_id)
        .where(Skill.tenant_id == current_user.tenant_id)
    )
    skill = result.scalar_one_or_none()

    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Навык не найден",
        )

    await db.delete(skill)
    await db.commit()

    return SuccessResponse(message="Навык удалён")


# ==================== Roles ====================

@router.get("/roles")
async def list_roles(
    current_user: Annotated[User, Depends(require_permissions("team:read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """List all roles."""
    result = await db.execute(
        select(Role)
        .where(
            (Role.tenant_id == current_user.tenant_id) | (Role.tenant_id.is_(None))
        )
        .order_by(Role.name)
    )
    roles = list(result.scalars().all())

    return {"items": roles, "total": len(roles)}


@router.post("/roles")
async def create_role(
    current_user: Annotated[User, Depends(require_permissions("team:manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    name: str,
    description: str | None = None,
    permissions: list[str] | None = None,
):
    """Create a new role."""
    role = Role(
        tenant_id=current_user.tenant_id,
        name=name,
        description=description,
        permissions=permissions or [],
    )
    db.add(role)
    await db.commit()
    await db.refresh(role)

    return role


@router.patch("/roles/{role_id}")
async def update_role(
    role_id: UUID,
    current_user: Annotated[User, Depends(require_permissions("team:manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    name: str | None = None,
    description: str | None = None,
    permissions: list[str] | None = None,
):
    """Update a role."""
    result = await db.execute(
        select(Role)
        .where(Role.id == role_id)
        .where(Role.tenant_id == current_user.tenant_id)
    )
    role = result.scalar_one_or_none()

    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Роль не найдена",
        )

    if role.is_system:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Системную роль нельзя изменить",
        )

    if name is not None:
        role.name = name
    if description is not None:
        role.description = description
    if permissions is not None:
        role.permissions = permissions

    await db.commit()
    await db.refresh(role)

    return role


@router.delete("/roles/{role_id}", response_model=SuccessResponse)
async def delete_role(
    role_id: UUID,
    current_user: Annotated[User, Depends(require_permissions("team:manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete a role."""
    result = await db.execute(
        select(Role)
        .where(Role.id == role_id)
        .where(Role.tenant_id == current_user.tenant_id)
    )
    role = result.scalar_one_or_none()

    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Роль не найдена",
        )

    if role.is_system:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Системную роль нельзя удалить",
        )

    await db.delete(role)
    await db.commit()

    return SuccessResponse(message="Роль удалена")
