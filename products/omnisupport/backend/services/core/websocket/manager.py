"""WebSocket connection manager."""

import json
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from fastapi import WebSocket


@dataclass
class Connection:
    """WebSocket connection info."""

    websocket: WebSocket
    user_id: UUID
    tenant_id: UUID
    connected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    subscribed_conversations: set[UUID] = field(default_factory=set)


class ConnectionManager:
    """Manages WebSocket connections."""

    def __init__(self):
        # Active connections by user_id
        self._connections: dict[UUID, Connection] = {}
        # Connections by tenant_id for broadcasting
        self._tenant_connections: dict[UUID, set[UUID]] = defaultdict(set)
        # Connections by conversation_id
        self._conversation_connections: dict[UUID, set[UUID]] = defaultdict(set)

    async def connect(
        self,
        websocket: WebSocket,
        user_id: UUID,
        tenant_id: UUID,
    ) -> Connection:
        """Accept new WebSocket connection."""
        await websocket.accept()

        connection = Connection(
            websocket=websocket,
            user_id=user_id,
            tenant_id=tenant_id,
        )

        self._connections[user_id] = connection
        self._tenant_connections[tenant_id].add(user_id)

        return connection

    async def disconnect(self, user_id: UUID) -> None:
        """Handle connection disconnect."""
        if user_id not in self._connections:
            return

        connection = self._connections[user_id]

        # Remove from tenant connections
        self._tenant_connections[connection.tenant_id].discard(user_id)

        # Remove from conversation subscriptions
        for conv_id in connection.subscribed_conversations:
            self._conversation_connections[conv_id].discard(user_id)

        del self._connections[user_id]

    def subscribe_conversation(self, user_id: UUID, conversation_id: UUID) -> bool:
        """Subscribe user to conversation updates."""
        if user_id not in self._connections:
            return False

        self._connections[user_id].subscribed_conversations.add(conversation_id)
        self._conversation_connections[conversation_id].add(user_id)
        return True

    def unsubscribe_conversation(self, user_id: UUID, conversation_id: UUID) -> bool:
        """Unsubscribe user from conversation updates."""
        if user_id not in self._connections:
            return False

        self._connections[user_id].subscribed_conversations.discard(conversation_id)
        self._conversation_connections[conversation_id].discard(user_id)
        return True

    async def send_personal(self, user_id: UUID, message: dict[str, Any]) -> bool:
        """Send message to specific user."""
        if user_id not in self._connections:
            return False

        try:
            await self._connections[user_id].websocket.send_json(message)
            return True
        except Exception:
            await self.disconnect(user_id)
            return False

    async def broadcast_tenant(
        self,
        tenant_id: UUID,
        message: dict[str, Any],
        exclude_user: UUID | None = None,
    ) -> int:
        """Broadcast message to all users in tenant."""
        sent = 0
        user_ids = list(self._tenant_connections.get(tenant_id, set()))

        for user_id in user_ids:
            if exclude_user and user_id == exclude_user:
                continue

            if await self.send_personal(user_id, message):
                sent += 1

        return sent

    async def broadcast_conversation(
        self,
        conversation_id: UUID,
        message: dict[str, Any],
        exclude_user: UUID | None = None,
    ) -> int:
        """Broadcast message to all users subscribed to conversation."""
        sent = 0
        user_ids = list(self._conversation_connections.get(conversation_id, set()))

        for user_id in user_ids:
            if exclude_user and user_id == exclude_user:
                continue

            if await self.send_personal(user_id, message):
                sent += 1

        return sent

    def get_online_users(self, tenant_id: UUID) -> list[UUID]:
        """Get list of online users in tenant."""
        return list(self._tenant_connections.get(tenant_id, set()))

    def is_online(self, user_id: UUID) -> bool:
        """Check if user is online."""
        return user_id in self._connections

    def get_connection_count(self, tenant_id: UUID | None = None) -> int:
        """Get total connection count."""
        if tenant_id:
            return len(self._tenant_connections.get(tenant_id, set()))
        return len(self._connections)


# Global connection manager instance
manager = ConnectionManager()


def get_manager() -> ConnectionManager:
    """Get the global connection manager."""
    return manager
