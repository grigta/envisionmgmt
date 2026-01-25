"""Base LLM interface and types."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum


class LLMRole(str, Enum):
    """Message role in conversation."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class LLMMessage:
    """Chat message for LLM."""

    role: LLMRole
    content: str


@dataclass
class LLMResponse:
    """LLM completion response."""

    content: str
    model: str
    usage: dict | None = None
    finish_reason: str | None = None


class BaseLLM(ABC):
    """Base class for LLM providers."""

    @abstractmethod
    async def complete(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> LLMResponse | None:
        """Generate completion for messages."""
        pass

    @abstractmethod
    async def stream_complete(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ):
        """Stream completion tokens."""
        pass

    async def simple_complete(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> str | None:
        """Simple completion with string prompt."""
        messages = []
        if system_prompt:
            messages.append(LLMMessage(role=LLMRole.SYSTEM, content=system_prompt))
        messages.append(LLMMessage(role=LLMRole.USER, content=prompt))

        response = await self.complete(messages, temperature, max_tokens)
        return response.content if response else None
