"""Conversation endpoints."""

from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from shared.auth.dependencies import ActiveUser, get_db, require_permissions
from shared.models.conversation import (
    Conversation,
    ConversationStatus,
    ConversationPriority,
    ChannelType,
    Message,
    SenderType,
    ContentType,
    CannedResponse,
)
from shared.models.customer import Customer
from shared.models.user import User
from shared.schemas.conversation import (
    ConversationCreate,
    ConversationUpdate,
    ConversationResponse,
    ConversationListResponse,
    MessageCreate,
    MessageResponse,
    MessageListResponse,
    AssignConversationRequest,
    TransferConversationRequest,
    ResolveConversationRequest,
    RateConversationRequest,
    ConversationFilters,
)
from shared.schemas.base import SuccessResponse, PaginatedResponse
from shared.events.publisher import get_publisher
from shared.events.types import EventType

router = APIRouter()


@router.get("", response_model=ConversationListResponse)
async def list_conversations(
    current_user: Annotated[User, Depends(require_permissions("conversations:read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: list[ConversationStatus] | None = Query(None),
    channel: list[ChannelType] | None = Query(None),
    assigned_to: UUID | None = None,
    unassigned: bool | None = None,
    search: str | None = None,
):
    """List conversations with filters."""
    query = (
        select(Conversation)
        .where(Conversation.tenant_id == current_user.tenant_id)
        .options(
            selectinload(Conversation.customer),
            selectinload(Conversation.assigned_to_user),
        )
    )

    if status:
        query = query.where(Conversation.status.in_(status))

    if channel:
        query = query.where(Conversation.channel.in_(channel))

    if assigned_to:
        query = query.where(Conversation.assigned_to == assigned_to)

    if unassigned:
        query = query.where(Conversation.assigned_to.is_(None))

    if search:
        search_pattern = f"%{search}%"
        query = query.join(Customer).where(
            or_(
                Customer.email.ilike(search_pattern),
                Customer.phone.ilike(search_pattern),
                Customer.name.ilike(search_pattern),
                Conversation.subject.ilike(search_pattern),
            )
        )

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Apply pagination and ordering
    query = query.order_by(Conversation.last_message_at.desc().nullslast())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    conversations = list(result.scalars().all())

    return PaginatedResponse.create(
        items=conversations,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=ConversationResponse)
async def create_conversation(
    data: ConversationCreate,
    current_user: Annotated[User, Depends(require_permissions("conversations:write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create a new conversation."""
    # Verify customer exists
    result = await db.execute(
        select(Customer)
        .where(Customer.id == data.customer_id)
        .where(Customer.tenant_id == current_user.tenant_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Клиент не найден",
        )

    conversation = Conversation(
        tenant_id=current_user.tenant_id,
        customer_id=data.customer_id,
        channel=data.channel,
        subject=data.subject,
        tags=data.tags,
        priority=data.priority,
        assigned_to=data.assigned_to,
        metadata=data.metadata,
    )
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation, ["customer", "assigned_to_user"])

    return conversation


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: UUID,
    current_user: Annotated[User, Depends(require_permissions("conversations:read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get conversation by ID."""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.id == conversation_id)
        .where(Conversation.tenant_id == current_user.tenant_id)
        .options(
            selectinload(Conversation.customer),
            selectinload(Conversation.assigned_to_user),
        )
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Диалог не найден",
        )

    return conversation


@router.patch("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: UUID,
    data: ConversationUpdate,
    current_user: Annotated[User, Depends(require_permissions("conversations:write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update conversation."""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.id == conversation_id)
        .where(Conversation.tenant_id == current_user.tenant_id)
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Диалог не найден",
        )

    update_data = data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        if hasattr(conversation, field):
            setattr(conversation, field, value)

    await db.commit()
    await db.refresh(conversation)

    return conversation


@router.get("/{conversation_id}/messages", response_model=MessageListResponse)
async def get_conversation_messages(
    conversation_id: UUID,
    current_user: Annotated[User, Depends(require_permissions("conversations:read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
):
    """Get conversation messages."""
    # Verify conversation exists
    result = await db.execute(
        select(Conversation)
        .where(Conversation.id == conversation_id)
        .where(Conversation.tenant_id == current_user.tenant_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Диалог не найден",
        )

    query = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
    )

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    messages = list(result.scalars().all())

    return PaginatedResponse.create(
        items=messages,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/{conversation_id}/messages", response_model=MessageResponse)
async def send_message(
    conversation_id: UUID,
    data: MessageCreate,
    current_user: Annotated[User, Depends(require_permissions("conversations:reply"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Send a message to conversation."""
    # Get conversation
    result = await db.execute(
        select(Conversation)
        .where(Conversation.id == conversation_id)
        .where(Conversation.tenant_id == current_user.tenant_id)
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
        sender_type=SenderType.OPERATOR,
        sender_id=current_user.id,
        content_type=data.content_type,
        content=data.content,
        is_internal=data.is_internal,
        reply_to_id=data.reply_to_id,
    )
    db.add(message)

    # Update conversation
    now = datetime.now(timezone.utc)
    conversation.last_message_at = now
    conversation.last_message_preview = data.content.get("text", "")[:500] if data.content_type == ContentType.TEXT else f"[{data.content_type.value}]"
    conversation.messages_count += 1

    # Set first response time if this is the first operator response
    if conversation.first_response_at is None and not data.is_internal:
        conversation.first_response_at = now

    await db.commit()
    await db.refresh(message)

    # Publish event
    publisher = await get_publisher()
    await publisher.publish_raw(
        event_type=EventType.MESSAGE_SENT,
        tenant_id=current_user.tenant_id,
        conversation_id=conversation_id,
        data={
            "message_id": str(message.id),
            "content_type": data.content_type.value,
            "sender_id": str(current_user.id),
        },
    )

    return message


@router.post("/{conversation_id}/assign", response_model=ConversationResponse)
async def assign_conversation(
    conversation_id: UUID,
    data: AssignConversationRequest,
    current_user: Annotated[User, Depends(require_permissions("conversations:assign"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Assign conversation to an operator."""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.id == conversation_id)
        .where(Conversation.tenant_id == current_user.tenant_id)
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Диалог не найден",
        )

    # Verify operator exists
    result = await db.execute(
        select(User)
        .where(User.id == data.operator_id)
        .where(User.tenant_id == current_user.tenant_id)
        .where(User.is_active == True)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Оператор не найден",
        )

    conversation.assigned_to = data.operator_id
    await db.commit()
    await db.refresh(conversation, ["customer", "assigned_to_user"])

    # Publish event
    publisher = await get_publisher()
    await publisher.publish_raw(
        event_type=EventType.CONVERSATION_ASSIGNED,
        tenant_id=current_user.tenant_id,
        conversation_id=conversation_id,
        data={"operator_id": str(data.operator_id)},
    )

    return conversation


@router.post("/{conversation_id}/transfer", response_model=ConversationResponse)
async def transfer_conversation(
    conversation_id: UUID,
    data: TransferConversationRequest,
    current_user: Annotated[User, Depends(require_permissions("conversations:assign"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Transfer conversation to another operator."""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.id == conversation_id)
        .where(Conversation.tenant_id == current_user.tenant_id)
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Диалог не найден",
        )

    # Verify target operator
    result = await db.execute(
        select(User)
        .where(User.id == data.operator_id)
        .where(User.tenant_id == current_user.tenant_id)
        .where(User.is_active == True)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Оператор не найден",
        )

    old_operator = conversation.assigned_to
    conversation.assigned_to = data.operator_id

    # Add internal note about transfer
    if data.note:
        note = Message(
            conversation_id=conversation_id,
            sender_type=SenderType.SYSTEM,
            sender_id=current_user.id,
            content_type=ContentType.TEXT,
            content={"text": f"Диалог передан: {data.note}"},
            is_internal=True,
        )
        db.add(note)

    await db.commit()
    await db.refresh(conversation, ["customer", "assigned_to_user"])

    # Publish event
    publisher = await get_publisher()
    await publisher.publish_raw(
        event_type=EventType.CONVERSATION_TRANSFERRED,
        tenant_id=current_user.tenant_id,
        conversation_id=conversation_id,
        data={
            "from_operator_id": str(old_operator) if old_operator else None,
            "to_operator_id": str(data.operator_id),
        },
    )

    return conversation


@router.post("/{conversation_id}/resolve", response_model=ConversationResponse)
async def resolve_conversation(
    conversation_id: UUID,
    current_user: Annotated[User, Depends(require_permissions("conversations:write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    data: ResolveConversationRequest | None = None,
):
    """Resolve conversation."""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.id == conversation_id)
        .where(Conversation.tenant_id == current_user.tenant_id)
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Диалог не найден",
        )

    conversation.status = ConversationStatus.RESOLVED
    conversation.resolved_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(conversation, ["customer", "assigned_to_user"])

    return conversation


@router.post("/{conversation_id}/close", response_model=ConversationResponse)
async def close_conversation(
    conversation_id: UUID,
    current_user: Annotated[User, Depends(require_permissions("conversations:write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Close conversation."""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.id == conversation_id)
        .where(Conversation.tenant_id == current_user.tenant_id)
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Диалог не найден",
        )

    conversation.status = ConversationStatus.CLOSED
    conversation.closed_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(conversation, ["customer", "assigned_to_user"])

    return conversation


@router.post("/{conversation_id}/reopen", response_model=ConversationResponse)
async def reopen_conversation(
    conversation_id: UUID,
    current_user: Annotated[User, Depends(require_permissions("conversations:write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Reopen a closed conversation."""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.id == conversation_id)
        .where(Conversation.tenant_id == current_user.tenant_id)
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Диалог не найден",
        )

    conversation.status = ConversationStatus.OPEN
    conversation.resolved_at = None
    conversation.closed_at = None

    await db.commit()
    await db.refresh(conversation, ["customer", "assigned_to_user"])

    return conversation


# ==================== Canned Responses ====================

@router.get("/canned-responses", response_model=list)
async def list_canned_responses(
    current_user: Annotated[User, Depends(require_permissions("conversations:read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    category: str | None = None,
):
    """List canned responses."""
    query = (
        select(CannedResponse)
        .where(CannedResponse.tenant_id == current_user.tenant_id)
        .where(CannedResponse.is_active == True)
    )

    if category:
        query = query.where(CannedResponse.category == category)

    query = query.order_by(CannedResponse.usage_count.desc())

    result = await db.execute(query)
    responses = list(result.scalars().all())

    return responses


@router.post("/canned-responses")
async def create_canned_response(
    current_user: Annotated[User, Depends(require_permissions("conversations:write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    title: str,
    content: str,
    shortcut: str | None = None,
    category: str | None = None,
):
    """Create a canned response."""
    canned = CannedResponse(
        tenant_id=current_user.tenant_id,
        created_by=current_user.id,
        title=title,
        content=content,
        shortcut=shortcut,
        category=category,
    )
    db.add(canned)
    await db.commit()
    await db.refresh(canned)

    return canned
