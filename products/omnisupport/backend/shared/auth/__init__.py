"""Authentication module."""

from shared.auth.jwt import (
    create_access_token,
    create_refresh_token,
    decode_token,
    TokenPayload,
)
from shared.auth.password import (
    hash_password,
    verify_password,
)
from shared.auth.two_factor import (
    generate_totp_secret,
    verify_totp_code,
    generate_qr_code_url,
    generate_backup_codes,
)
from shared.auth.dependencies import (
    get_current_user,
    get_current_active_user,
    get_current_tenant,
    require_permissions,
)

__all__ = [
    # JWT
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "TokenPayload",
    # Password
    "hash_password",
    "verify_password",
    # 2FA
    "generate_totp_secret",
    "verify_totp_code",
    "generate_qr_code_url",
    "generate_backup_codes",
    # Dependencies
    "get_current_user",
    "get_current_active_user",
    "get_current_tenant",
    "require_permissions",
]
