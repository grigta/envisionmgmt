"""YandexGPT LLM integration."""

import logging
from typing import AsyncIterator

import httpx

from shared.config import get_settings
from services.ai.llm.base import BaseLLM, LLMMessage, LLMResponse, LLMRole

logger = logging.getLogger(__name__)
settings = get_settings()


class YandexGPTLLM(BaseLLM):
    """YandexGPT API client."""

    def __init__(self, model: str = "yandexgpt-lite"):
        """
        Initialize YandexGPT.

        model: "yandexgpt-lite" (fast) or "yandexgpt" (pro)
        """
        self.api_key = settings.yandex_gpt_api_key
        self.folder_id = settings.yandex_gpt_folder_id
        self.model = model
        self.api_url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
        self.stream_url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completionAsync"

    def _get_model_uri(self) -> str:
        """Get full model URI."""
        return f"gpt://{self.folder_id}/{self.model}/latest"

    def _convert_messages(self, messages: list[LLMMessage]) -> list[dict]:
        """Convert messages to YandexGPT format."""
        result = []
        for msg in messages:
            role = msg.role.value
            # YandexGPT uses 'system' only for first message
            if role == "system" and result:
                role = "user"
            result.append({"role": role, "text": msg.content})
        return result

    async def complete(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> LLMResponse | None:
        """Generate completion."""
        if not self.api_key or not self.folder_id:
            logger.warning("YandexGPT credentials not configured")
            return None

        headers = {
            "Authorization": f"Api-Key {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "modelUri": self._get_model_uri(),
            "completionOptions": {
                "stream": False,
                "temperature": temperature,
                "maxTokens": str(max_tokens),
            },
            "messages": self._convert_messages(messages),
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(
                    self.api_url,
                    headers=headers,
                    json=payload,
                )

                if response.status_code == 200:
                    data = response.json()
                    result = data.get("result", {})
                    alternatives = result.get("alternatives", [])

                    if alternatives:
                        message = alternatives[0].get("message", {})
                        return LLMResponse(
                            content=message.get("text", ""),
                            model=self.model,
                            usage=result.get("usage"),
                            finish_reason=alternatives[0].get("status"),
                        )
                else:
                    logger.error(f"YandexGPT error: {response.status_code} - {response.text}")

            except Exception as e:
                logger.error(f"YandexGPT request error: {e}")

        return None

    async def stream_complete(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> AsyncIterator[str]:
        """Stream completion tokens."""
        if not self.api_key or not self.folder_id:
            logger.warning("YandexGPT credentials not configured")
            return

        headers = {
            "Authorization": f"Api-Key {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "modelUri": self._get_model_uri(),
            "completionOptions": {
                "stream": True,
                "temperature": temperature,
                "maxTokens": str(max_tokens),
            },
            "messages": self._convert_messages(messages),
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                async with client.stream(
                    "POST",
                    self.api_url,
                    headers=headers,
                    json=payload,
                ) as response:
                    if response.status_code != 200:
                        logger.error(f"YandexGPT stream error: {response.status_code}")
                        return

                    async for line in response.aiter_lines():
                        if line:
                            import json

                            try:
                                data = json.loads(line)
                                result = data.get("result", {})
                                alternatives = result.get("alternatives", [])
                                if alternatives:
                                    text = alternatives[0].get("message", {}).get("text", "")
                                    if text:
                                        yield text
                            except json.JSONDecodeError:
                                continue

            except Exception as e:
                logger.error(f"YandexGPT stream error: {e}")
