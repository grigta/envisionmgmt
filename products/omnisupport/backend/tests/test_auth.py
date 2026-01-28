"""Tests for authentication endpoints."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.user import User


class TestRegister:
    """Tests for user registration endpoint."""

    @pytest.mark.asyncio
    async def test_register_success(self, client: AsyncClient, api_prefix: str):
        """Test successful user registration."""
        response = await client.post(
            f"{api_prefix}/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "SecurePassword123",
                "first_name": "John",
                "last_name": "Doe",
                "company_name": "New Company",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] > 0

    @pytest.mark.asyncio
    async def test_register_duplicate_email(
        self, client: AsyncClient, api_prefix: str, test_user: User
    ):
        """Test registration with existing email fails."""
        response = await client.post(
            f"{api_prefix}/auth/register",
            json={
                "email": test_user.email,  # Already exists
                "password": "SecurePassword123",
                "first_name": "Another",
                "company_name": "Another Company",
            },
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "уже существует" in data["detail"].lower() or "already exists" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_register_invalid_email(self, client: AsyncClient, api_prefix: str):
        """Test registration with invalid email fails."""
        response = await client.post(
            f"{api_prefix}/auth/register",
            json={
                "email": "invalid-email",
                "password": "SecurePassword123",
                "first_name": "John",
                "company_name": "Company",
            },
        )
        
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_register_short_password(self, client: AsyncClient, api_prefix: str):
        """Test registration with too short password fails."""
        response = await client.post(
            f"{api_prefix}/auth/register",
            json={
                "email": "user@example.com",
                "password": "short",  # Less than 8 characters
                "first_name": "John",
                "company_name": "Company",
            },
        )
        
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_register_missing_required_fields(self, client: AsyncClient, api_prefix: str):
        """Test registration without required fields fails."""
        response = await client.post(
            f"{api_prefix}/auth/register",
            json={
                "email": "user@example.com",
            },
        )
        
        assert response.status_code == 422


class TestLogin:
    """Tests for user login endpoint."""

    @pytest.mark.asyncio
    async def test_login_success(
        self, client: AsyncClient, api_prefix: str, test_user: User
    ):
        """Test successful login."""
        response = await client.post(
            f"{api_prefix}/auth/login",
            json={
                "email": test_user.email,
                "password": "TestPassword123",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_wrong_password(
        self, client: AsyncClient, api_prefix: str, test_user: User
    ):
        """Test login with wrong password fails."""
        response = await client.post(
            f"{api_prefix}/auth/login",
            json={
                "email": test_user.email,
                "password": "WrongPassword123",
            },
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "неверный" in data["detail"].lower() or "invalid" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client: AsyncClient, api_prefix: str):
        """Test login with non-existent email fails."""
        response = await client.post(
            f"{api_prefix}/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "SomePassword123",
            },
        )
        
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_invalid_email_format(self, client: AsyncClient, api_prefix: str):
        """Test login with invalid email format fails."""
        response = await client.post(
            f"{api_prefix}/auth/login",
            json={
                "email": "not-an-email",
                "password": "SomePassword123",
            },
        )
        
        assert response.status_code == 422


class TestRefreshToken:
    """Tests for token refresh endpoint."""

    @pytest.mark.asyncio
    async def test_refresh_token_success(
        self, client: AsyncClient, api_prefix: str, test_user: User
    ):
        """Test successful token refresh."""
        # First login to get tokens
        login_response = await client.post(
            f"{api_prefix}/auth/login",
            json={
                "email": test_user.email,
                "password": "TestPassword123",
            },
        )
        assert login_response.status_code == 200
        refresh_token = login_response.json()["refresh_token"]
        
        # Refresh the token
        response = await client.post(
            f"{api_prefix}/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    @pytest.mark.asyncio
    async def test_refresh_token_invalid(self, client: AsyncClient, api_prefix: str):
        """Test refresh with invalid token fails."""
        response = await client.post(
            f"{api_prefix}/auth/refresh",
            json={"refresh_token": "invalid-token"},
        )
        
        assert response.status_code == 401


class TestLogout:
    """Tests for logout endpoint."""

    @pytest.mark.asyncio
    async def test_logout_success(
        self, client: AsyncClient, api_prefix: str, auth_headers: dict
    ):
        """Test successful logout."""
        response = await client.post(
            f"{api_prefix}/auth/logout",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_logout_without_auth(self, client: AsyncClient, api_prefix: str):
        """Test logout without authentication fails."""
        response = await client.post(f"{api_prefix}/auth/logout")
        
        assert response.status_code == 403  # No credentials


class TestChangePassword:
    """Tests for password change endpoint."""

    @pytest.mark.asyncio
    async def test_change_password_success(
        self, client: AsyncClient, api_prefix: str, auth_headers: dict
    ):
        """Test successful password change."""
        response = await client.post(
            f"{api_prefix}/auth/change-password",
            headers=auth_headers,
            json={
                "current_password": "TestPassword123",
                "new_password": "NewSecurePassword456",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_change_password_wrong_current(
        self, client: AsyncClient, api_prefix: str, auth_headers: dict
    ):
        """Test password change with wrong current password fails."""
        response = await client.post(
            f"{api_prefix}/auth/change-password",
            headers=auth_headers,
            json={
                "current_password": "WrongPassword",
                "new_password": "NewSecurePassword456",
            },
        )
        
        assert response.status_code == 400


class TestForgotPassword:
    """Tests for forgot password endpoint."""

    @pytest.mark.asyncio
    async def test_forgot_password_existing_email(
        self, client: AsyncClient, api_prefix: str, test_user: User
    ):
        """Test forgot password with existing email (always succeeds for security)."""
        response = await client.post(
            f"{api_prefix}/auth/forgot-password",
            json={"email": test_user.email},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_forgot_password_nonexistent_email(
        self, client: AsyncClient, api_prefix: str
    ):
        """Test forgot password with non-existent email (returns success to prevent enumeration)."""
        response = await client.post(
            f"{api_prefix}/auth/forgot-password",
            json={"email": "nonexistent@example.com"},
        )
        
        # Should still return success to prevent email enumeration
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
