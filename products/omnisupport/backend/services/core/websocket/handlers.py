"""WebSocket event handlers."""

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.user import User, UserStatus
from shared.models.conversation import Conversation, Message
from services.core.websocket.manager import ConnectionManager


class EventHandler:
    """Handles incoming WebSocket events."""

    def __init__(self, manager: ConnectionManager, db: AsyncSession):
        self.manager = manager
        self.db = db

    async def handle_event(
        self,
        user_id: UUID,
        event_type: str,
        data: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Route event to appropriate handler."""
        handlers = {
            "join_conversation": self._handle_join_conversation,
            "leave_conversation": self._handle_leave_conversation,
            "typing_start": self._handle_typing_start,
            "typing_stop": self._handle_typing_stop,
            "message_read": self._handle_message_read,
            "status_update": self._handle_status_update,
            "ping": self._handle_ping,
        }

        handler = handlers.get(event_type)
        if handler:
            return await handler(user_id, data)

        return {"type": "error", "message": f"Unknown event type: {event_type}"}

    async def _handle_join_conversation(
        self,
        user_id: UUID,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        """Handle join_conversation event."""
        conversation_id = UUID(data.get("conversation_id", ""))

        # Verify access
        result = await self.db.execute(
            select(Conversation)
            .join(User, User.tenant_id == Conversation.tenant_id)
            .where(Conversation.id == conversation_id)
            .where(User.id == user_id)
        )
        conversation = result.scalar_one_or_none()

        if not conversation:
            return {"type": "error", "message": "Conversation not found or access denied"}

        self.manager.subscribe_conversation(user_id, conversation_id)

        return {
            "type": "joined_conversation",
            "conversation_id": str(conversation_id),
        }

    async def _handle_leave_conversation(
        self,
        user_id: UUID,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        """Handle leave_conversation event."""
        conversation_id = UUID(data.get("conversation_id", ""))
        self.manager.unsubscribe_conversation(user_id, conversation_id)

        return {
            "type": "left_conversation",
            "conversation_id": str(conversation_id),
        }

    async def _handle_typing_start(
        self,
        user_id: UUID,
        data: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Handle typing_start event."""
        conversation_id = UUID(data.get("conversation_id", ""))

        # Broadcast to other users in conversation
        await self.manager.broadcast_conversation(
            conversation_id,
            {
                "type": "operator.typing",
                "conversation_id": str(conversation_id),
                "user_id": str(user_id),
                "is_typing": True,
            },
            exclude_user=user_id,
        )

        return None  # No response needed

    async def _handle_typing_stop(
        self,
        user_id: UUID,
        data: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Handle typing_stop event."""
        conversation_id = UUID(data.get("conversation_id", ""))

        await self.manager.broadcast_conversation(
            conversation_id,
            {
                "type": "operator.typing",
                "conversation_id": str(conversation_id),
                "user_id": str(user_id),
                "is_typing": False,
            },
            exclude_user=user_id,
        )

        return None

    async def _handle_message_read(
        self,
        user_id: UUID,
        data: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Handle message_read event."""
        message_id = UUID(data.get("message_id", ""))

        # Update message read status
        result = await self.db.execute(
            select(Message).where(Message.id == message_id)
        )
        message = result.scalar_one_or_none()

        if message:
            message.is_read = True
            message.read_at = datetime.now(timezone.utc)
            await self.db.commit()

            # Broadcast read receipt
            await self.manager.broadcast_conversation(
                message.conversation_id,
                {
                    "type": "message.read",
                    "message_id": str(message_id),
                    "conversation_id": str(message.conversation_id),
                    "read_by": str(user_id),
                    "read_at": message.read_at.isoformat(),
                },
                exclude_user=user_id,
            )

        return None

    async def _handle_status_update(
        self,
        user_id: UUID,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        """Handle status_update event."""
        new_status = data.get("status", "online")

        # Update user status
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if user:
            user.status = UserStatus(new_status)
            user.last_activity_at = datetime.now(timezone.utc)
            await self.db.commit()

            # Broadcast status change to tenant
            await self.manager.broadcast_tenant(
                user.tenant_id,
                {
                    "type": "operator.status_changed",
                    "user_id": str(user_id),
                    "status": new_status,
                },
                exclude_user=user_id,
            )

        return {"type": "status_updated", "status": new_status}

    async def _handle_ping(
        self,
        user_id: UUID,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        """Handle ping event (keepalive)."""
        return {"type": "pong", "timestamp": datetime.now(timezone.utc).isoformat()}
