"""WhatsApp Business API adapter."""

from datetime import datetime, timezone

import httpx

from services.channel.adapters.base import BaseChannelAdapter, UnifiedMessage


class WhatsAppAdapter(BaseChannelAdapter):
    """WhatsApp Business API adapter."""

    channel_type = "whatsapp"

    def __init__(self, api_url: str, api_token: str, phone_number_id: str):
        self.api_url = api_url.rstrip("/")
        self.api_token = api_token
        self.phone_number_id = phone_number_id

    async def send_message(
        self,
        channel_user_id: str,
        content_type: str,
        content: dict,
        **kwargs,
    ) -> str | None:
        """Send message via WhatsApp Business API."""
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient() as client:
            try:
                if content_type == "text":
                    payload = {
                        "messaging_product": "whatsapp",
                        "to": channel_user_id,
                        "type": "text",
                        "text": {"body": content.get("text", "")},
                    }
                elif content_type == "image":
                    payload = {
                        "messaging_product": "whatsapp",
                        "to": channel_user_id,
                        "type": "image",
                        "image": {
                            "link": content.get("url"),
                            "caption": content.get("caption"),
                        },
                    }
                elif content_type == "file":
                    payload = {
                        "messaging_product": "whatsapp",
                        "to": channel_user_id,
                        "type": "document",
                        "document": {
                            "link": content.get("url"),
                            "filename": content.get("filename"),
                        },
                    }
                else:
                    return None

                response = await client.post(
                    f"{self.api_url}/{self.phone_number_id}/messages",
                    headers=headers,
                    json=payload,
                )

                if response.status_code == 200:
                    result = response.json()
                    messages = result.get("messages", [])
                    if messages:
                        return messages[0].get("id")

            except Exception as e:
                print(f"WhatsApp send error: {e}")

        return None

    async def parse_webhook(self, payload: dict) -> UnifiedMessage | None:
        """Parse WhatsApp webhook payload."""
        # WhatsApp Cloud API webhook structure
        entry = payload.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})

        messages = value.get("messages", [])
        if not messages:
            return None

        message = messages[0]
        contacts = value.get("contacts", [{}])
        contact = contacts[0] if contacts else {}

        # Get message type
        msg_type = message.get("type", "text")
        content_type = "text"
        content = {}

        if msg_type == "text":
            content_type = "text"
            content = {"text": message.get("text", {}).get("body", "")}
        elif msg_type == "image":
            content_type = "image"
            image = message.get("image", {})
            content = {
                "media_id": image.get("id"),
                "mime_type": image.get("mime_type"),
                "caption": image.get("caption"),
            }
        elif msg_type == "document":
            content_type = "file"
            doc = message.get("document", {})
            content = {
                "media_id": doc.get("id"),
                "filename": doc.get("filename"),
                "mime_type": doc.get("mime_type"),
            }
        elif msg_type == "audio":
            content_type = "audio"
            audio = message.get("audio", {})
            content = {
                "media_id": audio.get("id"),
                "mime_type": audio.get("mime_type"),
            }
        elif msg_type == "location":
            content_type = "location"
            loc = message.get("location", {})
            content = {
                "latitude": loc.get("latitude"),
                "longitude": loc.get("longitude"),
                "name": loc.get("name"),
                "address": loc.get("address"),
            }

        # Parse timestamp
        timestamp = None
        if message.get("timestamp"):
            timestamp = datetime.fromtimestamp(int(message["timestamp"]), tz=timezone.utc)

        return UnifiedMessage(
            channel="whatsapp",
            channel_message_id=message.get("id", ""),
            channel_user_id=message.get("from", ""),
            channel_name=contact.get("profile", {}).get("name"),
            phone=message.get("from"),
            content_type=content_type,
            content=content,
            timestamp=timestamp,
            metadata={
                "wa_id": contact.get("wa_id"),
            },
        )

    async def validate_credentials(self, credentials: dict) -> bool:
        """Validate WhatsApp API credentials."""
        api_token = credentials.get("api_token")
        phone_number_id = credentials.get("phone_number_id")

        if not api_token or not phone_number_id:
            return False

        headers = {"Authorization": f"Bearer {api_token}"}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"https://graph.facebook.com/v18.0/{phone_number_id}",
                    headers=headers,
                )
                return response.status_code == 200
            except Exception:
                pass

        return False

    async def download_media(self, media_id: str) -> bytes | None:
        """Download media file from WhatsApp."""
        headers = {"Authorization": f"Bearer {self.api_token}"}

        async with httpx.AsyncClient() as client:
            try:
                # Get media URL
                response = await client.get(
                    f"https://graph.facebook.com/v18.0/{media_id}",
                    headers=headers,
                )
                if response.status_code != 200:
                    return None

                media_url = response.json().get("url")
                if not media_url:
                    return None

                # Download media
                response = await client.get(media_url, headers=headers)
                if response.status_code == 200:
                    return response.content

            except Exception:
                pass

        return None
