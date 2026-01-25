"""Department model."""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.models.base import BaseModel

if TYPE_CHECKING:
    from shared.models.tenant import Tenant
    from shared.models.user import User


class Department(BaseModel):
    """Department model."""

    __tablename__ = "departments"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    color: Mapped[str | None] = mapped_column(String(7))  # Hex color
    icon: Mapped[str | None] = mapped_column(String(50))

    # Settings
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")

    # Parent department (for hierarchy)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id", ondelete="SET NULL")
    )

    # Relationships
    parent: Mapped["Department | None"] = relationship(
        "Department", remote_side="Department.id", back_populates="children"
    )
    children: Mapped[list["Department"]] = relationship("Department", back_populates="parent")
    members: Mapped[list["DepartmentMember"]] = relationship(
        "DepartmentMember", back_populates="department", cascade="all, delete-orphan"
    )

    __table_args__ = (UniqueConstraint("tenant_id", "name", name="uq_department_tenant_name"),)

    def __repr__(self) -> str:
        return f"<Department {self.name}>"


class DepartmentMember(BaseModel):
    """Department membership."""

    __tablename__ = "department_members"

    department_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    # Role within department
    is_manager: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")

    # Relationships
    department: Mapped["Department"] = relationship("Department", back_populates="members")
    user: Mapped["User"] = relationship("User", back_populates="department_memberships")

    __table_args__ = (UniqueConstraint("department_id", "user_id", name="uq_department_member"),)
