"""Channel management endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from shared.auth.dependencies import ActiveUser, get_db, require_permissions
from shared.models.channel import Channel, ChannelStatus, WidgetSettings, WidgetPosition
from shared.models.conversation import ChannelType
from shared.models.user import User
from shared.schemas.base import SuccessResponse

router = APIRouter()


@router.get("")
async def list_channels(
    current_user: Annotated[User, Depends(require_permissions("channels:read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """List all channels."""
    result = await db.execute(
        select(Channel)
        .where(Channel.tenant_id == current_user.tenant_id)
        .options(selectinload(Channel.widget_settings))
        .order_by(Channel.created_at)
    )
    channels = list(result.scalars().all())

    return {"items": channels, "total": len(channels)}


@router.get("/{channel_type}/{channel_id}")
async def get_channel(
    channel_type: ChannelType,
    channel_id: UUID,
    current_user: Annotated[User, Depends(require_permissions("channels:read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get channel by ID."""
    result = await db.execute(
        select(Channel)
        .where(Channel.id == channel_id)
        .where(Channel.type == channel_type)
        .where(Channel.tenant_id == current_user.tenant_id)
        .options(selectinload(Channel.widget_settings))
    )
    channel = result.scalar_one_or_none()

    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Канал не найден",
        )

    return channel


@router.post("/telegram")
async def connect_telegram(
    current_user: Annotated[User, Depends(require_permissions("channels:manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    name: str,
    bot_token: str,
):
    """Connect Telegram bot."""
    # TODO: Validate bot token with Telegram API
    channel = Channel(
        tenant_id=current_user.tenant_id,
        type=ChannelType.TELEGRAM,
        name=name,
        credentials={"bot_token": bot_token},
        status=ChannelStatus.PENDING,
    )
    db.add(channel)
    await db.commit()
    await db.refresh(channel)

    # TODO: Set up webhook with Telegram

    return channel


@router.post("/whatsapp")
async def connect_whatsapp(
    current_user: Annotated[User, Depends(require_permissions("channels:manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    name: str,
    api_key: str,
    phone_number_id: str,
):
    """Connect WhatsApp Business API."""
    channel = Channel(
        tenant_id=current_user.tenant_id,
        type=ChannelType.WHATSAPP,
        name=name,
        credentials={
            "api_key": api_key,
            "phone_number_id": phone_number_id,
        },
        status=ChannelStatus.PENDING,
    )
    db.add(channel)
    await db.commit()
    await db.refresh(channel)

    return channel


@router.post("/widget")
async def create_widget(
    current_user: Annotated[User, Depends(require_permissions("channels:manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    name: str,
    primary_color: str = "#6366f1",
    welcome_message: str | None = None,
):
    """Create web widget."""
    import secrets

    widget_id = secrets.token_urlsafe(16)

    channel = Channel(
        tenant_id=current_user.tenant_id,
        type=ChannelType.WEB,
        name=name,
        credentials={"widget_id": widget_id},
        status=ChannelStatus.ACTIVE,
    )
    db.add(channel)
    await db.flush()

    # Create widget settings
    widget_settings = WidgetSettings(
        channel_id=channel.id,
        primary_color=primary_color,
        welcome_message=welcome_message,
    )
    db.add(widget_settings)

    await db.commit()
    await db.refresh(channel, ["widget_settings"])

    return channel


@router.patch("/{channel_type}/{channel_id}")
async def update_channel(
    channel_type: ChannelType,
    channel_id: UUID,
    current_user: Annotated[User, Depends(require_permissions("channels:manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    name: str | None = None,
    is_active: bool | None = None,
    settings: dict | None = None,
):
    """Update channel settings."""
    result = await db.execute(
        select(Channel)
        .where(Channel.id == channel_id)
        .where(Channel.type == channel_type)
        .where(Channel.tenant_id == current_user.tenant_id)
    )
    channel = result.scalar_one_or_none()

    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Канал не найден",
        )

    if name is not None:
        channel.name = name
    if is_active is not None:
        channel.is_active = is_active
    if settings is not None:
        channel.settings = {**channel.settings, **settings}

    await db.commit()
    await db.refresh(channel)

    return channel


@router.patch("/{channel_type}/{channel_id}/widget")
async def update_widget_settings(
    channel_type: ChannelType,
    channel_id: UUID,
    current_user: Annotated[User, Depends(require_permissions("channels:manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    primary_color: str | None = None,
    text_color: str | None = None,
    background_color: str | None = None,
    position: WidgetPosition | None = None,
    welcome_message: str | None = None,
    placeholder_text: str | None = None,
    offline_message: str | None = None,
    auto_open: bool | None = None,
    require_email: bool | None = None,
    require_name: bool | None = None,
):
    """Update widget settings."""
    if channel_type != ChannelType.WEB:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Только для веб-виджета",
        )

    result = await db.execute(
        select(Channel)
        .where(Channel.id == channel_id)
        .where(Channel.tenant_id == current_user.tenant_id)
        .options(selectinload(Channel.widget_settings))
    )
    channel = result.scalar_one_or_none()

    if not channel or not channel.widget_settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Виджет не найден",
        )

    ws = channel.widget_settings

    if primary_color is not None:
        ws.primary_color = primary_color
    if text_color is not None:
        ws.text_color = text_color
    if background_color is not None:
        ws.background_color = background_color
    if position is not None:
        ws.position = position
    if welcome_message is not None:
        ws.welcome_message = welcome_message
    if placeholder_text is not None:
        ws.placeholder_text = placeholder_text
    if offline_message is not None:
        ws.offline_message = offline_message
    if auto_open is not None:
        ws.auto_open = auto_open
    if require_email is not None:
        ws.require_email = require_email
    if require_name is not None:
        ws.require_name = require_name

    await db.commit()
    await db.refresh(channel, ["widget_settings"])

    return channel


@router.delete("/{channel_type}/{channel_id}", response_model=SuccessResponse)
async def delete_channel(
    channel_type: ChannelType,
    channel_id: UUID,
    current_user: Annotated[User, Depends(require_permissions("channels:manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete channel."""
    result = await db.execute(
        select(Channel)
        .where(Channel.id == channel_id)
        .where(Channel.type == channel_type)
        .where(Channel.tenant_id == current_user.tenant_id)
    )
    channel = result.scalar_one_or_none()

    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Канал не найден",
        )

    await db.delete(channel)
    await db.commit()

    return SuccessResponse(message="Канал удалён")
