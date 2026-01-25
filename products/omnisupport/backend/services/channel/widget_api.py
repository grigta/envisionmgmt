"""Public Widget API - no authentication required."""

from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from shared.database import get_db
from shared.models.tenant import Tenant
from shared.models.channel import Channel, WidgetSettings
from shared.models.conversation import Conversation, Message, ChannelType, ConversationStatus, SenderType, ContentType
from shared.models.customer import Customer, CustomerIdentity
from shared.events.publisher import get_publisher
from shared.events.types import EventType

router = APIRouter()


class WidgetConfigResponse(BaseModel):
    """Widget configuration response."""

    tenant_id: str
    tenant_name: str
    primary_color: str
    text_color: str
    background_color: str
    position: str
    welcome_message: str | None
    placeholder_text: str
    offline_message: str | None
    require_email: bool
    require_name: bool
    show_branding: bool
    is_online: bool


class StartConversationRequest(BaseModel):
    """Start conversation request."""

    visitor_id: str
    name: str | None = None
    email: EmailStr | None = None
    initial_message: str | None = None
    metadata: dict = {}


class SendMessageRequest(BaseModel):
    """Send message request."""

    content: str
    content_type: str = "text"


@router.get("/config/{tenant_slug}", response_model=WidgetConfigResponse)
async def get_widget_config(
    tenant_slug: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get widget configuration by tenant slug."""
    # Find tenant and active web channel
    result = await db.execute(
        select(Tenant)
        .where(Tenant.slug == tenant_slug)
        .where(Tenant.is_active == True)
    )
    tenant = result.scalar_one_or_none()

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Виджет не найден",
        )

    # Find web channel with widget settings
    result = await db.execute(
        select(Channel)
        .where(Channel.tenant_id == tenant.id)
        .where(Channel.type == ChannelType.WEB)
        .where(Channel.is_active == True)
        .options(selectinload(Channel.widget_settings))
        .limit(1)
    )
    channel = result.scalar_one_or_none()

    if not channel or not channel.widget_settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Виджет не настроен",
        )

    ws = channel.widget_settings

    # TODO: Check business hours to determine is_online
    is_online = True

    return WidgetConfigResponse(
        tenant_id=str(tenant.id),
        tenant_name=tenant.name,
        primary_color=ws.primary_color,
        text_color=ws.text_color,
        background_color=ws.background_color,
        position=ws.position.value,
        welcome_message=ws.welcome_message,
        placeholder_text=ws.placeholder_text,
        offline_message=ws.offline_message,
        require_email=ws.require_email,
        require_name=ws.require_name,
        show_branding=ws.show_branding,
        is_online=is_online,
    )


@router.post("/conversations")
async def start_conversation(
    data: StartConversationRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    tenant_slug: str = Query(...),
):
    """Start a new conversation from widget."""
    # Find tenant
    result = await db.execute(
        select(Tenant)
        .where(Tenant.slug == tenant_slug)
        .where(Tenant.is_active == True)
    )
    tenant = result.scalar_one_or_none()

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Компания не найдена",
        )

    # Find or create customer
    customer = await _get_or_create_customer(
        db=db,
        tenant_id=tenant.id,
        visitor_id=data.visitor_id,
        name=data.name,
        email=data.email,
        metadata=data.metadata,
    )

    # Create conversation
    conversation = Conversation(
        tenant_id=tenant.id,
        customer_id=customer.id,
        channel=ChannelType.WEB,
        channel_conversation_id=data.visitor_id,
        status=ConversationStatus.OPEN,
    )
    db.add(conversation)
    await db.flush()

    # Create initial message if provided
    if data.initial_message:
        message = Message(
            conversation_id=conversation.id,
            sender_type=SenderType.CUSTOMER,
            sender_id=customer.id,
            content_type=ContentType.TEXT,
            content={"text": data.initial_message},
        )
        db.add(message)

        conversation.last_message_at = datetime.now(timezone.utc)
        conversation.last_message_preview = data.initial_message[:500]
        conversation.messages_count = 1

    await db.commit()
    await db.refresh(conversation)

    # Publish event
    publisher = await get_publisher()
    await publisher.publish_raw(
        event_type=EventType.CONVERSATION_CREATED,
        tenant_id=tenant.id,
        conversation_id=conversation.id,
        customer_id=customer.id,
        data={"channel": "web"},
    )

    return {
        "conversation_id": str(conversation.id),
        "customer_id": str(customer.id),
    }


@router.get("/conversations/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    after: datetime | None = None,
    limit: int = Query(50, ge=1, le=100),
):
    """Get messages for conversation (public, from widget)."""
    query = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .where(Message.is_internal == False)  # Don't show internal notes
        .order_by(Message.created_at.desc())
        .limit(limit)
    )

    if after:
        query = query.where(Message.created_at > after)

    result = await db.execute(query)
    messages = list(result.scalars().all())

    return {
        "messages": [
            {
                "id": str(m.id),
                "sender_type": m.sender_type.value,
                "content_type": m.content_type.value,
                "content": m.content,
                "created_at": m.created_at.isoformat(),
            }
            for m in reversed(messages)
        ]
    }


@router.post("/conversations/{conversation_id}/messages")
async def send_message_from_widget(
    conversation_id: UUID,
    data: SendMessageRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Send message from widget."""
    # Get conversation
    result = await db.execute(
        select(Conversation)
        .where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Диалог не найден",
        )

    # Create message
    message = Message(
        conversation_id=conversation_id,
        sender_type=SenderType.CUSTOMER,
        sender_id=conversation.customer_id,
        content_type=ContentType.TEXT,
        content={"text": data.content},
    )
    db.add(message)

    # Update conversation
    now = datetime.now(timezone.utc)
    conversation.last_message_at = now
    conversation.last_message_preview = data.content[:500]
    conversation.messages_count += 1

    # Reopen if closed
    if conversation.status == ConversationStatus.CLOSED:
        conversation.status = ConversationStatus.OPEN

    await db.commit()
    await db.refresh(message)

    # Publish event
    publisher = await get_publisher()
    await publisher.publish_raw(
        event_type=EventType.MESSAGE_RECEIVED,
        tenant_id=conversation.tenant_id,
        conversation_id=conversation_id,
        customer_id=conversation.customer_id,
        data={
            "message_id": str(message.id),
            "content_type": "text",
        },
    )

    return {
        "message_id": str(message.id),
        "created_at": message.created_at.isoformat(),
    }


@router.websocket("/conversations/{conversation_id}/ws")
async def widget_websocket(
    websocket: WebSocket,
    conversation_id: UUID,
):
    """WebSocket for real-time widget updates."""
    await websocket.accept()

    # Simple message forwarding from Redis pub/sub
    # In production, this would subscribe to conversation-specific channel

    try:
        while True:
            # Wait for messages (or implement proper Redis subscription)
            data = await websocket.receive_json()

            # Handle typing indicator from customer
            if data.get("type") == "typing":
                # TODO: Forward to operators
                pass

    except WebSocketDisconnect:
        pass
    except Exception:
        pass


async def _get_or_create_customer(
    db: AsyncSession,
    tenant_id: UUID,
    visitor_id: str,
    name: str | None,
    email: str | None,
    metadata: dict,
) -> Customer:
    """Get existing customer or create new one."""
    # Try to find by visitor_id (channel identity)
    result = await db.execute(
        select(CustomerIdentity)
        .where(CustomerIdentity.channel == "web")
        .where(CustomerIdentity.channel_user_id == visitor_id)
        .options(selectinload(CustomerIdentity.customer))
    )
    identity = result.scalar_one_or_none()

    if identity and identity.customer:
        # Update customer info if provided
        customer = identity.customer
        if name and not customer.name:
            customer.name = name
        if email and not customer.email:
            customer.email = email
        customer.last_seen_at = datetime.now(timezone.utc)
        return customer

    # Try to find by email
    if email:
        result = await db.execute(
            select(Customer)
            .where(Customer.tenant_id == tenant_id)
            .where(Customer.email == email)
        )
        customer = result.scalar_one_or_none()

        if customer:
            # Create identity for this customer
            identity = CustomerIdentity(
                customer_id=customer.id,
                channel="web",
                channel_user_id=visitor_id,
                channel_name=name,
            )
            db.add(identity)
            customer.last_seen_at = datetime.now(timezone.utc)
            return customer

    # Create new customer
    now = datetime.now(timezone.utc)
    customer = Customer(
        tenant_id=tenant_id,
        name=name,
        email=email,
        metadata=metadata,
        first_seen_at=now,
        last_seen_at=now,
        preferred_channel="web",
    )
    db.add(customer)
    await db.flush()

    # Create identity
    identity = CustomerIdentity(
        customer_id=customer.id,
        channel="web",
        channel_user_id=visitor_id,
        channel_name=name,
    )
    db.add(identity)

    return customer
