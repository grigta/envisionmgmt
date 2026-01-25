"""Pydantic schemas for API validation and serialization."""

from shared.schemas.base import BaseSchema, PaginatedResponse
from shared.schemas.auth import (
    TokenResponse,
    LoginRequest,
    RegisterRequest,
    RefreshTokenRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    ChangePasswordRequest,
    TwoFactorEnableResponse,
    TwoFactorVerifyRequest,
)
from shared.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserListResponse,
    InviteUserRequest,
    AcceptInviteRequest,
)
from shared.schemas.tenant import (
    TenantCreate,
    TenantUpdate,
    TenantResponse,
    TenantSettingsUpdate,
    BusinessHoursUpdate,
    BrandingUpdate,
)
from shared.schemas.customer import (
    CustomerCreate,
    CustomerUpdate,
    CustomerResponse,
    CustomerListResponse,
    CustomerNoteCreate,
    CustomerMergeRequest,
)
from shared.schemas.conversation import (
    ConversationCreate,
    ConversationUpdate,
    ConversationResponse,
    ConversationListResponse,
    MessageCreate,
    MessageResponse,
    AssignConversationRequest,
    TransferConversationRequest,
)

__all__ = [
    # Base
    "BaseSchema",
    "PaginatedResponse",
    # Auth
    "TokenResponse",
    "LoginRequest",
    "RegisterRequest",
    "RefreshTokenRequest",
    "ForgotPasswordRequest",
    "ResetPasswordRequest",
    "ChangePasswordRequest",
    "TwoFactorEnableResponse",
    "TwoFactorVerifyRequest",
    # User
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserListResponse",
    "InviteUserRequest",
    "AcceptInviteRequest",
    # Tenant
    "TenantCreate",
    "TenantUpdate",
    "TenantResponse",
    "TenantSettingsUpdate",
    "BusinessHoursUpdate",
    "BrandingUpdate",
    # Customer
    "CustomerCreate",
    "CustomerUpdate",
    "CustomerResponse",
    "CustomerListResponse",
    "CustomerNoteCreate",
    "CustomerMergeRequest",
    # Conversation
    "ConversationCreate",
    "ConversationUpdate",
    "ConversationResponse",
    "ConversationListResponse",
    "MessageCreate",
    "MessageResponse",
    "AssignConversationRequest",
    "TransferConversationRequest",
]
