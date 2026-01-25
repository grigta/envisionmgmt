"""S3-compatible storage service for file uploads."""

import hashlib
import mimetypes
import uuid
from datetime import datetime, timedelta, timezone
from typing import BinaryIO

import aioboto3
from botocore.config import Config

from shared.config import get_settings

# File limits
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB
MAX_FILES_PER_UPLOAD = 10

# Allowed file types
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
ALLOWED_DOCUMENT_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
}
ALLOWED_TYPES = ALLOWED_IMAGE_TYPES | ALLOWED_DOCUMENT_TYPES


class StorageError(Exception):
    """Storage operation error."""

    pass


class FileTooLargeError(StorageError):
    """File exceeds size limit."""

    pass


class InvalidFileTypeError(StorageError):
    """File type not allowed."""

    pass


class UploadResult:
    """Result of a file upload."""

    def __init__(
        self,
        key: str,
        url: str,
        filename: str,
        mime_type: str,
        size: int,
        checksum: str,
    ):
        self.key = key
        self.url = url
        self.filename = filename
        self.mime_type = mime_type
        self.size = size
        self.checksum = checksum

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "url": self.url,
            "filename": self.filename,
            "mime_type": self.mime_type,
            "size": self.size,
            "checksum": self.checksum,
        }


class StorageService:
    """S3-compatible storage service."""

    def __init__(self):
        self.settings = get_settings()
        self.session = aioboto3.Session()
        self._client_config = Config(
            signature_version="s3v4",
            s3={"addressing_style": "path"},
        )

    def _get_client(self):
        """Get S3 client context manager."""
        return self.session.client(
            "s3",
            endpoint_url=self.settings.s3_endpoint_url,
            aws_access_key_id=self.settings.s3_access_key_id,
            aws_secret_access_key=self.settings.s3_secret_access_key,
            config=self._client_config,
        )

    def _validate_file(self, filename: str, content_type: str, size: int) -> None:
        """Validate file before upload."""
        # Check content type
        if content_type not in ALLOWED_TYPES:
            raise InvalidFileTypeError(
                f"Тип файла '{content_type}' не поддерживается. "
                f"Разрешённые типы: изображения (JPEG, PNG, GIF, WebP), документы (PDF, DOC, DOCX, TXT)"
            )

        # Check size based on type
        if content_type in ALLOWED_IMAGE_TYPES:
            if size > MAX_IMAGE_SIZE:
                raise FileTooLargeError(
                    f"Изображение слишком большое ({size / 1024 / 1024:.1f} MB). "
                    f"Максимальный размер: {MAX_IMAGE_SIZE / 1024 / 1024:.0f} MB"
                )
        else:
            if size > MAX_FILE_SIZE:
                raise FileTooLargeError(
                    f"Файл слишком большой ({size / 1024 / 1024:.1f} MB). "
                    f"Максимальный размер: {MAX_FILE_SIZE / 1024 / 1024:.0f} MB"
                )

    def _generate_key(self, tenant_id: str, filename: str, content_type: str) -> str:
        """Generate unique S3 key for file."""
        # Determine folder based on content type
        if content_type in ALLOWED_IMAGE_TYPES:
            folder = "images"
        else:
            folder = "documents"

        # Generate unique ID
        file_id = uuid.uuid4().hex[:12]

        # Get extension
        ext = mimetypes.guess_extension(content_type) or ""
        if not ext and "." in filename:
            ext = "." + filename.rsplit(".", 1)[-1].lower()

        # Build key: tenants/{tenant_id}/{folder}/{date}/{file_id}{ext}
        date_path = datetime.now(timezone.utc).strftime("%Y/%m/%d")
        return f"tenants/{tenant_id}/{folder}/{date_path}/{file_id}{ext}"

    async def upload_file(
        self,
        file: BinaryIO,
        filename: str,
        content_type: str,
        tenant_id: str,
        size: int | None = None,
    ) -> UploadResult:
        """Upload file to S3.

        Args:
            file: File-like object with read() method
            filename: Original filename
            content_type: MIME type of file
            tenant_id: Tenant ID for path organization
            size: File size in bytes (optional, will be calculated if not provided)

        Returns:
            UploadResult with file info

        Raises:
            FileTooLargeError: If file exceeds size limit
            InvalidFileTypeError: If file type not allowed
            StorageError: If upload fails
        """
        # Read file data
        data = file.read()
        actual_size = len(data)

        # Use provided size or calculated size
        file_size = size if size is not None else actual_size

        # Validate
        self._validate_file(filename, content_type, file_size)

        # Generate S3 key
        key = self._generate_key(tenant_id, filename, content_type)

        # Calculate checksum
        checksum = hashlib.md5(data).hexdigest()

        # Upload to S3
        try:
            async with self._get_client() as s3:
                await s3.put_object(
                    Bucket=self.settings.s3_bucket_name,
                    Key=key,
                    Body=data,
                    ContentType=content_type,
                    ContentDisposition=f'attachment; filename="{filename}"',
                    Metadata={
                        "original-filename": filename,
                        "tenant-id": tenant_id,
                        "checksum": checksum,
                    },
                )
        except Exception as e:
            raise StorageError(f"Ошибка загрузки файла: {str(e)}") from e

        # Generate URL
        url = await self.get_file_url(key)

        return UploadResult(
            key=key,
            url=url,
            filename=filename,
            mime_type=content_type,
            size=actual_size,
            checksum=checksum,
        )

    async def get_file_url(self, key: str, expires_in: int = 3600) -> str:
        """Generate pre-signed URL for file access.

        Args:
            key: S3 object key
            expires_in: URL expiration time in seconds (default 1 hour)

        Returns:
            Pre-signed URL for file access
        """
        try:
            async with self._get_client() as s3:
                url = await s3.generate_presigned_url(
                    "get_object",
                    Params={
                        "Bucket": self.settings.s3_bucket_name,
                        "Key": key,
                    },
                    ExpiresIn=expires_in,
                )
                return url
        except Exception as e:
            raise StorageError(f"Ошибка генерации URL: {str(e)}") from e

    async def delete_file(self, key: str) -> bool:
        """Delete file from S3.

        Args:
            key: S3 object key

        Returns:
            True if deleted successfully
        """
        try:
            async with self._get_client() as s3:
                await s3.delete_object(
                    Bucket=self.settings.s3_bucket_name,
                    Key=key,
                )
                return True
        except Exception as e:
            raise StorageError(f"Ошибка удаления файла: {str(e)}") from e

    async def file_exists(self, key: str) -> bool:
        """Check if file exists in S3.

        Args:
            key: S3 object key

        Returns:
            True if file exists
        """
        try:
            async with self._get_client() as s3:
                await s3.head_object(
                    Bucket=self.settings.s3_bucket_name,
                    Key=key,
                )
                return True
        except Exception:
            return False


# Global instance
_storage_service: StorageService | None = None


def get_storage_service() -> StorageService:
    """Get storage service instance."""
    global _storage_service
    if _storage_service is None:
        _storage_service = StorageService()
    return _storage_service
