"""
Mock AI providers for testing.

Provides mock implementations of AI providers that return
canned responses instantly, suitable for GUI testing.
"""

from typing import AsyncIterator

from src.ai.gateway import (
    AICapability,
    AIMessage,
    AIResponse,
    AIStreamChunk,
    GenerationConfig,
)
from src.ai.providers.base import BaseProvider


class MockAIProvider(BaseProvider):
    """
    Mock AI provider for testing.

    Returns configurable canned responses instantly,
    allowing GUI tests to run without real AI calls.
    """

    name = "mock"
    display_name = "Mock Provider"
    capabilities = {
        AICapability.TEXT_GENERATION,
        AICapability.CHAT,
        AICapability.CODE_GENERATION,
    }

    def __init__(
        self,
        response_text: str = "This is a mock AI response for testing.",
        model_name: str = "mock-model-v1",
    ):
        super().__init__()
        self.response_text = response_text
        self.model_name = model_name
        self._is_initialized = True
        self._is_available = True

        # Track calls for assertions in tests
        self.generate_calls: list[dict] = []
        self.chat_calls: list[dict] = []

    async def initialize(self) -> bool:
        """Initialize the mock provider (always succeeds)."""
        self._is_initialized = True
        self._is_available = True
        return True

    def is_available(self) -> bool:
        """Check if provider is available (always True)."""
        return self._is_available

    async def generate(
        self,
        prompt: str,
        config: GenerationConfig,
    ) -> AIResponse:
        """Generate a mock response."""
        # Track the call
        self.generate_calls.append({
            "prompt": prompt,
            "config": config,
        })

        return AIResponse(
            content=self.response_text,
            provider=self.name,
            model=self.model_name,
            usage={
                "prompt_tokens": len(prompt.split()),
                "completion_tokens": len(self.response_text.split()),
                "total_tokens": len(prompt.split()) + len(self.response_text.split()),
            },
            finish_reason="stop",
        )

    async def chat(
        self,
        messages: list[AIMessage],
        config: GenerationConfig,
    ) -> AIResponse:
        """Generate a mock chat response."""
        # Track the call
        self.chat_calls.append({
            "messages": [m.to_dict() for m in messages],
            "config": config,
        })

        return AIResponse(
            content=self.response_text,
            provider=self.name,
            model=self.model_name,
            usage={
                "prompt_tokens": sum(len(m.content.split()) for m in messages),
                "completion_tokens": len(self.response_text.split()),
                "total_tokens": sum(len(m.content.split()) for m in messages) + len(self.response_text.split()),
            },
            finish_reason="stop",
        )

    async def chat_stream(
        self,
        messages: list[AIMessage],
        config: GenerationConfig,
    ) -> AsyncIterator[AIStreamChunk]:
        """Stream a mock chat response word by word."""
        words = self.response_text.split()

        for i, word in enumerate(words):
            is_final = i == len(words) - 1
            yield AIStreamChunk(
                content=word + (" " if not is_final else ""),
                is_final=is_final,
                usage={"total_tokens": len(words)} if is_final else None,
            )

    def get_models(self) -> list[dict]:
        """Get available mock models."""
        return [
            {
                "id": self.model_name,
                "name": "Mock Model",
                "description": "A mock model for testing",
                "context_length": 4096,
            }
        ]

    def reset(self):
        """Reset call tracking for test isolation."""
        self.generate_calls.clear()
        self.chat_calls.clear()


class FailingAIProvider(BaseProvider):
    """
    Mock provider that always fails.

    Useful for testing error handling and fallback behavior.
    """

    name = "failing"
    display_name = "Failing Provider"
    capabilities = {AICapability.TEXT_GENERATION, AICapability.CHAT}

    def __init__(self, error_message: str = "Mock provider failure"):
        super().__init__()
        self.error_message = error_message
        self._is_initialized = True
        self._is_available = True

    async def initialize(self) -> bool:
        return True

    def is_available(self) -> bool:
        return self._is_available

    async def generate(
        self,
        prompt: str,
        config: GenerationConfig,
    ) -> AIResponse:
        raise RuntimeError(self.error_message)

    async def chat(
        self,
        messages: list[AIMessage],
        config: GenerationConfig,
    ) -> AIResponse:
        raise RuntimeError(self.error_message)


class SlowAIProvider(MockAIProvider):
    """
    Mock provider with configurable delay.

    Useful for testing loading states and timeouts.
    """

    name = "slow"
    display_name = "Slow Provider"

    def __init__(self, delay_seconds: float = 1.0, **kwargs):
        super().__init__(**kwargs)
        self.delay_seconds = delay_seconds

    async def generate(
        self,
        prompt: str,
        config: GenerationConfig,
    ) -> AIResponse:
        import asyncio
        await asyncio.sleep(self.delay_seconds)
        return await super().generate(prompt, config)

    async def chat(
        self,
        messages: list[AIMessage],
        config: GenerationConfig,
    ) -> AIResponse:
        import asyncio
        await asyncio.sleep(self.delay_seconds)
        return await super().chat(messages, config)
