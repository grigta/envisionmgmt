"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from typing import Any

from pydantic import PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    debug: bool = False
    environment: str = "development"
    api_v1_prefix: str = "/api/v1"
    app_name: str = "OmniSupport"

    # Database
    database_url: PostgresDsn

    # Redis
    redis_url: RedisDsn

    # Qdrant
    qdrant_url: str = "http://localhost:6333"

    # JWT
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            import json

            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [origin.strip() for origin in v.split(",")]
        return v

    # LLM Providers
    yandex_gpt_api_key: str | None = None
    yandex_gpt_folder_id: str | None = None
    gigachat_client_id: str | None = None
    gigachat_client_secret: str | None = None

    # Telegram
    telegram_bot_token: str | None = None

    # WhatsApp
    whatsapp_api_url: str | None = None
    whatsapp_api_token: str | None = None

    # S3 Storage
    s3_endpoint_url: str | None = None
    s3_access_key_id: str | None = None
    s3_secret_access_key: str | None = None
    s3_bucket_name: str = "omnisupport"

    # SMTP Email
    smtp_host: str = "localhost"
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_from: str | None = None
    smtp_tls: bool = False

    # Qdrant (vector DB)
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333

    @property
    def async_database_url(self) -> str:
        """Get the async database URL."""
        return str(self.database_url)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()  # type: ignore[call-arg]
