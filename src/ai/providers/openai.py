"""
OpenAI Provider - OpenAI API integration.

Supports GPT-4, GPT-3.5, embeddings, and DALL-E.
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


class OpenAIProvider(BaseProvider):
    """
    OpenAI API provider.

    Supports GPT models, embeddings, and image generation.
    Requires OPENAI_API_KEY environment variable or explicit key.
    """

    name = "openai"
    display_name = "OpenAI"
    capabilities = {
        AICapability.TEXT_GENERATION,
        AICapability.CHAT,
        AICapability.EMBEDDINGS,
        AICapability.IMAGE_GENERATION,
        AICapability.IMAGE_ANALYSIS,
        AICapability.CODE_GENERATION,
        AICapability.FUNCTION_CALLING,
    }

    MODELS = [
        {"id": "gpt-4o", "name": "GPT-4o", "context": 128000},
        {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "context": 128000},
        {"id": "gpt-4-turbo", "name": "GPT-4 Turbo", "context": 128000},
        {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "context": 16385},
    ]

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gpt-4o-mini",
        base_url: str | None = None,
    ):
        super().__init__()
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.model = model
        self.base_url = base_url
        self._client = None

    async def initialize(self) -> bool:
        """Initialize the OpenAI provider."""
        if not self.api_key:
            self._is_available = False
            return False

        try:
            from openai import AsyncOpenAI

            self._client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
            )
            self._is_initialized = True
            self._is_available = True
            return True
        except ImportError:
            print("openai package not installed. Install with: pip install openai")
            self._is_available = False
            return False
        except Exception as e:
            print(f"Failed to initialize OpenAI provider: {e}")
            self._is_available = False
            return False

    def is_available(self) -> bool:
        """Check if OpenAI provider is available."""
        return self._is_available and self.api_key is not None

    def get_models(self) -> list[dict]:
        """Get available OpenAI models."""
        return self.MODELS

    def get_default_model(self) -> str:
        """Get the default model."""
        return self.model

    async def generate(
        self,
        prompt: str,
        config: GenerationConfig,
    ) -> AIResponse:
        """Generate text from a prompt using chat completion."""
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

        response = await self._client.chat.completions.create(
            model=self.model,
            messages=[m.to_dict() for m in messages],
            max_tokens=config.max_tokens,
            temperature=config.temperature,
            top_p=config.top_p,
            stop=config.stop_sequences or None,
        )

        choice = response.choices[0]

        return AIResponse(
            content=choice.message.content or "",
            provider=self.name,
            model=self.model,
            usage={
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0,
            },
            finish_reason=choice.finish_reason,
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

        stream = await self._client.chat.completions.create(
            model=self.model,
            messages=[m.to_dict() for m in messages],
            max_tokens=config.max_tokens,
            temperature=config.temperature,
            top_p=config.top_p,
            stop=config.stop_sequences or None,
            stream=True,
        )

        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield AIStreamChunk(
                    content=chunk.choices[0].delta.content,
                    is_final=chunk.choices[0].finish_reason is not None,
                )

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for texts."""
        if not self._client:
            await self.initialize()

        response = await self._client.embeddings.create(
            model="text-embedding-3-small",
            input=texts,
        )

        return [item.embedding for item in response.data]

    async def generate_image(
        self,
        prompt: str,
        size: str = "1024x1024",
        quality: str = "standard",
        n: int = 1,
    ) -> list[str]:
        """
        Generate images from a prompt.

        Args:
            prompt: Image description
            size: Image size (1024x1024, 1792x1024, 1024x1792)
            quality: "standard" or "hd"
            n: Number of images to generate

        Returns:
            List of image URLs
        """
        if not self._client:
            await self.initialize()

        response = await self._client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size=size,
            quality=quality,
            n=n,
        )

        return [item.url for item in response.data]
