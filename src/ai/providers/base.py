"""
Base Provider - Abstract base class for AI providers.
"""

from abc import ABC, abstractmethod
from typing import AsyncIterator, Optional

from src.ai.gateway import (
    AICapability,
    AIMessage,
    AIResponse,
    AIStreamChunk,
    GenerationConfig,
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

    def get_default_model(self) -> Optional[str]:
        """Get the default model for this provider."""
        models = self.get_models()
        return models[0]["id"] if models else None
