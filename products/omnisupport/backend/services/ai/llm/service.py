"""Unified LLM service with provider selection."""

import logging

from shared.config import get_settings
from services.ai.llm.base import BaseLLM, LLMMessage, LLMResponse, LLMRole
from services.ai.llm.yandexgpt import YandexGPTLLM
from services.ai.llm.gigachat import GigaChatLLM
from services.ai.llm.anthropic import AnthropicLLM
from services.ai.llm.openai import OpenAILLM

logger = logging.getLogger(__name__)
settings = get_settings()


class LLMService:
    """Unified LLM service with automatic provider selection."""

    def __init__(self, preferred_provider: str | None = None):
        """
        Initialize LLM service.

        preferred_provider: "yandexgpt", "gigachat", or None for auto-select
        """
        self.preferred_provider = preferred_provider
        self._provider: BaseLLM | None = None

    def _get_provider(self) -> BaseLLM | None:
        """Get LLM provider based on configuration."""
        if self._provider is not None:
            return self._provider

        # Use preferred provider if specified and configured
        if self.preferred_provider == "yandexgpt":
            if settings.yandex_gpt_api_key and settings.yandex_gpt_folder_id:
                self._provider = YandexGPTLLM()
                logger.info("Using YandexGPT LLM")
                return self._provider

        if self.preferred_provider == "gigachat":
            if settings.gigachat_client_id and settings.gigachat_client_secret:
                self._provider = GigaChatLLM()
                logger.info("Using GigaChat LLM")
                return self._provider

        if self.preferred_provider == "anthropic" or self.preferred_provider == "claude":
            if settings.anthropic_api_key:
                self._provider = AnthropicLLM()
                logger.info("Using Anthropic Claude LLM")
                return self._provider

        if self.preferred_provider == "openai" or self.preferred_provider == "gpt":
            if settings.openai_api_key:
                self._provider = OpenAILLM()
                logger.info("Using OpenAI GPT LLM")
                return self._provider

        # Auto-select: try Claude first, then OpenAI, then YandexGPT, then GigaChat
        if settings.anthropic_api_key:
            self._provider = AnthropicLLM()
            logger.info("Using Anthropic Claude LLM (auto-selected)")
        elif settings.openai_api_key:
            self._provider = OpenAILLM()
            logger.info("Using OpenAI GPT LLM (auto-selected)")
        elif settings.yandex_gpt_api_key and settings.yandex_gpt_folder_id:
            self._provider = YandexGPTLLM()
            logger.info("Using YandexGPT LLM (auto-selected)")
        elif settings.gigachat_client_id and settings.gigachat_client_secret:
            self._provider = GigaChatLLM()
            logger.info("Using GigaChat LLM (auto-selected)")
        else:
            logger.warning("No LLM provider configured")

        return self._provider

    async def complete(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> LLMResponse | None:
        """Generate completion."""
        provider = self._get_provider()
        if not provider:
            return None
        return await provider.complete(messages, temperature, max_tokens)

    async def simple_complete(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> str | None:
        """Simple completion with string prompt."""
        provider = self._get_provider()
        if not provider:
            return None
        return await provider.simple_complete(prompt, system_prompt, temperature, max_tokens)

    async def generate_suggestions(
        self,
        customer_message: str,
        context: str = "",
        num_suggestions: int = 3,
    ) -> list[str]:
        """Generate response suggestions for operator."""
        system_prompt = """Ты помощник оператора поддержки.
Твоя задача - предложить варианты ответов на сообщение клиента.
Ответы должны быть вежливыми, профессиональными и по существу.
Используй предоставленный контекст из базы знаний.
Дай ровно {n} варианта ответа, каждый с новой строки, начиная с числа и точки."""

        prompt = f"""Сообщение клиента: {customer_message}

Контекст из базы знаний:
{context if context else "Контекст не найден"}

Предложи {num_suggestions} варианта ответа:"""

        response = await self.simple_complete(
            prompt,
            system_prompt.format(n=num_suggestions),
            temperature=0.8,
            max_tokens=500,
        )

        if not response:
            return []

        # Parse numbered responses
        suggestions = []
        lines = response.strip().split("\n")
        current = []

        for line in lines:
            line = line.strip()
            if line and line[0].isdigit() and "." in line[:3]:
                if current:
                    suggestions.append(" ".join(current))
                current = [line.split(".", 1)[1].strip()]
            elif current:
                current.append(line)

        if current:
            suggestions.append(" ".join(current))

        return suggestions[:num_suggestions]

    async def summarize_conversation(
        self,
        messages: list[dict],
        max_length: int = 200,
    ) -> str | None:
        """Summarize a conversation."""
        system_prompt = """Ты помощник для создания кратких саммари диалогов поддержки.
Выдели ключевые моменты: проблему клиента, предпринятые действия, результат.
Саммари должно быть на русском языке, кратким и информативным."""

        # Format messages
        formatted = []
        for msg in messages:
            sender = "Клиент" if msg.get("sender") == "customer" else "Оператор"
            text = msg.get("text", "")[:500]
            formatted.append(f"{sender}: {text}")

        conversation_text = "\n".join(formatted[-20:])  # Last 20 messages

        prompt = f"""Создай краткое саммари диалога (максимум {max_length} символов):

{conversation_text}

Саммари:"""

        return await self.simple_complete(
            prompt,
            system_prompt,
            temperature=0.3,
            max_tokens=300,
        )

    async def analyze_sentiment(
        self,
        text: str,
    ) -> dict | None:
        """Analyze sentiment of text."""
        system_prompt = """Проанализируй эмоциональный тон сообщения клиента.
Верни JSON в формате: {"sentiment": "positive|neutral|negative", "score": 0.0-1.0, "emotions": ["emotion1", "emotion2"]}
Только JSON, без пояснений."""

        prompt = f"Сообщение: {text[:1000]}"

        response = await self.simple_complete(
            prompt,
            system_prompt,
            temperature=0.1,
            max_tokens=100,
        )

        if response:
            import json

            try:
                # Extract JSON from response
                start = response.find("{")
                end = response.rfind("}") + 1
                if start >= 0 and end > start:
                    return json.loads(response[start:end])
            except json.JSONDecodeError:
                pass

        return None

    async def classify_intent(
        self,
        message: str,
        intents: list[str],
    ) -> str | None:
        """Classify message intent from predefined list."""
        system_prompt = f"""Определи намерение клиента из списка: {', '.join(intents)}.
Верни только название намерения, без пояснений."""

        prompt = f"Сообщение клиента: {message[:500]}"

        response = await self.simple_complete(
            prompt,
            system_prompt,
            temperature=0.1,
            max_tokens=50,
        )

        if response:
            response = response.strip().lower()
            for intent in intents:
                if intent.lower() in response:
                    return intent

        return None


# Singleton
_llm_service: LLMService | None = None


def get_llm_service(preferred_provider: str | None = None) -> LLMService:
    """Get LLM service singleton."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService(preferred_provider)
    return _llm_service
