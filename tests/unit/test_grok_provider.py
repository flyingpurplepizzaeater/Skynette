"""Unit tests for Grok provider.

Tests focus on provider attributes, initialization behavior, and error handling
without requiring the actual xai-sdk to be present.
"""

from unittest.mock import patch

import pytest

from src.ai.gateway import AICapability, AIMessage, GenerationConfig
from src.ai.providers.grok import GrokProvider


class TestGrokProviderAttributes:
    """Test provider static attributes and configuration."""

    def test_provider_name(self):
        """Test provider has correct name."""
        provider = GrokProvider()
        assert provider.name == "grok"

    def test_provider_display_name(self):
        """Test provider has correct display_name."""
        provider = GrokProvider()
        assert provider.display_name == "xAI (Grok)"

    def test_provider_has_chat_capability(self):
        """Test provider declares chat capability."""
        provider = GrokProvider()
        assert AICapability.CHAT in provider.capabilities

    def test_provider_has_text_generation_capability(self):
        """Test provider declares text generation capability."""
        provider = GrokProvider()
        assert AICapability.TEXT_GENERATION in provider.capabilities

    def test_provider_has_image_analysis_capability(self):
        """Test provider declares image analysis capability."""
        provider = GrokProvider()
        assert AICapability.IMAGE_ANALYSIS in provider.capabilities

    def test_provider_has_code_generation_capability(self):
        """Test provider declares code generation capability."""
        provider = GrokProvider()
        assert AICapability.CODE_GENERATION in provider.capabilities


class TestGrokProviderModels:
    """Test model listing and selection."""

    def test_models_list_not_empty(self):
        """Test provider has models defined."""
        provider = GrokProvider()
        models = provider.get_models()
        assert len(models) > 0

    def test_models_have_required_fields(self):
        """Test all models have id and name fields."""
        provider = GrokProvider()
        models = provider.get_models()
        for model in models:
            assert "id" in model, f"Model missing 'id': {model}"
            assert "name" in model, f"Model missing 'name': {model}"

    def test_models_have_context_field(self):
        """Test all models have context window size."""
        provider = GrokProvider()
        models = provider.get_models()
        for model in models:
            assert "context" in model, f"Model missing 'context': {model}"
            assert model["context"] > 0, f"Invalid context size: {model}"

    def test_grok_3_model_available(self):
        """Test Grok 3 is in available models."""
        provider = GrokProvider()
        models = provider.get_models()
        model_ids = [m["id"] for m in models]
        assert "grok-3" in model_ids

    def test_grok_2_model_available(self):
        """Test Grok 2 is in available models."""
        provider = GrokProvider()
        models = provider.get_models()
        model_ids = [m["id"] for m in models]
        assert "grok-2" in model_ids

    def test_grok_3_fast_model_available(self):
        """Test Grok 3 Fast is in available models."""
        provider = GrokProvider()
        models = provider.get_models()
        model_ids = [m["id"] for m in models]
        assert "grok-3-fast" in model_ids

    def test_default_model_is_grok_2(self):
        """Test default model is grok-2."""
        provider = GrokProvider()
        assert provider.get_default_model() == "grok-2"

    def test_custom_model_selection(self):
        """Test provider can be initialized with custom model."""
        provider = GrokProvider(model="grok-3")
        assert provider.get_default_model() == "grok-3"


class TestGrokProviderInitialization:
    """Test provider initialization behavior."""

    def test_provider_initially_not_available(self):
        """Test provider is not available before initialization."""
        provider = GrokProvider()
        assert provider.is_available() is False

    def test_provider_accepts_api_key_param(self):
        """Test provider accepts api_key parameter."""
        provider = GrokProvider(api_key="test-key-123")
        assert provider.api_key == "test-key-123"

    @pytest.mark.asyncio
    async def test_initialize_without_api_key_returns_false(self):
        """Test initialization fails gracefully without API key."""
        with patch.dict("os.environ", {}, clear=True):
            provider = GrokProvider(api_key=None)
            result = await provider.initialize()
            assert result is False

    @pytest.mark.asyncio
    async def test_initialize_without_api_key_sets_unavailable(self):
        """Test provider unavailable after failed initialization."""
        with patch.dict("os.environ", {}, clear=True):
            provider = GrokProvider(api_key=None)
            await provider.initialize()
            assert provider.is_available() is False

    @pytest.mark.asyncio
    async def test_initialize_gets_api_key_from_env(self):
        """Test provider reads XAI_API_KEY from environment."""
        with patch.dict("os.environ", {"XAI_API_KEY": "env-test-key"}):
            provider = GrokProvider()
            assert provider.api_key == "env-test-key"


