"""WebSocket routes."""

import json
from uuid import UUID

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.auth.jwt import decode_token
from shared.database import get_db
from shared.models.user import User, UserStatus
from services.core.websocket.manager import get_manager, ConnectionManager
from services.core.websocket.handlers import EventHandler

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...),
):
    """Main WebSocket endpoint for operators."""
    manager = get_manager()

    # Authenticate using token
    payload = decode_token(token)
    if not payload or payload.type != "access":
        await websocket.close(code=4001, reason="Invalid token")
        return

    user_id = UUID(payload.sub)
    tenant_id = UUID(payload.tenant_id)

    # Get database session
    async for db in get_db():
        # Verify user exists and is active
        result = await db.execute(
            select(User)
            .where(User.id == user_id)
            .where(User.is_active == True)
        )
        user = result.scalar_one_or_none()

        if not user:
            await websocket.close(code=4003, reason="User not found")
            return

        # Connect
        connection = await manager.connect(websocket, user_id, tenant_id)

        # Update user status to online
        user.status = UserStatus.ONLINE
        await db.commit()

        # Notify others
        await manager.broadcast_tenant(
            tenant_id,
            {
                "type": "operator.connected",
                "user_id": str(user_id),
            },
            exclude_user=user_id,
        )

        # Send initial state
        await websocket.send_json({
            "type": "connected",
            "user_id": str(user_id),
            "online_users": [str(uid) for uid in manager.get_online_users(tenant_id)],
        })

        # Event handler
        handler = EventHandler(manager, db)

        try:
            while True:
                # Receive message
                data = await websocket.receive_json()
                event_type = data.get("type")
                event_data = data.get("data", {})

                # Handle event
                response = await handler.handle_event(user_id, event_type, event_data)

                # Send response if any
                if response:
                    await websocket.send_json(response)

        except WebSocketDisconnect:
            pass
        except Exception as e:
            print(f"WebSocket error: {e}")
        finally:
            # Disconnect
            await manager.disconnect(user_id)

            # Update user status to offline
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if user:
                user.status = UserStatus.OFFLINE
                await db.commit()

            # Notify others
            await manager.broadcast_tenant(
                tenant_id,
                {
                    "type": "operator.disconnected",
                    "user_id": str(user_id),
                },
            )
