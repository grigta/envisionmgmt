"""Superadmin services module."""

from services.superadmin.service import (
    SuperadminService,
    get_superadmin_service,
)

__all__ = [
    "SuperadminService",
    "get_superadmin_service",
]
