"""Tests for conversation endpoints."""

import pytest
from httpx import AsyncClient
from uuid import uuid4

from shared.models.conversation import Conversation, ChannelType, ConversationStatus
from shared.models.customer import Customer
from shared.models.user import User


class TestListConversations:
    """Tests for list conversations endpoint."""

    @pytest.mark.asyncio
    async def test_list_conversations_success(
        self,
        client: AsyncClient,
        api_prefix: str,
        auth_headers: dict,
        test_conversation: Conversation,
    ):
        """Test listing conversations returns data."""
        response = await client.get(
            f"{api_prefix}/conversations",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert len(data["items"]) >= 1

    @pytest.mark.asyncio
    async def test_list_conversations_pagination(
        self,
        client: AsyncClient,
        api_prefix: str,
        auth_headers: dict,
        test_conversation: Conversation,
    ):
        """Test conversations pagination works."""
        response = await client.get(
            f"{api_prefix}/conversations",
            headers=auth_headers,
            params={"page": 1, "page_size": 5},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 5

    @pytest.mark.asyncio
    async def test_list_conversations_filter_by_status(
        self,
        client: AsyncClient,
        api_prefix: str,
        auth_headers: dict,
        test_conversation: Conversation,
    ):
        """Test filtering conversations by status."""
        response = await client.get(
            f"{api_prefix}/conversations",
            headers=auth_headers,
            params={"status": "open"},
        )
        
        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["status"] == "open"

    @pytest.mark.asyncio
    async def test_list_conversations_filter_by_channel(
        self,
        client: AsyncClient,
        api_prefix: str,
        auth_headers: dict,
        test_conversation: Conversation,
    ):
        """Test filtering conversations by channel."""
        response = await client.get(
            f"{api_prefix}/conversations",
            headers=auth_headers,
            params={"channel": "widget"},
        )
        
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_list_conversations_unauthorized(
        self, client: AsyncClient, api_prefix: str
    ):
        """Test listing conversations without auth fails."""
        response = await client.get(f"{api_prefix}/conversations")
        
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_list_conversations_search(
        self,
        client: AsyncClient,
        api_prefix: str,
        auth_headers: dict,
        test_conversation: Conversation,
    ):
        """Test searching conversations."""
        response = await client.get(
            f"{api_prefix}/conversations",
            headers=auth_headers,
            params={"search": "Test"},
        )
        
        assert response.status_code == 200


class TestCreateConversation:
    """Tests for create conversation endpoint."""

    @pytest.mark.asyncio
    async def test_create_conversation_success(
        self,
        client: AsyncClient,
        api_prefix: str,
        auth_headers: dict,
        test_customer: Customer,
    ):
        """Test creating a new conversation."""
        response = await client.post(
            f"{api_prefix}/conversations",
            headers=auth_headers,
            json={
                "customer_id": str(test_customer.id),
                "channel": "widget",
                "subject": "New Test Conversation",
                "tags": ["test", "api"],
                "priority": "normal",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["subject"] == "New Test Conversation"
        assert data["channel"] == "widget"
        assert data["customer_id"] == str(test_customer.id)
        assert "test" in data["tags"]

    @pytest.mark.asyncio
    async def test_create_conversation_with_assignment(
        self,
        client: AsyncClient,
        api_prefix: str,
        auth_headers: dict,
        test_customer: Customer,
        test_user: User,
    ):
        """Test creating conversation with operator assignment."""
        response = await client.post(
            f"{api_prefix}/conversations",
            headers=auth_headers,
            json={
                "customer_id": str(test_customer.id),
                "channel": "telegram",
                "assigned_to": str(test_user.id),
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["assigned_to"] == str(test_user.id)

    @pytest.mark.asyncio
    async def test_create_conversation_invalid_customer(
        self,
        client: AsyncClient,
        api_prefix: str,
        auth_headers: dict,
    ):
        """Test creating conversation with non-existent customer fails."""
        response = await client.post(
            f"{api_prefix}/conversations",
            headers=auth_headers,
            json={
                "customer_id": str(uuid4()),  # Non-existent
                "channel": "widget",
            },
        )
        
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_conversation_missing_required_fields(
        self,
        client: AsyncClient,
        api_prefix: str,
        auth_headers: dict,
    ):
        """Test creating conversation without required fields fails."""
        response = await client.post(
            f"{api_prefix}/conversations",
            headers=auth_headers,
            json={
                "subject": "Test",  # Missing customer_id and channel
            },
        )
        
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_conversation_unauthorized(
        self, client: AsyncClient, api_prefix: str, test_customer: Customer
    ):
        """Test creating conversation without auth fails."""
        response = await client.post(
            f"{api_prefix}/conversations",
            json={
                "customer_id": str(test_customer.id),
                "channel": "widget",
            },
        )
        
        assert response.status_code == 403


class TestGetConversation:
    """Tests for get conversation by ID endpoint."""

    @pytest.mark.asyncio
    async def test_get_conversation_success(
        self,
        client: AsyncClient,
        api_prefix: str,
        auth_headers: dict,
        test_conversation: Conversation,
    ):
        """Test getting conversation by ID."""
        response = await client.get(
            f"{api_prefix}/conversations/{test_conversation.id}",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_conversation.id)
        assert data["subject"] == test_conversation.subject

    @pytest.mark.asyncio
    async def test_get_conversation_not_found(
        self,
        client: AsyncClient,
        api_prefix: str,
        auth_headers: dict,
    ):
        """Test getting non-existent conversation returns 404."""
        response = await client.get(
            f"{api_prefix}/conversations/{uuid4()}",
            headers=auth_headers,
        )
        
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_conversation_unauthorized(
        self, client: AsyncClient, api_prefix: str, test_conversation: Conversation
    ):
        """Test getting conversation without auth fails."""
        response = await client.get(
            f"{api_prefix}/conversations/{test_conversation.id}"
        )
        
        assert response.status_code == 403


class TestUpdateConversation:
    """Tests for update conversation endpoint."""

    @pytest.mark.asyncio
    async def test_update_conversation_subject(
        self,
        client: AsyncClient,
        api_prefix: str,
        auth_headers: dict,
        test_conversation: Conversation,
    ):
        """Test updating conversation subject."""
        response = await client.patch(
            f"{api_prefix}/conversations/{test_conversation.id}",
            headers=auth_headers,
            json={"subject": "Updated Subject"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["subject"] == "Updated Subject"

    @pytest.mark.asyncio
    async def test_update_conversation_tags(
        self,
        client: AsyncClient,
        api_prefix: str,
        auth_headers: dict,
        test_conversation: Conversation,
    ):
        """Test updating conversation tags."""
        response = await client.patch(
            f"{api_prefix}/conversations/{test_conversation.id}",
            headers=auth_headers,
            json={"tags": ["urgent", "vip"]},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "urgent" in data["tags"]
        assert "vip" in data["tags"]

    @pytest.mark.asyncio
    async def test_update_conversation_priority(
        self,
        client: AsyncClient,
        api_prefix: str,
        auth_headers: dict,
        test_conversation: Conversation,
    ):
        """Test updating conversation priority."""
        response = await client.patch(
            f"{api_prefix}/conversations/{test_conversation.id}",
            headers=auth_headers,
            json={"priority": "high"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["priority"] == "high"

    @pytest.mark.asyncio
    async def test_update_conversation_not_found(
        self,
        client: AsyncClient,
        api_prefix: str,
        auth_headers: dict,
    ):
        """Test updating non-existent conversation returns 404."""
        response = await client.patch(
            f"{api_prefix}/conversations/{uuid4()}",
            headers=auth_headers,
            json={"subject": "Test"},
        )
        
        assert response.status_code == 404


class TestConversationActions:
    """Tests for conversation action endpoints (assign, resolve, close, etc.)."""

    @pytest.mark.asyncio
    async def test_assign_conversation(
        self,
        client: AsyncClient,
        api_prefix: str,
        auth_headers: dict,
        test_conversation: Conversation,
        test_user: User,
    ):
        """Test assigning conversation to operator."""
        response = await client.post(
            f"{api_prefix}/conversations/{test_conversation.id}/assign",
            headers=auth_headers,
            json={"operator_id": str(test_user.id)},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["assigned_to"] == str(test_user.id)

    @pytest.mark.asyncio
    async def test_resolve_conversation(
        self,
        client: AsyncClient,
        api_prefix: str,
        auth_headers: dict,
        test_conversation: Conversation,
    ):
        """Test resolving conversation."""
        response = await client.post(
            f"{api_prefix}/conversations/{test_conversation.id}/resolve",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "resolved"

    @pytest.mark.asyncio
    async def test_close_conversation(
        self,
        client: AsyncClient,
        api_prefix: str,
        auth_headers: dict,
        test_conversation: Conversation,
    ):
        """Test closing conversation."""
        response = await client.post(
            f"{api_prefix}/conversations/{test_conversation.id}/close",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "closed"

    @pytest.mark.asyncio
    async def test_reopen_conversation(
        self,
        client: AsyncClient,
        api_prefix: str,
        auth_headers: dict,
        test_conversation: Conversation,
    ):
        """Test reopening closed conversation."""
        # First close it
        await client.post(
            f"{api_prefix}/conversations/{test_conversation.id}/close",
            headers=auth_headers,
        )
        
        # Then reopen
        response = await client.post(
            f"{api_prefix}/conversations/{test_conversation.id}/reopen",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "open"

    @pytest.mark.asyncio
    async def test_transfer_conversation(
        self,
        client: AsyncClient,
        api_prefix: str,
        auth_headers: dict,
        test_conversation: Conversation,
        test_user: User,
    ):
        """Test transferring conversation with note."""
        response = await client.post(
            f"{api_prefix}/conversations/{test_conversation.id}/transfer",
            headers=auth_headers,
            json={
                "operator_id": str(test_user.id),
                "note": "Transferring for expertise",
            },
        )
        
        assert response.status_code == 200
