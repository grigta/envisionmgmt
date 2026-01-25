"""JWT token utilities."""

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from jose import JWTError, jwt
from pydantic import BaseModel

from shared.config import get_settings

settings = get_settings()


class TokenPayload(BaseModel):
    """JWT token payload."""

    sub: str  # user_id
    tenant_id: str
    type: str  # "access" or "refresh"
    exp: datetime
    iat: datetime
    permissions: list[str] = []


def create_access_token(
    user_id: UUID,
    tenant_id: UUID,
    permissions: list[str] | None = None,
    expires_delta: timedelta | None = None,
) -> str:
    """Create JWT access token."""
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.access_token_expire_minutes)

    now = datetime.now(timezone.utc)
    expire = now + expires_delta

    payload = {
        "sub": str(user_id),
        "tenant_id": str(tenant_id),
        "type": "access",
        "permissions": permissions or [],
        "exp": expire,
        "iat": now,
    }

    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(
    user_id: UUID,
    tenant_id: UUID,
    expires_delta: timedelta | None = None,
) -> str:
    """Create JWT refresh token."""
    if expires_delta is None:
        expires_delta = timedelta(days=settings.refresh_token_expire_days)

    now = datetime.now(timezone.utc)
    expire = now + expires_delta

    payload = {
        "sub": str(user_id),
        "tenant_id": str(tenant_id),
        "type": "refresh",
        "exp": expire,
        "iat": now,
    }

    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> TokenPayload | None:
    """Decode and validate JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return TokenPayload(**payload)
    except JWTError:
        return None


def create_email_verification_token(user_id: UUID, email: str) -> str:
    """Create email verification token."""
    now = datetime.now(timezone.utc)
    expire = now + timedelta(hours=24)

    payload = {
        "sub": str(user_id),
        "email": email,
        "type": "email_verification",
        "exp": expire,
        "iat": now,
    }

    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_password_reset_token(user_id: UUID, email: str) -> str:
    """Create password reset token."""
    now = datetime.now(timezone.utc)
    expire = now + timedelta(hours=1)

    payload = {
        "sub": str(user_id),
        "email": email,
        "type": "password_reset",
        "exp": expire,
        "iat": now,
    }

    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_invite_token(email: str, tenant_id: UUID, role_ids: list[str]) -> str:
    """Create user invitation token."""
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=7)

    payload = {
        "email": email,
        "tenant_id": str(tenant_id),
        "role_ids": role_ids,
        "type": "invite",
        "exp": expire,
        "iat": now,
    }

    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_special_token(token: str, expected_type: str) -> dict[str, Any] | None:
    """Decode special tokens (email verification, password reset, invite)."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        if payload.get("type") != expected_type:
            return None
        return payload
    except JWTError:
        return None
