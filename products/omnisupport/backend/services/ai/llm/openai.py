"""OpenAI GPT LLM provider."""

import logging
from typing import Optional

import httpx

from shared.config import get_settings
from services.ai.llm.base import BaseLLM, LLMMessage, LLMResponse, LLMRole

logger = logging.getLogger(__name__)
settings = get_settings()


class OpenAILLM(BaseLLM):
    """OpenAI GPT LLM provider."""

    MODELS = {
        "gpt-4": "gpt-4",
        "gpt-4-turbo": "gpt-4-turbo-preview",
        "gpt-4o": "gpt-4o",
        "gpt-4o-mini": "gpt-4o-mini",
        "gpt-3.5-turbo": "gpt-3.5-turbo",
    }

    def __init__(self, model: str = "gpt-4o-mini"):
        """Initialize OpenAI provider."""
        self.api_key = settings.openai_api_key
        self.model = self.MODELS.get(model, model)
        self.base_url = "https://api.openai.com/v1"
        
        if not self.api_key:
            logger.warning("OpenAI API key not configured")

    async def complete(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> Optional[LLMResponse]:
        """Generate completion using OpenAI."""
        if not self.api_key:
            return None

        # Convert messages to OpenAI format
        openai_messages = []
        for msg in messages:
            role = "system" if msg.role == LLMRole.SYSTEM else (
                "user" if msg.role == LLMRole.USER else "assistant"
            )
            openai_messages.append({
                "role": role,
                "content": msg.content,
            })

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": openai_messages,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                    },
                )
                response.raise_for_status()
                data = response.json()

                choices = data.get("choices", [])
                content = choices[0].get("message", {}).get("content", "") if choices else ""
                
                return LLMResponse(
                    content=content,
                    model=self.model,
                    usage={
                        "prompt_tokens": data.get("usage", {}).get("prompt_tokens", 0),
                        "completion_tokens": data.get("usage", {}).get("completion_tokens", 0),
                        "total_tokens": data.get("usage", {}).get("total_tokens", 0),
                    },
                )

        except httpx.HTTPStatusError as e:
            logger.error(f"OpenAI API error: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"OpenAI request failed: {e}")
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
