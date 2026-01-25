"""User schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import EmailStr, Field

from shared.models.user import UserStatus
from shared.schemas.base import BaseSchema, PaginatedResponse


class UserBase(BaseSchema):
    """Base user schema."""

    email: EmailStr
    first_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)
    phone: str | None = Field(default=None, max_length=50)
    avatar_url: str | None = Field(default=None, max_length=500)


class UserCreate(UserBase):
    """Create user schema."""

    password: str = Field(min_length=8, max_length=100)
    role_ids: list[UUID] | None = None
    department_ids: list[UUID] | None = None
    skill_ids: list[UUID] | None = None


class UserUpdate(BaseSchema):
    """Update user schema."""

    first_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)
    phone: str | None = Field(default=None, max_length=50)
    avatar_url: str | None = Field(default=None, max_length=500)
    is_active: bool | None = None
    max_concurrent_chats: int | None = Field(default=None, ge=1, le=50)


class UserResponse(UserBase):
    """User response schema."""

    id: UUID
    tenant_id: UUID
    status: UserStatus
    is_active: bool
    email_verified: bool
    two_factor_enabled: bool
    max_concurrent_chats: int | None
    last_activity_at: datetime | None
    created_at: datetime
    updated_at: datetime

    # Computed
    full_name: str
    roles: list["RoleResponse"] = []
    departments: list["DepartmentBriefResponse"] = []
    skills: list["SkillBriefResponse"] = []


class UserListResponse(PaginatedResponse[UserResponse]):
    """Paginated user list response."""

    pass


class RoleResponse(BaseSchema):
    """Role response schema."""

    id: UUID
    name: str
    description: str | None
    permissions: list[str]
    is_system: bool


class DepartmentBriefResponse(BaseSchema):
    """Brief department response."""

    id: UUID
    name: str
    color: str | None


class SkillBriefResponse(BaseSchema):
    """Brief skill response."""

    id: UUID
    name: str
    level: int


class InviteUserRequest(BaseSchema):
    """Invite user request."""

    email: EmailStr
    first_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)
    role_ids: list[UUID] | None = None
    department_ids: list[UUID] | None = None


class AcceptInviteRequest(BaseSchema):
    """Accept invite request."""

    password: str = Field(min_length=8, max_length=100)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)


class UserStatusUpdate(BaseSchema):
    """Update user status."""

    status: UserStatus
