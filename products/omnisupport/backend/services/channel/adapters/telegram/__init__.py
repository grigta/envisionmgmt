"""Telegram channel adapter."""

from datetime import datetime, timezone
from typing import Any

import httpx

from services.channel.adapters.base import BaseChannelAdapter, UnifiedMessage


class TelegramAdapter(BaseChannelAdapter):
    """Telegram Bot API adapter."""

    channel_type = "telegram"

    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.api_base = f"https://api.telegram.org/bot{bot_token}"

    async def send_message(
        self,
        channel_user_id: str,
        content_type: str,
        content: dict,
        reply_to_message_id: str | None = None,
        **kwargs,
    ) -> str | None:
        """Send message via Telegram Bot API."""
        async with httpx.AsyncClient() as client:
            try:
                if content_type == "text":
                    response = await client.post(
                        f"{self.api_base}/sendMessage",
                        json={
                            "chat_id": channel_user_id,
                            "text": content.get("text", ""),
                            "parse_mode": "HTML",
                            "reply_to_message_id": reply_to_message_id,
                        },
                    )
                elif content_type == "image":
                    response = await client.post(
                        f"{self.api_base}/sendPhoto",
                        json={
                            "chat_id": channel_user_id,
                            "photo": content.get("url"),
                            "caption": content.get("caption"),
                        },
                    )
                elif content_type == "file":
                    response = await client.post(
                        f"{self.api_base}/sendDocument",
                        json={
                            "chat_id": channel_user_id,
                            "document": content.get("url"),
                            "caption": content.get("caption"),
                        },
                    )
                else:
                    return None

                if response.status_code == 200:
                    result = response.json()
                    if result.get("ok"):
                        return str(result["result"]["message_id"])

            except Exception as e:
                print(f"Telegram send error: {e}")

        return None

    async def parse_webhook(self, payload: dict) -> UnifiedMessage | None:
        """Parse Telegram webhook update."""
        # Handle different update types
        message = payload.get("message") or payload.get("edited_message")

        if not message:
            return None

        chat = message.get("chat", {})
        from_user = message.get("from", {})

        # Determine content type
        content_type = "text"
        content = {}

        if "text" in message:
            content_type = "text"
            content = {"text": message["text"]}
        elif "photo" in message:
            content_type = "image"
            # Get largest photo
            photo = max(message["photo"], key=lambda p: p.get("file_size", 0))
            content = {
                "file_id": photo["file_id"],
                "caption": message.get("caption"),
            }
        elif "document" in message:
            content_type = "file"
            doc = message["document"]
            content = {
                "file_id": doc["file_id"],
                "filename": doc.get("file_name"),
                "mime_type": doc.get("mime_type"),
                "file_size": doc.get("file_size"),
            }
        elif "voice" in message:
            content_type = "audio"
            voice = message["voice"]
            content = {
                "file_id": voice["file_id"],
                "duration": voice.get("duration"),
            }
        elif "sticker" in message:
            content_type = "sticker"
            sticker = message["sticker"]
            content = {
                "file_id": sticker["file_id"],
                "emoji": sticker.get("emoji"),
            }
        elif "location" in message:
            content_type = "location"
            loc = message["location"]
            content = {
                "latitude": loc["latitude"],
                "longitude": loc["longitude"],
            }
        elif "contact" in message:
            content_type = "contact"
            contact = message["contact"]
            content = {
                "phone": contact.get("phone_number"),
                "name": f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip(),
            }

        return UnifiedMessage(
            channel="telegram",
            channel_message_id=str(message["message_id"]),
            channel_user_id=str(chat["id"]),
            channel_username=from_user.get("username"),
            channel_name=f"{from_user.get('first_name', '')} {from_user.get('last_name', '')}".strip(),
            content_type=content_type,
            content=content,
            phone=from_user.get("phone_number"),
            timestamp=datetime.fromtimestamp(message["date"], tz=timezone.utc),
            metadata={
                "chat_type": chat.get("type"),
                "language_code": from_user.get("language_code"),
            },
        )

    async def validate_credentials(self, credentials: dict) -> bool:
        """Validate Telegram bot token."""
        token = credentials.get("bot_token")
        if not token:
            return False

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"https://api.telegram.org/bot{token}/getMe"
                )
                if response.status_code == 200:
                    result = response.json()
                    return result.get("ok", False)
            except Exception:
                pass

        return False

    async def setup_webhook(self, webhook_url: str, credentials: dict) -> bool:
        """Set up Telegram webhook."""
        token = credentials.get("bot_token")
        secret = credentials.get("webhook_secret", "")

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"https://api.telegram.org/bot{token}/setWebhook",
                    json={
                        "url": webhook_url,
                        "secret_token": secret,
                        "allowed_updates": ["message", "edited_message"],
                    },
                )
                if response.status_code == 200:
                    result = response.json()
                    return result.get("ok", False)
            except Exception:
                pass

        return False

    async def remove_webhook(self, credentials: dict) -> bool:
        """Remove Telegram webhook."""
        token = credentials.get("bot_token")

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"https://api.telegram.org/bot{token}/deleteWebhook"
                )
                if response.status_code == 200:
                    result = response.json()
                    return result.get("ok", False)
            except Exception:
                pass

        return False

    async def get_file_url(self, file_id: str) -> str | None:
        """Get download URL for a file."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.api_base}/getFile",
                    params={"file_id": file_id},
                )
                if response.status_code == 200:
                    result = response.json()
                    if result.get("ok"):
                        file_path = result["result"]["file_path"]
                        return f"https://api.telegram.org/file/bot{self.bot_token}/{file_path}"
            except Exception:
                pass

        return None
