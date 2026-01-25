"""User, Role, and Permission models."""

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.models.base import BaseModel

if TYPE_CHECKING:
    from shared.models.tenant import Tenant
    from shared.models.department import DepartmentMember
    from shared.models.skill import UserSkill
    from shared.models.conversation import Conversation


class UserStatus(str, enum.Enum):
    """User online status."""

    ONLINE = "online"
    OFFLINE = "offline"
    AWAY = "away"
    BUSY = "busy"


class User(BaseModel):
    """User model (operators, admins, viewers)."""

    __tablename__ = "users"

    # Tenant
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Basic info
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String(255))
    first_name: Mapped[str | None] = mapped_column(String(100))
    last_name: Mapped[str | None] = mapped_column(String(100))
    avatar_url: Mapped[str | None] = mapped_column(String(500))
    phone: Mapped[str | None] = mapped_column(String(50))

    # Status
    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus), default=UserStatus.OFFLINE, server_default="offline"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    # Email verification
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    email_verification_token: Mapped[str | None] = mapped_column(String(255))
    email_verification_expires: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Password reset
    password_reset_token: Mapped[str | None] = mapped_column(String(255))
    password_reset_expires: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Two-factor auth
    two_factor_enabled: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    two_factor_secret: Mapped[str | None] = mapped_column(String(255))

    # Refresh tokens (JSON array of token hashes)
    refresh_tokens: Mapped[list] = mapped_column(JSONB, default=list, server_default="[]")

    # Settings
    settings: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")
    notification_preferences: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")

    # Operator-specific
    max_concurrent_chats: Mapped[int | None] = mapped_column(default=5)
    last_activity_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Push notification tokens [{platform: "fcm"|"apns"|"web", token: str, ...}]
    push_tokens: Mapped[list] = mapped_column(JSONB, default=list, server_default="[]")

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="users")
    roles: Mapped[list["UserRole"]] = relationship(
        "UserRole", back_populates="user", cascade="all, delete-orphan"
    )
    department_memberships: Mapped[list["DepartmentMember"]] = relationship(
        "DepartmentMember", back_populates="user", cascade="all, delete-orphan"
    )
    skills: Mapped[list["UserSkill"]] = relationship(
        "UserSkill", back_populates="user", cascade="all, delete-orphan"
    )
    assigned_conversations: Mapped[list["Conversation"]] = relationship(
        "Conversation", back_populates="assigned_to_user", foreign_keys="Conversation.assigned_to"
    )

    __table_args__ = (UniqueConstraint("tenant_id", "email", name="uq_user_tenant_email"),)

    @property
    def full_name(self) -> str:
        """Get user's full name."""
        parts = [self.first_name, self.last_name]
        return " ".join(p for p in parts if p) or self.email

    @property
    def is_online(self) -> bool:
        """Check if user is online."""
        return self.status in (UserStatus.ONLINE, UserStatus.BUSY)

    def __repr__(self) -> str:
        return f"<User {self.email}>"


class Permission(BaseModel):
    """Permission model."""

    __tablename__ = "permissions"

    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str | None] = mapped_column(String(100))

    def __repr__(self) -> str:
        return f"<Permission {self.code}>"


class Role(BaseModel):
    """Role model."""

    __tablename__ = "roles"

    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")

    # Permissions as array of permission codes
    permissions: Mapped[list] = mapped_column(ARRAY(String), default=list, server_default="{}")

    # Relationships
    user_roles: Mapped[list["UserRole"]] = relationship(
        "UserRole", back_populates="role", cascade="all, delete-orphan"
    )

    __table_args__ = (UniqueConstraint("tenant_id", "name", name="uq_role_tenant_name"),)

    def __repr__(self) -> str:
        return f"<Role {self.name}>"


class UserRole(BaseModel):
    """User-Role association."""

    __tablename__ = "user_roles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="roles")
    role: Mapped["Role"] = relationship("Role", back_populates="user_roles")

    __table_args__ = (UniqueConstraint("user_id", "role_id", name="uq_user_role"),)