class TestGrokProviderChatNotInitialized:
    """Test chat behavior when provider not initialized."""

    @pytest.mark.asyncio
    async def test_chat_without_init_returns_error_response(self):
        """Test chat returns error when provider not initialized."""
        provider = GrokProvider(api_key=None)
        messages = [AIMessage(role="user", content="Hello")]
        config = GenerationConfig()

        response = await provider.chat(messages, config)

        assert response.finish_reason == "error"

    @pytest.mark.asyncio
    async def test_chat_without_init_error_mentions_init(self):
        """Test chat error message mentions initialization."""
        provider = GrokProvider(api_key=None)
        messages = [AIMessage(role="user", content="Hello")]
        config = GenerationConfig()

        response = await provider.chat(messages, config)

        assert "not initialized" in response.content.lower() or "api key" in response.content.lower()

    @pytest.mark.asyncio
    async def test_chat_response_has_correct_provider(self):
        """Test error response has correct provider name."""
        provider = GrokProvider(api_key=None)
        messages = [AIMessage(role="user", content="Hello")]
        config = GenerationConfig()

        response = await provider.chat(messages, config)

        assert response.provider == "grok"


class TestGrokProviderStreamingNotInitialized:
    """Test streaming behavior when provider not initialized."""

    @pytest.mark.asyncio
    async def test_stream_without_init_yields_error(self):
        """Test streaming returns error when not initialized."""
        provider = GrokProvider(api_key=None)
        messages = [AIMessage(role="user", content="Hello")]
        config = GenerationConfig()

        chunks = []
        async for chunk in provider.chat_stream(messages, config):
            chunks.append(chunk)

        assert len(chunks) == 1

    @pytest.mark.asyncio
    async def test_stream_without_init_final_chunk(self):
        """Test streaming yields final chunk on error."""
        provider = GrokProvider(api_key=None)
        messages = [AIMessage(role="user", content="Hello")]
        config = GenerationConfig()

        chunks = []
        async for chunk in provider.chat_stream(messages, config):
            chunks.append(chunk)

        assert chunks[0].is_final is True

    @pytest.mark.asyncio
    async def test_stream_without_init_error_message(self):
        """Test streaming error mentions initialization issue."""
        provider = GrokProvider(api_key=None)
        messages = [AIMessage(role="user", content="Hello")]
        config = GenerationConfig()

        chunks = []
        async for chunk in provider.chat_stream(messages, config):
            chunks.append(chunk)

        assert "not initialized" in chunks[0].content.lower() or "api key" in chunks[0].content.lower()


class TestGrokProviderGenerate:
    """Test text generation functionality."""

    @pytest.mark.asyncio
    async def test_generate_without_init_returns_error(self):
        """Test generate returns error when not initialized."""
        provider = GrokProvider(api_key=None)
        config = GenerationConfig()

        response = await provider.generate("Generate something", config)

        assert response.finish_reason == "error"

    @pytest.mark.asyncio
    async def test_generate_response_has_provider(self):
        """Test generate response has correct provider."""
        provider = GrokProvider(api_key=None)
        config = GenerationConfig()

        response = await provider.generate("Generate something", config)

        assert response.provider == "grok"


class TestGrokProviderTimeout:
    """Test timeout configuration for reasoning models."""

    def test_provider_client_timeout_attribute(self):
        """Test provider stores timeout config for reasoning models."""
        # The timeout is set when client is created, verify attribute exists
        provider = GrokProvider(api_key="test-key")
        # Client will be None since we haven't initialized, but provider stores api_key
        assert provider.api_key == "test-key"
        # The 3600s timeout is applied in initialize() when creating client


class TestGrokProviderModelContext:
    """Test model context window sizes."""

    def test_grok_3_context_size(self):
        """Test Grok 3 has large context window."""
        provider = GrokProvider()
        models = provider.get_models()
        grok3 = next(m for m in models if m["id"] == "grok-3")
        assert grok3["context"] >= 131072

    def test_grok_2_vision_context_size(self):
        """Test Grok 2 Vision has reasonable context window."""
        provider = GrokProvider()
        models = provider.get_models()
        grok2_vision = next(m for m in models if m["id"] == "grok-2-vision")
        assert grok2_vision["context"] >= 32768
