"""Unit tests for Gemini provider.

Tests focus on provider attributes, initialization behavior, and error handling
without requiring the actual google-genai SDK to be present.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.ai.gateway import AICapability, AIMessage, GenerationConfig
from src.ai.providers.gemini import GeminiProvider


class TestGeminiProviderAttributes:
    """Test provider static attributes and configuration."""

    def test_provider_name(self):
        """Test provider has correct name."""
        provider = GeminiProvider()
        assert provider.name == "gemini"

    def test_provider_display_name(self):
        """Test provider has correct display_name."""
        provider = GeminiProvider()
        assert provider.display_name == "Google Gemini"

    def test_provider_has_chat_capability(self):
        """Test provider declares chat capability."""
        provider = GeminiProvider()
        assert AICapability.CHAT in provider.capabilities

    def test_provider_has_text_generation_capability(self):
        """Test provider declares text generation capability."""
        provider = GeminiProvider()
        assert AICapability.TEXT_GENERATION in provider.capabilities

    def test_provider_has_image_analysis_capability(self):
        """Test provider declares image analysis capability."""
        provider = GeminiProvider()
        assert AICapability.IMAGE_ANALYSIS in provider.capabilities

    def test_provider_has_code_generation_capability(self):
        """Test provider declares code generation capability."""
        provider = GeminiProvider()
        assert AICapability.CODE_GENERATION in provider.capabilities


class TestGeminiProviderModels:
    """Test model listing and selection."""

    def test_models_list_not_empty(self):
        """Test provider has models defined."""
        provider = GeminiProvider()
        models = provider.get_models()
        assert len(models) > 0

    def test_models_have_required_fields(self):
        """Test all models have id and name fields."""
        provider = GeminiProvider()
        models = provider.get_models()
        for model in models:
            assert "id" in model, f"Model missing 'id': {model}"
            assert "name" in model, f"Model missing 'name': {model}"

    def test_models_have_context_field(self):
        """Test all models have context window size."""
        provider = GeminiProvider()
        models = provider.get_models()
        for model in models:
            assert "context" in model, f"Model missing 'context': {model}"
            assert model["context"] > 0, f"Invalid context size: {model}"

    def test_gemini_25_flash_model_available(self):
        """Test Gemini 2.5 Flash is in available models."""
        provider = GeminiProvider()
        models = provider.get_models()
        model_ids = [m["id"] for m in models]
        assert "gemini-2.5-flash" in model_ids

    def test_gemini_20_pro_model_available(self):
        """Test Gemini 2.0 Pro is in available models."""
        provider = GeminiProvider()
        models = provider.get_models()
        model_ids = [m["id"] for m in models]
        assert "gemini-2.0-pro" in model_ids

    def test_default_model_is_25_flash(self):
        """Test default model is gemini-2.5-flash."""
        provider = GeminiProvider()
        assert provider.get_default_model() == "gemini-2.5-flash"

    def test_custom_model_selection(self):
        """Test provider can be initialized with custom model."""
        provider = GeminiProvider(model="gemini-2.0-pro")
        assert provider.get_default_model() == "gemini-2.0-pro"


class TestGeminiProviderInitialization:
    """Test provider initialization behavior."""

    def test_provider_initially_not_available(self):
        """Test provider is not available before initialization."""
        provider = GeminiProvider()
        assert provider.is_available() is False

    def test_provider_accepts_api_key_param(self):
        """Test provider accepts api_key parameter."""
        provider = GeminiProvider(api_key="test-key-123")
        assert provider.api_key == "test-key-123"

    @pytest.mark.asyncio
    async def test_initialize_without_api_key_returns_false(self):
        """Test initialization fails gracefully without API key."""
        with patch.dict("os.environ", {}, clear=True):
            provider = GeminiProvider(api_key=None)
            result = await provider.initialize()
            assert result is False

    @pytest.mark.asyncio
    async def test_initialize_without_api_key_sets_unavailable(self):
        """Test provider unavailable after failed initialization."""
        with patch.dict("os.environ", {}, clear=True):
            provider = GeminiProvider(api_key=None)
            await provider.initialize()
            assert provider.is_available() is False

    @pytest.mark.asyncio
    async def test_initialize_gets_api_key_from_env(self):
        """Test provider reads GOOGLE_API_KEY from environment."""
        with patch.dict("os.environ", {"GOOGLE_API_KEY": "env-test-key"}):
            provider = GeminiProvider()
            assert provider.api_key == "env-test-key"


class TestGeminiProviderChatNotInitialized:
    """Test chat behavior when provider not initialized."""

    @pytest.mark.asyncio
    async def test_chat_without_init_returns_error_response(self):
        """Test chat returns error when provider not initialized."""
        provider = GeminiProvider(api_key=None)
        messages = [AIMessage(role="user", content="Hello")]
        config = GenerationConfig()

        response = await provider.chat(messages, config)

        assert response.finish_reason == "error"

    @pytest.mark.asyncio
    async def test_chat_without_init_error_mentions_api_key(self):
        """Test chat error message mentions API key."""
        provider = GeminiProvider(api_key=None)
        messages = [AIMessage(role="user", content="Hello")]
        config = GenerationConfig()

        response = await provider.chat(messages, config)

        assert "GOOGLE_API_KEY" in response.content or "not initialized" in response.content.lower()

    @pytest.mark.asyncio
    async def test_chat_response_has_correct_provider(self):
        """Test error response has correct provider name."""
        provider = GeminiProvider(api_key=None)
        messages = [AIMessage(role="user", content="Hello")]
        config = GenerationConfig()

        response = await provider.chat(messages, config)

        assert response.provider == "gemini"


class TestGeminiProviderStreamingNotInitialized:
    """Test streaming behavior when provider not initialized."""

    @pytest.mark.asyncio
    async def test_stream_without_init_yields_error(self):
        """Test streaming returns error when not initialized."""
        provider = GeminiProvider(api_key=None)
        messages = [AIMessage(role="user", content="Hello")]
        config = GenerationConfig()

        chunks = []
        async for chunk in provider.chat_stream(messages, config):
            chunks.append(chunk)

        assert len(chunks) == 1

    @pytest.mark.asyncio
    async def test_stream_without_init_final_chunk(self):
        """Test streaming yields final chunk on error."""
        provider = GeminiProvider(api_key=None)
        messages = [AIMessage(role="user", content="Hello")]
        config = GenerationConfig()

        chunks = []
        async for chunk in provider.chat_stream(messages, config):
            chunks.append(chunk)

        assert chunks[0].is_final is True

    @pytest.mark.asyncio
    async def test_stream_without_init_error_message(self):
        """Test streaming error mentions API key."""
        provider = GeminiProvider(api_key=None)
        messages = [AIMessage(role="user", content="Hello")]
        config = GenerationConfig()

        chunks = []
        async for chunk in provider.chat_stream(messages, config):
            chunks.append(chunk)

        assert "GOOGLE_API_KEY" in chunks[0].content or "not initialized" in chunks[0].content.lower()


class TestGeminiProviderGenerate:
    """Test text generation functionality."""

    @pytest.mark.asyncio
    async def test_generate_without_init_returns_error(self):
        """Test generate returns error when not initialized."""
        provider = GeminiProvider(api_key=None)
        config = GenerationConfig()

        response = await provider.generate("Generate something", config)

        assert response.finish_reason == "error"

    @pytest.mark.asyncio
    async def test_generate_response_has_provider(self):
        """Test generate response has correct provider."""
        provider = GeminiProvider(api_key=None)
        config = GenerationConfig()

        response = await provider.generate("Generate something", config)

        assert response.provider == "gemini"


class TestGeminiProviderCleanup:
    """Test cleanup functionality."""

    @pytest.mark.asyncio
    async def test_cleanup_handles_no_client(self):
        """Test cleanup handles uninitialized provider."""
        provider = GeminiProvider()
        # Should not raise
        await provider.cleanup()

    @pytest.mark.asyncio
    async def test_cleanup_resets_client_references(self):
        """Test cleanup sets client to None."""
        provider = GeminiProvider()
        provider._client = MagicMock()
        provider._aclient = MagicMock()

        await provider.cleanup()

        assert provider._client is None
        assert provider._aclient is None
