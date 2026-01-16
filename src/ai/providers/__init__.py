"""AI Provider implementations."""

from src.ai.providers.base import BaseProvider
from src.ai.providers.local import LocalProvider
from src.ai.providers.openai import OpenAIProvider
from src.ai.providers.anthropic import AnthropicProvider
from src.ai.providers.demo import DemoProvider
from src.ai.providers.lm_studio import LMStudioProvider
from src.ai.providers.ollama import OllamaProvider

__all__ = [
    "BaseProvider",
    "LocalProvider",
    "OpenAIProvider",
    "AnthropicProvider",
    "DemoProvider",
    "LMStudioProvider",
    "OllamaProvider",
]


def initialize_default_providers():
    """Initialize and register default providers with the gateway."""
    from src.ai.gateway import get_gateway

    gateway = get_gateway()

    # Always register demo provider as fallback
    demo = DemoProvider()
    gateway.register_provider(demo, priority=99)  # Low priority fallback

    # Try to initialize local provider (llama.cpp)
    try:
        local = LocalProvider()
        gateway.register_provider(local, priority=1)
    except Exception:
        pass  # Local provider optional

    # Try to initialize Ollama provider
    try:
        ollama = OllamaProvider()
        gateway.register_provider(ollama, priority=2)
    except Exception:
        pass  # Ollama provider optional

    return gateway
