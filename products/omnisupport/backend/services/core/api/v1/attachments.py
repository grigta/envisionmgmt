"""Attachment upload endpoints."""

from datetime import datetime, timedelta, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.auth.dependencies import ActiveUser, get_db
from shared.models.attachment import Attachment, AttachmentStatus
from shared.schemas.attachment import (
    AttachmentResponse,
    AttachmentUploadResponse,
    AttachmentListResponse,
)
from shared.storage import (
    get_storage_service,
    StorageService,
    StorageError,
    FileTooLargeError,
    InvalidFileTypeError,
    MAX_FILES_PER_UPLOAD,
)

router = APIRouter()

# Pending attachment expiration (2 hours)
PENDING_EXPIRATION_HOURS = 2


def get_storage() -> StorageService:
    """Get storage service dependency."""
    return get_storage_service()


@router.post("/upload", response_model=AttachmentUploadResponse)
async def upload_file(
    file: Annotated[UploadFile, File(description="Файл для загрузки")],
    current_user: ActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    storage: Annotated[StorageService, Depends(get_storage)],
) -> AttachmentUploadResponse:
    """
    Upload a single file.

    **Limits:**
    - Images: max 10 MB
    - Documents: max 25 MB
    - Allowed types: JPEG, PNG, GIF, WebP, PDF, DOC, DOCX, TXT
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Имя файла обязательно",
        )

    # Get content type
    content_type = file.content_type or "application/octet-stream"

    # Get file size
    file.file.seek(0, 2)  # Seek to end
    size = file.file.tell()
    file.file.seek(0)  # Reset to beginning

    try:
        # Upload to S3
        result = await storage.upload_file(
            file=file.file,
            filename=file.filename,
            content_type=content_type,
            tenant_id=str(current_user.tenant_id),
            size=size,
        )

        # Determine attachment type
        attachment_type = Attachment.determine_type(content_type)

        # Create attachment record
        attachment = Attachment(
            tenant_id=current_user.tenant_id,
            uploaded_by_id=current_user.id,
            filename=result.key.split("/")[-1],  # Storage filename
            original_filename=file.filename,
            mime_type=content_type,
            size=result.size,
            storage_key=result.key,
            storage_url=result.url,
            checksum=result.checksum,
            attachment_type=attachment_type,
            status=AttachmentStatus.PENDING,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=PENDING_EXPIRATION_HOURS),
        )

        db.add(attachment)
        await db.commit()
        await db.refresh(attachment)

        return AttachmentUploadResponse(
            id=attachment.id,
            filename=attachment.filename,
            original_filename=attachment.original_filename,
            mime_type=attachment.mime_type,
            size=attachment.size,
            url=result.url,
            attachment_type=attachment.attachment_type.value,
        )

    except FileTooLargeError as e:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=str(e),
        )
    except InvalidFileTypeError as e:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=str(e),
        )
    except StorageError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post("/upload/batch", response_model=AttachmentListResponse)
async def upload_files(
    files: Annotated[list[UploadFile], File(description="Файлы для загрузки")],
    current_user: ActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    storage: Annotated[StorageService, Depends(get_storage)],
) -> AttachmentListResponse:
    """
    Upload multiple files at once.

    **Limits:**
    - Max 10 files per request
    - Images: max 10 MB each
    - Documents: max 25 MB each
    """
    if len(files) > MAX_FILES_PER_UPLOAD:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Максимум {MAX_FILES_PER_UPLOAD} файлов за раз",
        )

    attachments: list[AttachmentUploadResponse] = []
    failed: list[dict] = []

    for file in files:
        if not file.filename:
            failed.append({"filename": "unknown", "error": "Имя файла обязательно"})
            continue

        content_type = file.content_type or "application/octet-stream"

        # Get file size
        file.file.seek(0, 2)
        size = file.file.tell()
        file.file.seek(0)

        try:
            # Upload to S3
            result = await storage.upload_file(
                file=file.file,
                filename=file.filename,
                content_type=content_type,
                tenant_id=str(current_user.tenant_id),
                size=size,
            )

            # Determine attachment type
            attachment_type = Attachment.determine_type(content_type)

            # Create attachment record
            attachment = Attachment(
                tenant_id=current_user.tenant_id,
                uploaded_by_id=current_user.id,
                filename=result.key.split("/")[-1],
                original_filename=file.filename,
                mime_type=content_type,
                size=result.size,
                storage_key=result.key,
                storage_url=result.url,
                checksum=result.checksum,
                attachment_type=attachment_type,
                status=AttachmentStatus.PENDING,
                expires_at=datetime.now(timezone.utc) + timedelta(hours=PENDING_EXPIRATION_HOURS),
            )

            db.add(attachment)
            await db.flush()  # Get ID without committing

            attachments.append(
                AttachmentUploadResponse(
                    id=attachment.id,
                    filename=attachment.filename,
                    original_filename=attachment.original_filename,
                    mime_type=attachment.mime_type,
                    size=attachment.size,
                    url=result.url,
                    attachment_type=attachment.attachment_type.value,
                )
            )

        except (FileTooLargeError, InvalidFileTypeError, StorageError) as e:
            failed.append({"filename": file.filename, "error": str(e)})

    # Commit all successful uploads
    await db.commit()

    return AttachmentListResponse(attachments=attachments, failed=failed)


@router.get("/{attachment_id}", response_model=AttachmentResponse)
async def get_attachment(
    attachment_id: UUID,
    current_user: ActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    storage: Annotated[StorageService, Depends(get_storage)],
) -> AttachmentResponse:
    """Get attachment by ID with fresh URL."""
    result = await db.execute(
        select(Attachment)
        .where(Attachment.id == attachment_id)
        .where(Attachment.tenant_id == current_user.tenant_id)
        .where(Attachment.is_deleted == False)
    )
    attachment = result.scalar_one_or_none()

    if not attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Вложение не найдено",
        )

    # Generate fresh URL
    try:
        url = await storage.get_file_url(attachment.storage_key)
    except StorageError:
        url = None

    # Generate thumbnail URL if exists
    thumbnail_url = None
    if attachment.thumbnail_key:
        try:
            thumbnail_url = await storage.get_file_url(attachment.thumbnail_key)
        except StorageError:
            pass

    return AttachmentResponse(
        id=attachment.id,
        filename=attachment.filename,
        original_filename=attachment.original_filename,
        mime_type=attachment.mime_type,
        size=attachment.size,
        attachment_type=attachment.attachment_type.value,
        url=url,
        thumbnail_url=thumbnail_url,
        width=attachment.width,
        height=attachment.height,
        status=attachment.status.value,
        created_at=attachment.created_at,
        updated_at=attachment.updated_at,
    )


@router.delete("/{attachment_id}")
async def delete_attachment(
    attachment_id: UUID,
    current_user: ActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    storage: Annotated[StorageService, Depends(get_storage)],
) -> dict:
    """Delete an attachment (soft delete)."""
    result = await db.execute(
        select(Attachment)
        .where(Attachment.id == attachment_id)
        .where(Attachment.tenant_id == current_user.tenant_id)
        .where(Attachment.is_deleted == False)
    )
    attachment = result.scalar_one_or_none()

    if not attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Вложение не найдено",
        )

    # Only allow deletion of pending attachments (not yet attached to messages)
    if attachment.status != AttachmentStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя удалить прикреплённое к сообщению вложение",
        )

    # Soft delete
    attachment.is_deleted = True
    attachment.deleted_at = datetime.now(timezone.utc)
    attachment.status = AttachmentStatus.DELETED

    # Also delete from S3
    try:
        await storage.delete_file(attachment.storage_key)
        if attachment.thumbnail_key:
            await storage.delete_file(attachment.thumbnail_key)
    except StorageError:
        pass  # Continue even if S3 deletion fails

    await db.commit()

    return {"success": True, "message": "Вложение удалено"}
