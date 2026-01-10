"""
Skynette AI Module

Provides unified AI capabilities through multiple providers.
"""

from src.ai.gateway import (
    AIGateway,
    AICapability,
    AIMessage,
    AIResponse,
    AIStreamChunk,
    GenerationConfig,
    get_gateway,
)
from src.ai.providers import (
    BaseProvider,
    LocalProvider,
    OpenAIProvider,
    AnthropicProvider,
)

__all__ = [
    # Gateway
    "AIGateway",
    "AICapability",
    "AIMessage",
    "AIResponse",
    "AIStreamChunk",
    "GenerationConfig",
    "get_gateway",
    # Providers
    "BaseProvider",
    "LocalProvider",
    "OpenAIProvider",
    "AnthropicProvider",
]


async def setup_default_providers():
    """Set up default providers based on available configuration."""
    gateway = get_gateway()

    # Always add local provider (priority 0 = highest)
    local = LocalProvider()
    await local.initialize()
    gateway.register_provider(local, priority=0)

    # Add cloud providers if API keys available
    openai = OpenAIProvider()
    if await openai.initialize():
        gateway.register_provider(openai, priority=1)

    anthropic = AnthropicProvider()
    if await anthropic.initialize():
        gateway.register_provider(anthropic, priority=2)

    return gateway
