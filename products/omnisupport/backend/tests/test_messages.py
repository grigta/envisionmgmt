"""Tests for message endpoints."""

import pytest
from httpx import AsyncClient
from uuid import uuid4

from shared.models.conversation import Conversation, Message, ContentType
from shared.models.user import User


class TestListMessages:
    """Tests for list conversation messages endpoint."""

    @pytest.mark.asyncio
    async def test_list_messages_success(
        self,
        client: AsyncClient,
        api_prefix: str,
        auth_headers: dict,
        test_conversation: Conversation,
        test_message: Message,
    ):
        """Test listing messages in a conversation."""
        response = await client.get(
            f"{api_prefix}/conversations/{test_conversation.id}/messages",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) >= 1

    @pytest.mark.asyncio
    async def test_list_messages_pagination(
        self,
        client: AsyncClient,
        api_prefix: str,
        auth_headers: dict,
        test_conversation: Conversation,
        test_message: Message,
    ):
        """Test messages pagination."""
        response = await client.get(
            f"{api_prefix}/conversations/{test_conversation.id}/messages",
            headers=auth_headers,
            params={"page": 1, "page_size": 10},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 10

    @pytest.mark.asyncio
    async def test_list_messages_conversation_not_found(
        self,
        client: AsyncClient,
        api_prefix: str,
        auth_headers: dict,
    ):
        """Test listing messages for non-existent conversation."""
        response = await client.get(
            f"{api_prefix}/conversations/{uuid4()}/messages",
            headers=auth_headers,
        )
        
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_list_messages_unauthorized(
        self, client: AsyncClient, api_prefix: str, test_conversation: Conversation
    ):
        """Test listing messages without auth fails."""
        response = await client.get(
            f"{api_prefix}/conversations/{test_conversation.id}/messages"
        )
        
        assert response.status_code == 403


class TestSendMessage:
    """Tests for send message endpoint."""

    @pytest.mark.asyncio
    async def test_send_text_message_success(
        self,
        client: AsyncClient,
        api_prefix: str,
        auth_headers: dict,
        test_conversation: Conversation,
    ):
        """Test sending a text message."""
        response = await client.post(
            f"{api_prefix}/conversations/{test_conversation.id}/messages",
            headers=auth_headers,
            json={
                "content_type": "text",
                "content": {"text": "Hello from operator!"},
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["content_type"] == "text"
        assert data["content"]["text"] == "Hello from operator!"
        assert data["sender_type"] == "operator"

    @pytest.mark.asyncio
    async def test_send_internal_message(
        self,
        client: AsyncClient,
        api_prefix: str,
        auth_headers: dict,
        test_conversation: Conversation,
    ):
        """Test sending an internal note (not visible to customer)."""
        response = await client.post(
            f"{api_prefix}/conversations/{test_conversation.id}/messages",
            headers=auth_headers,
            json={
                "content_type": "text",
                "content": {"text": "Internal note for team"},
                "is_internal": True,
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_internal"] is True

    @pytest.mark.asyncio
    async def test_send_message_with_reply_to(
        self,
        client: AsyncClient,
        api_prefix: str,
        auth_headers: dict,
        test_conversation: Conversation,
        test_message: Message,
    ):
        """Test sending a reply to another message."""
        response = await client.post(
            f"{api_prefix}/conversations/{test_conversation.id}/messages",
            headers=auth_headers,
            json={
                "content_type": "text",
                "content": {"text": "This is a reply"},
                "reply_to_id": str(test_message.id),
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["reply_to_id"] == str(test_message.id)

    @pytest.mark.asyncio
    async def test_send_image_message(
        self,
        client: AsyncClient,
        api_prefix: str,
        auth_headers: dict,
        test_conversation: Conversation,
    ):
        """Test sending an image message."""
        response = await client.post(
            f"{api_prefix}/conversations/{test_conversation.id}/messages",
            headers=auth_headers,
            json={
                "content_type": "image",
                "content": {
                    "url": "https://example.com/image.png",
                    "caption": "Check this screenshot",
                },
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["content_type"] == "image"

    @pytest.mark.asyncio
    async def test_send_file_message(
        self,
        client: AsyncClient,
        api_prefix: str,
        auth_headers: dict,
        test_conversation: Conversation,
    ):
        """Test sending a file message."""
        response = await client.post(
            f"{api_prefix}/conversations/{test_conversation.id}/messages",
            headers=auth_headers,
            json={
                "content_type": "file",
                "content": {
                    "url": "https://example.com/document.pdf",
                    "filename": "report.pdf",
                },
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["content_type"] == "file"

    @pytest.mark.asyncio
    async def test_send_message_conversation_not_found(
        self,
        client: AsyncClient,
        api_prefix: str,
        auth_headers: dict,
    ):
        """Test sending message to non-existent conversation."""
        response = await client.post(
            f"{api_prefix}/conversations/{uuid4()}/messages",
            headers=auth_headers,
            json={
                "content_type": "text",
                "content": {"text": "Test message"},
            },
        )
        
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_send_message_unauthorized(
        self, client: AsyncClient, api_prefix: str, test_conversation: Conversation
    ):
        """Test sending message without auth fails."""
        response = await client.post(
            f"{api_prefix}/conversations/{test_conversation.id}/messages",
            json={
                "content_type": "text",
                "content": {"text": "Test"},
            },
        )
        
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_send_message_empty_content(
        self,
        client: AsyncClient,
        api_prefix: str,
        auth_headers: dict,
        test_conversation: Conversation,
    ):
        """Test sending message with empty content."""
        response = await client.post(
            f"{api_prefix}/conversations/{test_conversation.id}/messages",
            headers=auth_headers,
            json={
                "content_type": "text",
                "content": {},
            },
        )
        
        # Should succeed (validation is loose)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_send_message_updates_conversation(
        self,
        client: AsyncClient,
        api_prefix: str,
        auth_headers: dict,
        test_conversation: Conversation,
    ):
        """Test that sending message updates conversation metadata."""
        # Send a message
        await client.post(
            f"{api_prefix}/conversations/{test_conversation.id}/messages",
            headers=auth_headers,
            json={
                "content_type": "text",
                "content": {"text": "New message to update conversation"},
            },
        )
        
        # Get conversation and verify it was updated
        response = await client.get(
            f"{api_prefix}/conversations/{test_conversation.id}",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["last_message_at"] is not None
        assert data["messages_count"] >= 1


class TestMessageContent:
    """Tests for various message content types and validation."""

    @pytest.mark.asyncio
    async def test_send_message_with_metadata(
        self,
        client: AsyncClient,
        api_prefix: str,
        auth_headers: dict,
        test_conversation: Conversation,
    ):
        """Test that message preserves content structure."""
        content = {
            "text": "Hello",
            "custom_field": "custom_value",
        }
        
        response = await client.post(
            f"{api_prefix}/conversations/{test_conversation.id}/messages",
            headers=auth_headers,
            json={
                "content_type": "text",
                "content": content,
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["content"]["text"] == "Hello"

    @pytest.mark.asyncio
    async def test_message_response_structure(
        self,
        client: AsyncClient,
        api_prefix: str,
        auth_headers: dict,
        test_conversation: Conversation,
    ):
        """Test that message response has all required fields."""
        response = await client.post(
            f"{api_prefix}/conversations/{test_conversation.id}/messages",
            headers=auth_headers,
            json={
                "content_type": "text",
                "content": {"text": "Test structure"},
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify required fields
        assert "id" in data
        assert "conversation_id" in data
        assert "sender_type" in data
        assert "content_type" in data
        assert "content" in data
        assert "created_at" in data
        assert "is_internal" in data
        assert "is_read" in data


class TestCannedResponses:
    """Tests for canned responses (templates)."""

    @pytest.mark.asyncio
    async def test_list_canned_responses(
        self,
        client: AsyncClient,
        api_prefix: str,
        auth_headers: dict,
    ):
        """Test listing canned responses."""
        response = await client.get(
            f"{api_prefix}/conversations/canned-responses",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_create_canned_response(
        self,
        client: AsyncClient,
        api_prefix: str,
        auth_headers: dict,
    ):
        """Test creating a canned response."""
        response = await client.post(
            f"{api_prefix}/conversations/canned-responses",
            headers=auth_headers,
            params={
                "title": "Greeting",
                "content": "Hello! How can I help you today?",
                "shortcut": "/hello",
                "category": "greetings",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Greeting"
        assert data["shortcut"] == "/hello"
