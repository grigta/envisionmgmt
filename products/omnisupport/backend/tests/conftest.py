"""Pytest configuration and fixtures for OmniSupport API tests."""

import asyncio
from collections.abc import AsyncGenerator
from typing import Any
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from shared.auth.jwt import create_access_token
from shared.auth.password import hash_password
from shared.database import Base, get_db
from shared.models.tenant import Tenant
from shared.models.user import User, Role, UserRole
from shared.models.customer import Customer
from shared.models.conversation import Conversation, ChannelType, Message, SenderType, ContentType

# Import the FastAPI app
from services.core.main import app

# Test database URL - use SQLite for tests or override with env var
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for the test session."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture
async def db_session(engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for each test."""
    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test HTTP client with overridden dependencies."""
    
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture
async def test_tenant(db_session: AsyncSession) -> Tenant:
    """Create a test tenant."""
    tenant = Tenant(
        id=uuid4(),
        name="Test Company",
        slug="test-company",
        email="admin@test.com",
        is_active=True,
    )
    db_session.add(tenant)
    await db_session.commit()
    await db_session.refresh(tenant)
    return tenant


@pytest.fixture
async def test_role(db_session: AsyncSession, test_tenant: Tenant) -> Role:
    """Create a test admin role."""
    role = Role(
        id=uuid4(),
        tenant_id=test_tenant.id,
        name="Администратор",
        description="Full access",
        is_system=True,
        permissions=["*"],
    )
    db_session.add(role)
    await db_session.commit()
    await db_session.refresh(role)
    return role


@pytest.fixture
async def test_user(db_session: AsyncSession, test_tenant: Tenant, test_role: Role) -> User:
    """Create a test user with admin permissions."""
    user = User(
        id=uuid4(),
        tenant_id=test_tenant.id,
        email="testuser@test.com",
        password_hash=hash_password("TestPassword123"),
        first_name="Test",
        last_name="User",
        is_active=True,
        email_verified=True,
    )
    db_session.add(user)
    await db_session.flush()
    
    # Assign role
    user_role = UserRole(user_id=user.id, role_id=test_role.id)
    db_session.add(user_role)
    
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_customer(db_session: AsyncSession, test_tenant: Tenant) -> Customer:
    """Create a test customer."""
    customer = Customer(
        id=uuid4(),
        tenant_id=test_tenant.id,
        email="customer@example.com",
        name="Test Customer",
        phone="+79001234567",
    )
    db_session.add(customer)
    await db_session.commit()
    await db_session.refresh(customer)
    return customer


@pytest.fixture
async def test_conversation(
    db_session: AsyncSession,
    test_tenant: Tenant,
    test_customer: Customer,
    test_user: User,
) -> Conversation:
    """Create a test conversation."""
    conversation = Conversation(
        id=uuid4(),
        tenant_id=test_tenant.id,
        customer_id=test_customer.id,
        channel=ChannelType.WIDGET,
        subject="Test Conversation",
        assigned_to=test_user.id,
    )
    db_session.add(conversation)
    await db_session.commit()
    await db_session.refresh(conversation)
    return conversation


@pytest.fixture
async def test_message(
    db_session: AsyncSession,
    test_conversation: Conversation,
    test_user: User,
) -> Message:
    """Create a test message."""
    message = Message(
        id=uuid4(),
        conversation_id=test_conversation.id,
        sender_type=SenderType.OPERATOR,
        sender_id=test_user.id,
        content_type=ContentType.TEXT,
        content={"text": "Hello, how can I help you?"},
    )
    db_session.add(message)
    await db_session.commit()
    await db_session.refresh(message)
    return message


@pytest.fixture
def auth_headers(test_user: User, test_tenant: Tenant) -> dict[str, str]:
    """Create authorization headers with a valid JWT token."""
    access_token = create_access_token(
        user_id=test_user.id,
        tenant_id=test_tenant.id,
        permissions=["*"],
    )
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def api_prefix() -> str:
    """API v1 prefix."""
    return "/api/v1"
