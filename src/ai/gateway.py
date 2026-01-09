"""
AI Gateway - Unified Interface for AI Providers

Provides a single interface for all AI operations with:
- Auto-fallback between providers
- Provider priority management
- Response caching
- Usage tracking
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import AsyncIterator, Optional
import asyncio


class AICapability(str, Enum):
    """AI capabilities that providers can support."""
    TEXT_GENERATION = "text_generation"
    CHAT = "chat"
    EMBEDDINGS = "embeddings"
    IMAGE_GENERATION = "image_generation"
    IMAGE_ANALYSIS = "image_analysis"
    CODE_GENERATION = "code_generation"
    FUNCTION_CALLING = "function_calling"


@dataclass
class AIMessage:
    """A message in a conversation."""
    role: str  # "system", "user", "assistant"
    content: str
    name: Optional[str] = None

    def to_dict(self) -> dict:
        d = {"role": self.role, "content": self.content}
        if self.name:
            d["name"] = self.name
        return d


@dataclass
class AIResponse:
    """Response from an AI provider."""
    content: str
    provider: str
    model: str
    usage: dict = field(default_factory=dict)
    finish_reason: Optional[str] = None
    raw_response: Optional[dict] = None


@dataclass
class AIStreamChunk:
    """A chunk from a streaming response."""
    content: str
    is_final: bool = False
    usage: Optional[dict] = None


@dataclass
class GenerationConfig:
    """Configuration for text generation."""
    max_tokens: int = 2048
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 40
    stop_sequences: list[str] = field(default_factory=list)
    stream: bool = False


class AIGateway:
    """
    Unified gateway for AI operations.

    Manages multiple providers and handles:
    - Provider selection based on capability
    - Auto-fallback on failure
    - Response caching
    - Usage tracking
    """

    def __init__(self):
        self.providers: dict[str, "BaseProvider"] = {}
        self.provider_priority: list[str] = []
        self.default_provider: Optional[str] = None
        self.auto_fallback: bool = True
        self._usage_log: list[dict] = []

    def register_provider(self, provider: "BaseProvider", priority: int = 0):
        """Register an AI provider with the gateway."""
        self.providers[provider.name] = provider

        # Insert at correct priority position
        if priority >= len(self.provider_priority):
            self.provider_priority.append(provider.name)
        else:
            self.provider_priority.insert(priority, provider.name)

        # Set as default if first provider
        if self.default_provider is None:
            self.default_provider = provider.name

    def set_default_provider(self, name: str):
        """Set the default provider."""
        if name not in self.providers:
            raise ValueError(f"Provider '{name}' not registered")
        self.default_provider = name

    def get_provider(self, name: str) -> Optional["BaseProvider"]:
        """Get a provider by name."""
        return self.providers.get(name)

    def get_providers_for_capability(self, capability: AICapability) -> list["BaseProvider"]:
        """Get all providers that support a capability, in priority order."""
        result = []
        for name in self.provider_priority:
            provider = self.providers[name]
            if capability in provider.capabilities and provider.is_available():
                result.append(provider)
        return result

    async def generate(
        self,
        prompt: str,
        config: Optional[GenerationConfig] = None,
        provider: Optional[str] = None,
    ) -> AIResponse:
        """
        Generate text from a prompt.

        Args:
            prompt: The input prompt
            config: Generation configuration
            provider: Specific provider to use (optional)

        Returns:
            AIResponse with generated text
        """
        config = config or GenerationConfig()

        # Get providers to try
        if provider:
            providers = [self.providers[provider]] if provider in self.providers else []
        else:
            providers = self.get_providers_for_capability(AICapability.TEXT_GENERATION)

        if not providers:
            raise RuntimeError("No providers available for text generation")

        last_error = None
        for p in providers:
            try:
                response = await p.generate(prompt, config)
                self._log_usage(p.name, "generate", response.usage)
                return response
            except Exception as e:
                last_error = e
                if not self.auto_fallback:
                    raise
                continue

        raise RuntimeError(f"All providers failed. Last error: {last_error}")

    async def chat(
        self,
        messages: list[AIMessage],
        config: Optional[GenerationConfig] = None,
        provider: Optional[str] = None,
    ) -> AIResponse:
        """
        Generate a chat response.

        Args:
            messages: Conversation history
            config: Generation configuration
            provider: Specific provider to use (optional)

        Returns:
            AIResponse with assistant message
        """
        config = config or GenerationConfig()

        if provider:
            providers = [self.providers[provider]] if provider in self.providers else []
        else:
            providers = self.get_providers_for_capability(AICapability.CHAT)

        if not providers:
            raise RuntimeError("No providers available for chat")

        last_error = None
        for p in providers:
            try:
                response = await p.chat(messages, config)
                self._log_usage(p.name, "chat", response.usage)
                return response
            except Exception as e:
                last_error = e
                if not self.auto_fallback:
                    raise
                continue

        raise RuntimeError(f"All providers failed. Last error: {last_error}")

    async def chat_stream(
        self,
        messages: list[AIMessage],
        config: Optional[GenerationConfig] = None,
        provider: Optional[str] = None,
    ) -> AsyncIterator[AIStreamChunk]:
        """
        Stream a chat response.

        Args:
            messages: Conversation history
            config: Generation configuration
            provider: Specific provider to use (optional)

        Yields:
            AIStreamChunk objects as they arrive
        """
        config = config or GenerationConfig()
        config.stream = True

        if provider:
            providers = [self.providers[provider]] if provider in self.providers else []
        else:
            providers = self.get_providers_for_capability(AICapability.CHAT)

        if not providers:
            raise RuntimeError("No providers available for chat streaming")

        # Try first available provider (no fallback during streaming)
        p = providers[0]
        async for chunk in p.chat_stream(messages, config):
            yield chunk

    async def embed(
        self,
        texts: list[str],
        provider: Optional[str] = None,
    ) -> list[list[float]]:
        """
        Generate embeddings for texts.

        Args:
            texts: List of texts to embed
            provider: Specific provider to use (optional)

        Returns:
            List of embedding vectors
        """
        if provider:
            providers = [self.providers[provider]] if provider in self.providers else []
        else:
            providers = self.get_providers_for_capability(AICapability.EMBEDDINGS)

        if not providers:
            raise RuntimeError("No providers available for embeddings")

        last_error = None
        for p in providers:
            try:
                embeddings = await p.embed(texts)
                self._log_usage(p.name, "embed", {"texts": len(texts)})
                return embeddings
            except Exception as e:
                last_error = e
                if not self.auto_fallback:
                    raise
                continue

        raise RuntimeError(f"All providers failed. Last error: {last_error}")

    def _log_usage(self, provider: str, operation: str, usage: dict):
        """Log usage for tracking."""
        self._usage_log.append({
            "provider": provider,
            "operation": operation,
            "usage": usage,
        })

    def get_usage_summary(self) -> dict:
        """Get usage summary by provider."""
        summary = {}
        for entry in self._usage_log:
            provider = entry["provider"]
            if provider not in summary:
                summary[provider] = {"operations": 0, "tokens": 0}
            summary[provider]["operations"] += 1
            if "total_tokens" in entry.get("usage", {}):
                summary[provider]["tokens"] += entry["usage"]["total_tokens"]
        return summary


# Singleton gateway instance
_gateway: Optional[AIGateway] = None


def get_gateway() -> AIGateway:
    """Get the global AI gateway instance."""
    global _gateway
    if _gateway is None:
        _gateway = AIGateway()
    return _gateway
