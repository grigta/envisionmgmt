"""Web widget adapter - mostly handled by widget_api.py, this is for message sending."""

from services.channel.adapters.base import BaseChannelAdapter, UnifiedMessage


class WidgetAdapter(BaseChannelAdapter):
    """Web widget adapter."""

    channel_type = "web"

    async def send_message(
        self,
        channel_user_id: str,
        content_type: str,
        content: dict,
        **kwargs,
    ) -> str | None:
        """
        Send message to web widget.
        This is handled via WebSocket push, not direct API call.
        Returns a generated message ID.
        """
        import uuid

        # Web widget messages are pushed via WebSocket
        # This method is called for completeness but actual delivery
        # happens through the WebSocket connection manager

        return str(uuid.uuid4())

    async def parse_webhook(self, payload: dict) -> UnifiedMessage | None:
        """
        Parse widget message.
        Widget messages come through REST API, not webhooks.
        """
        return UnifiedMessage(
            channel="web",
            channel_message_id=payload.get("message_id", ""),
            channel_user_id=payload.get("visitor_id", ""),
            channel_name=payload.get("name"),
            content_type=payload.get("content_type", "text"),
            content=payload.get("content", {}),
            email=payload.get("email"),
            metadata=payload.get("metadata", {}),
        )

    async def validate_credentials(self, credentials: dict) -> bool:
        """Widget doesn't need external credential validation."""
        return True
