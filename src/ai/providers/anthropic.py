"""
Anthropic Provider - Claude API integration.

Supports Claude 3 models with long context and vision.
"""

import os
from collections.abc import AsyncIterator

from src.ai.gateway import (
    AICapability,
    AIMessage,
    AIResponse,
    AIStreamChunk,
    GenerationConfig,
    StreamInterruptedError,
)
from src.ai.providers.base import BaseProvider


class AnthropicProvider(BaseProvider):
    """
    Anthropic Claude API provider.

    Supports Claude 3 models with long context windows.
    Requires ANTHROPIC_API_KEY environment variable or explicit key.
    """

    name = "anthropic"
    display_name = "Anthropic (Claude)"
    capabilities = {
        AICapability.TEXT_GENERATION,
        AICapability.CHAT,
        AICapability.IMAGE_ANALYSIS,
        AICapability.CODE_GENERATION,
    }

    MODELS = [
        {"id": "claude-sonnet-4-20250514", "name": "Claude Sonnet 4", "context": 200000},
        {"id": "claude-3-5-sonnet-20241022", "name": "Claude 3.5 Sonnet", "context": 200000},
        {"id": "claude-3-5-haiku-20241022", "name": "Claude 3.5 Haiku", "context": 200000},
        {"id": "claude-3-opus-20240229", "name": "Claude 3 Opus", "context": 200000},
    ]

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "claude-3-5-sonnet-20241022",
    ):
        super().__init__()
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.model = model
        self._client = None

    async def initialize(self) -> bool:
        """Initialize the Anthropic provider."""
        if not self.api_key:
            self._is_available = False
            return False

        try:
            from anthropic import AsyncAnthropic

            self._client = AsyncAnthropic(api_key=self.api_key)
            self._is_initialized = True
            self._is_available = True
            return True
        except ImportError:
            print("anthropic package not installed. Install with: pip install anthropic")
            self._is_available = False
            return False
        except Exception as e:
            print(f"Failed to initialize Anthropic provider: {e}")
            self._is_available = False
            return False

    def is_available(self) -> bool:
        """Check if Anthropic provider is available."""
        return self._is_available and self.api_key is not None

    def get_models(self) -> list[dict]:
        """Get available Anthropic models."""
        return self.MODELS

    def get_default_model(self) -> str:
        """Get the default model."""
        return self.model

    async def generate(
        self,
        prompt: str,
        config: GenerationConfig,
    ) -> AIResponse:
        """Generate text from a prompt using messages API."""
        messages = [AIMessage(role="user", content=prompt)]
        return await self.chat(messages, config)

    async def chat(
        self,
        messages: list[AIMessage],
        config: GenerationConfig,
    ) -> AIResponse:
        """Generate a chat response."""
        if not self._client:
            await self.initialize()

        # Extract system message if present
        system_message = None
        chat_messages = []

        for msg in messages:
            if msg.role == "system":
                system_message = msg.content
            else:
                chat_messages.append({"role": msg.role, "content": msg.content})

        response = await self._client.messages.create(
            model=self.model,
            max_tokens=config.max_tokens,
            system=system_message or "",
            messages=chat_messages,
            temperature=config.temperature,
            top_p=config.top_p,
            stop_sequences=config.stop_sequences or None,
        )

        # Extract text content
        content = ""
        for block in response.content:
            if hasattr(block, "text"):
                content += block.text

        return AIResponse(
            content=content,
            provider=self.name,
            model=self.model,
            usage={
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
            },
            finish_reason=response.stop_reason,
            raw_response=response.model_dump(),
        )

    async def chat_stream(
        self,
        messages: list[AIMessage],
        config: GenerationConfig,
    ) -> AsyncIterator[AIStreamChunk]:
        """Stream a chat response with error recovery."""
        try:
            async for chunk in self._stream_with_recovery(self._raw_chat_stream(messages, config)):
                yield chunk
        except StreamInterruptedError:
            # Error already yielded as final chunk, just return
            return

    async def _raw_chat_stream(
        self,
        messages: list[AIMessage],
        config: GenerationConfig,
    ) -> AsyncIterator[AIStreamChunk]:
        """Internal streaming implementation."""
        if not self._client:
            await self.initialize()

        # Extract system message if present
        system_message = None
        chat_messages = []

        for msg in messages:
            if msg.role == "system":
                system_message = msg.content
            else:
                chat_messages.append({"role": msg.role, "content": msg.content})

        async with self._client.messages.stream(
            model=self.model,
            max_tokens=config.max_tokens,
            system=system_message or "",
            messages=chat_messages,
            temperature=config.temperature,
            top_p=config.top_p,
            stop_sequences=config.stop_sequences or None,
        ) as stream:
            async for text in stream.text_stream:
                yield AIStreamChunk(
                    content=text,
                    is_final=False,
                )

            # Final chunk with usage
            message = await stream.get_final_message()
            yield AIStreamChunk(
                content="",
                is_final=True,
                usage={
                    "prompt_tokens": message.usage.input_tokens,
                    "completion_tokens": message.usage.output_tokens,
                    "total_tokens": message.usage.input_tokens + message.usage.output_tokens,
                },
            )
