"""
Base Provider - Abstract base class for AI providers.
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from src.ai.gateway import (
    AICapability,
    AIMessage,
    AIResponse,
    AIStreamChunk,
    GenerationConfig,
    RateLimitInfo,
    StreamInterruptedError,
)


class BaseProvider(ABC):
    """
    Abstract base class for AI providers.

    Each provider must implement the core methods for
    text generation, chat, and embeddings.
    """

    name: str = "base"
    display_name: str = "Base Provider"
    capabilities: set[AICapability] = set()

    def __init__(self):
        self._is_initialized = False
        self._is_available = False

    @abstractmethod
    async def initialize(self) -> bool:
        """
        Initialize the provider.

        Returns:
            True if initialization successful
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is available and ready."""
        pass

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        config: GenerationConfig,
    ) -> AIResponse:
        """
        Generate text from a prompt.

        Args:
            prompt: Input prompt
            config: Generation configuration

        Returns:
            AIResponse with generated text
        """
        pass

    @abstractmethod
    async def chat(
        self,
        messages: list[AIMessage],
        config: GenerationConfig,
    ) -> AIResponse:
        """
        Generate a chat response.

        Args:
            messages: Conversation history
            config: Generation configuration

        Returns:
            AIResponse with assistant message
        """
        pass

    async def chat_stream(
        self,
        messages: list[AIMessage],
        config: GenerationConfig,
    ) -> AsyncIterator[AIStreamChunk]:
        """
        Stream a chat response.

        Default implementation yields full response as single chunk.
        Override for true streaming support.
        """
        response = await self.chat(messages, config)
        yield AIStreamChunk(
            content=response.content,
            is_final=True,
            usage=response.usage,
        )

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors

        Raises:
            NotImplementedError if provider doesn't support embeddings
        """
        raise NotImplementedError(f"{self.name} does not support embeddings")

    def get_models(self) -> list[dict]:
        """
        Get available models for this provider.

        Returns:
            List of model info dictionaries
        """
        return []

    def get_default_model(self) -> str | None:
        """Get the default model for this provider."""
        models = self.get_models()
        return models[0]["id"] if models else None

    async def _stream_with_recovery(
        self,
        stream_generator: AsyncIterator[AIStreamChunk],
        interrupt_marker: str = "\n\n[Response interrupted]",
    ) -> AsyncIterator[AIStreamChunk]:
        """
        Wrap a stream generator with partial response preservation.

        If the stream fails mid-response, yields a final chunk with:
        - The interrupt marker appended to content
        - Error info in the error field
        - is_final=True

        Usage in subclass:
            async for chunk in self._stream_with_recovery(self._raw_chat_stream(messages, config)):
                yield chunk
        """
        buffer = []
        try:
            async for chunk in stream_generator:
                buffer.append(chunk.content)
                yield chunk
        except Exception as e:
            partial_content = "".join(buffer)
            # Yield final chunk with error info
            yield AIStreamChunk(
                content=interrupt_marker,
                is_final=True,
                error={
                    "type": type(e).__name__,
                    "message": str(e),
                    "partial_content_length": len(partial_content),
                },
            )
            # Re-raise wrapped exception for caller handling
            raise StreamInterruptedError(partial_content=partial_content, cause=e)

    def _parse_rate_limit_headers(self, headers: dict) -> RateLimitInfo:
        """
        Parse rate limit info from response headers.

        Different providers use different header names. This method handles
        common patterns. Subclasses can override for provider-specific parsing.
        """
        # Common header patterns
        return RateLimitInfo(
            limit_requests=int(headers.get("x-ratelimit-limit-requests", 0)),
            remaining_requests=int(headers.get("x-ratelimit-remaining-requests", 0)),
            limit_tokens=int(headers.get("x-ratelimit-limit-tokens", 0)),
            remaining_tokens=int(headers.get("x-ratelimit-remaining-tokens", 0)),
            # Parse reset time if present (Retry-After header)
            reset_time=self._parse_reset_time(headers.get("retry-after")),
        )

    def _parse_reset_time(self, retry_after: str | None) -> float | None:
        """Parse Retry-After header to Unix timestamp."""
        if retry_after is None:
            return None
        import time

        try:
            # Try as seconds
            return time.time() + int(retry_after)
        except ValueError:
            # Try as HTTP date (not common, skip for now)
            return None
