"""Customer endpoints."""

from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from shared.auth.dependencies import ActiveUser, get_db, require_permissions
from shared.models.customer import Customer, CustomerIdentity, CustomerNote
from shared.models.user import User
from shared.schemas.customer import (
    CustomerCreate,
    CustomerUpdate,
    CustomerResponse,
    CustomerListResponse,
    CustomerNoteCreate,
    CustomerNoteResponse,
    CustomerMergeRequest,
)
from shared.schemas.base import SuccessResponse, PaginatedResponse

router = APIRouter()


@router.get("", response_model=CustomerListResponse)
async def list_customers(
    current_user: Annotated[User, Depends(require_permissions("customers:read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = None,
    tags: list[str] | None = Query(None),
    channel: str | None = None,
):
    """List customers with pagination and filters."""
    query = (
        select(Customer)
        .where(Customer.tenant_id == current_user.tenant_id)
        .options(selectinload(Customer.identities))
    )

    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            or_(
                Customer.email.ilike(search_pattern),
                Customer.phone.ilike(search_pattern),
                Customer.name.ilike(search_pattern),
            )
        )

    if tags:
        query = query.where(Customer.tags.contains(tags))

    if channel:
        query = query.join(CustomerIdentity).where(
            CustomerIdentity.channel == channel
        )

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Apply pagination
    query = query.offset((page - 1) * page_size).limit(page_size)
    query = query.order_by(Customer.last_seen_at.desc().nullslast())

    result = await db.execute(query)
    customers = list(result.scalars().all())

    return PaginatedResponse.create(
        items=customers,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=CustomerResponse)
async def create_customer(
    data: CustomerCreate,
    current_user: Annotated[User, Depends(require_permissions("customers:write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create a new customer."""
    customer = Customer(
        tenant_id=current_user.tenant_id,
        email=data.email,
        phone=data.phone,
        name=data.name,
        company=data.company,
        position=data.position,
        location=data.location,
        timezone=data.timezone,
        tags=data.tags,
        custom_fields=data.custom_fields,
        first_seen_at=datetime.now(timezone.utc),
    )
    db.add(customer)
    await db.commit()
    await db.refresh(customer)

    return customer


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: UUID,
    current_user: Annotated[User, Depends(require_permissions("customers:read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get customer by ID."""
    result = await db.execute(
        select(Customer)
        .where(Customer.id == customer_id)
        .where(Customer.tenant_id == current_user.tenant_id)
        .options(selectinload(Customer.identities))
    )
    customer = result.scalar_one_or_none()

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Клиент не найден",
        )

    return customer


@router.patch("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: UUID,
    data: CustomerUpdate,
    current_user: Annotated[User, Depends(require_permissions("customers:write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update customer."""
    result = await db.execute(
        select(Customer)
        .where(Customer.id == customer_id)
        .where(Customer.tenant_id == current_user.tenant_id)
    )
    customer = result.scalar_one_or_none()

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Клиент не найден",
        )

    update_data = data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        if hasattr(customer, field):
            setattr(customer, field, value)

    await db.commit()
    await db.refresh(customer)

    return customer


@router.delete("/{customer_id}", response_model=SuccessResponse)
async def delete_customer(
    customer_id: UUID,
    current_user: Annotated[User, Depends(require_permissions("customers:delete"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete customer."""
    result = await db.execute(
        select(Customer)
        .where(Customer.id == customer_id)
        .where(Customer.tenant_id == current_user.tenant_id)
    )
    customer = result.scalar_one_or_none()

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Клиент не найден",
        )

    await db.delete(customer)
    await db.commit()

    return SuccessResponse(message="Клиент удалён")


@router.get("/{customer_id}/conversations")
async def get_customer_conversations(
    customer_id: UUID,
    current_user: Annotated[User, Depends(require_permissions("customers:read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """Get customer's conversations."""
    from shared.models.conversation import Conversation

    # Verify customer exists
    result = await db.execute(
        select(Customer)
        .where(Customer.id == customer_id)
        .where(Customer.tenant_id == current_user.tenant_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Клиент не найден",
        )

    query = (
        select(Conversation)
        .where(Conversation.customer_id == customer_id)
        .order_by(Conversation.created_at.desc())
    )

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    conversations = list(result.scalars().all())

    return PaginatedResponse.create(
        items=conversations,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{customer_id}/notes", response_model=list[CustomerNoteResponse])
async def get_customer_notes(
    customer_id: UUID,
    current_user: Annotated[User, Depends(require_permissions("customers:read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get customer notes."""
    # Verify customer exists
    result = await db.execute(
        select(Customer)
        .where(Customer.id == customer_id)
        .where(Customer.tenant_id == current_user.tenant_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Клиент не найден",
        )

    result = await db.execute(
        select(CustomerNote)
        .where(CustomerNote.customer_id == customer_id)
        .options(selectinload(CustomerNote.author))
        .order_by(CustomerNote.created_at.desc())
    )
    notes = list(result.scalars().all())

    return notes


@router.post("/{customer_id}/notes", response_model=CustomerNoteResponse)
async def create_customer_note(
    customer_id: UUID,
    data: CustomerNoteCreate,
    current_user: Annotated[User, Depends(require_permissions("customers:write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create a note for customer."""
    # Verify customer exists
    result = await db.execute(
        select(Customer)
        .where(Customer.id == customer_id)
        .where(Customer.tenant_id == current_user.tenant_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Клиент не найден",
        )

    note = CustomerNote(
        customer_id=customer_id,
        author_id=current_user.id,
        content=data.content,
    )
    db.add(note)
    await db.commit()
    await db.refresh(note)

    return note


@router.post("/{customer_id}/merge", response_model=CustomerResponse)
async def merge_customers(
    customer_id: UUID,
    data: CustomerMergeRequest,
    current_user: Annotated[User, Depends(require_permissions("customers:delete"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Merge multiple customers into one."""
    # Get target customer
    result = await db.execute(
        select(Customer)
        .where(Customer.id == customer_id)
        .where(Customer.tenant_id == current_user.tenant_id)
    )
    target = result.scalar_one_or_none()

    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Целевой клиент не найден",
        )

    # Get source customers
    result = await db.execute(
        select(Customer)
        .where(Customer.id.in_(data.source_customer_ids))
        .where(Customer.tenant_id == current_user.tenant_id)
    )
    sources = list(result.scalars().all())

    if len(sources) != len(data.source_customer_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Не все исходные клиенты найдены",
        )

    # Merge data from sources to target
    for source in sources:
        # Merge identities
        result = await db.execute(
            select(CustomerIdentity).where(CustomerIdentity.customer_id == source.id)
        )
        for identity in result.scalars():
            identity.customer_id = target.id

        # Merge notes
        result = await db.execute(
            select(CustomerNote).where(CustomerNote.customer_id == source.id)
        )
        for note in result.scalars():
            note.customer_id = target.id

        # Merge conversations
        from shared.models.conversation import Conversation

        result = await db.execute(
            select(Conversation).where(Conversation.customer_id == source.id)
        )
        for conv in result.scalars():
            conv.customer_id = target.id

        # Update conversation count
        target.conversations_count += source.conversations_count

        # Merge tags
        target.tags = list(set(target.tags + source.tags))

        # Delete source
        await db.delete(source)

    await db.commit()
    await db.refresh(target)

    return target


@router.post("/export")
async def export_customers(
    current_user: Annotated[User, Depends(require_permissions("customers:read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    format: str = Query("csv", pattern="^(csv|excel)$"),
):
    """Export customers to CSV or Excel."""
    # TODO: Implement actual export
    return {"message": "Export started", "format": format}
