"""
Grok Provider - xAI Grok API integration.

Supports Grok models using the official xai-sdk.
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


class GrokProvider(BaseProvider):
    """
    xAI Grok API provider.

    Supports Grok models with large context windows.
    Requires XAI_API_KEY environment variable or explicit key.
    """

    name = "grok"
    display_name = "xAI (Grok)"
    capabilities = {
        AICapability.TEXT_GENERATION,
        AICapability.CHAT,
        AICapability.IMAGE_ANALYSIS,
        AICapability.CODE_GENERATION,
    }

    MODELS = [
        {"id": "grok-3", "name": "Grok 3", "context": 131072},
        {"id": "grok-3-fast", "name": "Grok 3 Fast", "context": 131072},
        {"id": "grok-2", "name": "Grok 2", "context": 131072},
        {"id": "grok-2-vision", "name": "Grok 2 Vision", "context": 32768},
    ]

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "grok-2",
    ):
        super().__init__()
        self.api_key = api_key or os.environ.get("XAI_API_KEY")
        self.model = model
        self._client = None

    async def initialize(self) -> bool:
        """Initialize the Grok provider."""
        if not self.api_key:
            self._is_available = False
            return False

        try:
            from xai_sdk import Client

            # Use 3600s timeout for reasoning models
            self._client = Client(api_key=self.api_key, timeout=3600)
            self._is_initialized = True
            self._is_available = True
            return True
        except ImportError:
            print("xai-sdk package not installed. Install with: pip install xai-sdk")
            self._is_available = False
            return False
        except Exception as e:
            print(f"Failed to initialize Grok provider: {e}")
            self._is_available = False
            return False

    def is_available(self) -> bool:
        """Check if Grok provider is available."""
        return self._is_available and self.api_key is not None

    def get_models(self) -> list[dict]:
        """Get available Grok models."""
        return self.MODELS

    def get_default_model(self) -> str:
        """Get the default model."""
        return self.model

    async def generate(
        self,
        prompt: str,
        config: GenerationConfig,
    ) -> AIResponse:
        """Generate text from a prompt using chat API."""
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

        if not self._client:
            return AIResponse(
                content="Grok provider not initialized. Check API key.",
                provider=self.name,
                model=self.model,
                usage={},
                finish_reason="error",
            )

        try:
            from xai_sdk.chat import assistant, system, user

            # Create a new chat session
            chat = self._client.chat.create(model=self.model)

            # Add messages to chat
            for msg in messages:
                if msg.role == "system":
                    chat.append(system(msg.content))
                elif msg.role == "user":
                    chat.append(user(msg.content))
                elif msg.role == "assistant":
                    chat.append(assistant(msg.content))

            # Execute chat (non-streaming)
            response = chat()

            return AIResponse(
                content=response.content if hasattr(response, "content") else str(response),
                provider=self.name,
                model=self.model,
                usage={},  # xai-sdk doesn't expose usage stats in basic response
                finish_reason="stop",
            )
        except Exception as e:
            error_msg = str(e)
            if "DEADLINE_EXCEEDED" in error_msg:
                error_msg = "Request timed out. The model may be processing a complex request."
            return AIResponse(
                content=f"Error: {error_msg}",
                provider=self.name,
                model=self.model,
                usage={},
                finish_reason="error",
            )

    async def chat_stream(
        self,
        messages: list[AIMessage],
        config: GenerationConfig,
    ) -> AsyncIterator[AIStreamChunk]:
        """Stream a chat response with error recovery."""
        if not self._client:
            await self.initialize()

        if not self._client:
            yield AIStreamChunk(
                content="Grok provider not initialized. Check API key.",
                is_final=True,
            )
            return

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
        from xai_sdk.chat import assistant, system, user

        # Create a new chat session
        chat = self._client.chat.create(model=self.model)

        # Add messages to chat
        for msg in messages:
            if msg.role == "system":
                chat.append(system(msg.content))
            elif msg.role == "user":
                chat.append(user(msg.content))
            elif msg.role == "assistant":
                chat.append(assistant(msg.content))

        # Stream the response
        # xai-sdk uses sync streaming, so we yield chunks as they arrive
        for response, chunk in chat.stream():
            content = chunk.content if hasattr(chunk, "content") else str(chunk)
            yield AIStreamChunk(
                content=content,
                is_final=False,
            )

        # Final chunk
        yield AIStreamChunk(
            content="",
            is_final=True,
            usage={},  # xai-sdk doesn't expose usage stats
        )
