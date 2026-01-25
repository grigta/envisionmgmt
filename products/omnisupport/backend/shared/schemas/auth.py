"""Authentication schemas."""

from pydantic import EmailStr, Field

from shared.schemas.base import BaseSchema


class LoginRequest(BaseSchema):
    """Login request."""

    email: EmailStr
    password: str = Field(min_length=1)
    two_factor_code: str | None = None


class RegisterRequest(BaseSchema):
    """Registration request."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=100)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)
    company_name: str = Field(min_length=1, max_length=255)


class TokenResponse(BaseSchema):
    """Token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class RefreshTokenRequest(BaseSchema):
    """Refresh token request."""

    refresh_token: str


class ForgotPasswordRequest(BaseSchema):
    """Forgot password request."""

    email: EmailStr


class ResetPasswordRequest(BaseSchema):
    """Reset password request."""

    token: str
    password: str = Field(min_length=8, max_length=100)


class ChangePasswordRequest(BaseSchema):
    """Change password request."""

    current_password: str
    new_password: str = Field(min_length=8, max_length=100)


class TwoFactorEnableResponse(BaseSchema):
    """Two-factor enable response."""

    secret: str
    qr_code_url: str
    backup_codes: list[str]


class TwoFactorVerifyRequest(BaseSchema):
    """Two-factor verification request."""

    code: str = Field(min_length=6, max_length=6)


class TwoFactorDisableRequest(BaseSchema):
    """Two-factor disable request."""

    password: str
    code: str = Field(min_length=6, max_length=6)
