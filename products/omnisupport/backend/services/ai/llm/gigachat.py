"""GigaChat LLM integration."""

import base64
import logging
import uuid
from typing import AsyncIterator

import httpx

from shared.config import get_settings
from services.ai.llm.base import BaseLLM, LLMMessage, LLMResponse, LLMRole

logger = logging.getLogger(__name__)
settings = get_settings()


class GigaChatLLM(BaseLLM):
    """GigaChat API client."""

    def __init__(self, model: str = "GigaChat"):
        """
        Initialize GigaChat.

        model: "GigaChat" (lite), "GigaChat-Plus", "GigaChat-Pro"
        """
        self.client_id = settings.gigachat_client_id
        self.client_secret = settings.gigachat_client_secret
        self.model = model
        self.auth_url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
        self.api_url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
        self._access_token: str | None = None
        self._token_expires: float = 0

    async def _get_access_token(self) -> str | None:
        """Get or refresh access token."""
        import time

        # Return cached token if valid
        if self._access_token and time.time() < self._token_expires - 60:
            return self._access_token

        if not self.client_id or not self.client_secret:
            return None

        credentials = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()

        # GigaChat requires SSL verification disabled for their cert
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            try:
                response = await client.post(
                    self.auth_url,
                    headers={
                        "Authorization": f"Basic {credentials}",
                        "Content-Type": "application/x-www-form-urlencoded",
                        "RqUID": str(uuid.uuid4()),
                    },
                    data={"scope": "GIGACHAT_API_PERS"},
                )

                if response.status_code == 200:
                    data = response.json()
                    self._access_token = data["access_token"]
                    self._token_expires = data.get("expires_at", time.time() + 1800) / 1000
                    return self._access_token
                else:
                    logger.error(f"GigaChat auth error: {response.status_code} - {response.text}")

            except Exception as e:
                logger.error(f"GigaChat auth request error: {e}")

        return None

    def _convert_messages(self, messages: list[LLMMessage]) -> list[dict]:
        """Convert messages to GigaChat format."""
        return [
            {"role": msg.role.value, "content": msg.content}
            for msg in messages
        ]

    async def complete(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> LLMResponse | None:
        """Generate completion."""
        token = await self._get_access_token()
        if not token:
            logger.warning("GigaChat credentials not configured")
            return None

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": self._convert_messages(messages),
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }

        async with httpx.AsyncClient(verify=False, timeout=120.0) as client:
            try:
                response = await client.post(
                    self.api_url,
                    headers=headers,
                    json=payload,
                )

                if response.status_code == 200:
                    data = response.json()
                    choices = data.get("choices", [])

                    if choices:
                        message = choices[0].get("message", {})
                        return LLMResponse(
                            content=message.get("content", ""),
                            model=data.get("model", self.model),
                            usage=data.get("usage"),
                            finish_reason=choices[0].get("finish_reason"),
                        )
                else:
                    logger.error(f"GigaChat error: {response.status_code} - {response.text}")

            except Exception as e:
                logger.error(f"GigaChat request error: {e}")

        return None

    async def stream_complete(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> AsyncIterator[str]:
        """Stream completion tokens."""
        token = await self._get_access_token()
        if not token:
            logger.warning("GigaChat credentials not configured")
            return

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": self._convert_messages(messages),
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }

        async with httpx.AsyncClient(verify=False, timeout=120.0) as client:
            try:
                async with client.stream(
                    "POST",
                    self.api_url,
                    headers=headers,
                    json=payload,
                ) as response:
                    if response.status_code != 200:
                        logger.error(f"GigaChat stream error: {response.status_code}")
                        return

                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:]
                            if data_str == "[DONE]":
                                break

                            import json

                            try:
                                data = json.loads(data_str)
                                choices = data.get("choices", [])
                                if choices:
                                    delta = choices[0].get("delta", {})
                                    content = delta.get("content", "")
                                    if content:
                                        yield content
                            except json.JSONDecodeError:
                                continue

            except Exception as e:
                logger.error(f"GigaChat stream error: {e}")
