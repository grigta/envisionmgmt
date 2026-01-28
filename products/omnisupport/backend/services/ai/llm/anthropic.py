"""Anthropic Claude LLM provider."""

import logging
from typing import Optional

import httpx

from shared.config import get_settings
from services.ai.llm.base import BaseLLM, LLMMessage, LLMResponse, LLMRole

logger = logging.getLogger(__name__)
settings = get_settings()


class AnthropicLLM(BaseLLM):
    """Anthropic Claude LLM provider."""

    MODELS = {
        "claude-3-opus": "claude-3-opus-20240229",
        "claude-3-sonnet": "claude-3-5-sonnet-20241022",
        "claude-3-haiku": "claude-3-haiku-20240307",
        "claude-4-sonnet": "claude-sonnet-4-20250514",
    }

    def __init__(self, model: str = "claude-3-sonnet"):
        """Initialize Anthropic provider."""
        self.api_key = settings.anthropic_api_key
        self.model = self.MODELS.get(model, model)
        self.base_url = "https://api.anthropic.com/v1"
        
        if not self.api_key:
            logger.warning("Anthropic API key not configured")

    async def complete(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> Optional[LLMResponse]:
        """Generate completion using Claude."""
        if not self.api_key:
            return None

        # Extract system message
        system_message = None
        chat_messages = []
        
        for msg in messages:
            if msg.role == LLMRole.SYSTEM:
                system_message = msg.content
            else:
                chat_messages.append({
                    "role": "user" if msg.role == LLMRole.USER else "assistant",
                    "content": msg.content,
                })

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/messages",
                    headers={
                        "x-api-key": self.api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "max_tokens": max_tokens,
                        "temperature": temperature,
                        "system": system_message or "You are a helpful assistant.",
                        "messages": chat_messages,
                    },
                )
                response.raise_for_status()
                data = response.json()

                content = data.get("content", [])
                text = content[0].get("text", "") if content else ""
                
                return LLMResponse(
                    content=text,
                    model=self.model,
                    usage={
                        "input_tokens": data.get("usage", {}).get("input_tokens", 0),
                        "output_tokens": data.get("usage", {}).get("output_tokens", 0),
                    },
                )

        except httpx.HTTPStatusError as e:
            logger.error(f"Anthropic API error: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Anthropic request failed: {e}")
            return None

    async def simple_complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> Optional[str]:
        """Simple completion with string prompt."""
        messages = []
        if system_prompt:
            messages.append(LLMMessage(role=LLMRole.SYSTEM, content=system_prompt))
        messages.append(LLMMessage(role=LLMRole.USER, content=prompt))

        response = await self.complete(messages, temperature, max_tokens)
        return response.content if response else None
