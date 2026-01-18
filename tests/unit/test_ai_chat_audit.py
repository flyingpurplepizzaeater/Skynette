"""
Regression tests for bugs found during AI Chat audit (Plan 01-01).

Note: The plan targeted simple_mode.py (which is actually a workflow builder,
not AI Chat) and gateway.py. These tests document the bugs found and their fixes.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.ai.gateway import (
    AICapability,
    AIGateway,
    AIMessage,
    AIResponse,
    AIStreamChunk,
    GenerationConfig,
    get_gateway,
)


class TestAIGatewayAuditFindings:
    """Regression tests for bugs found in AIGateway during audit."""

    @pytest.fixture
    def gateway(self):
        """Create a fresh gateway for testing."""
        return AIGateway()

    @pytest.fixture
    def mock_provider(self):
        """Create a mock provider for testing."""
        provider = MagicMock()
        provider.name = "test_provider"
        provider.capabilities = {AICapability.CHAT, AICapability.TEXT_GENERATION}
        provider.is_available.return_value = True
        provider.chat = AsyncMock(
            return_value=AIResponse(
                content="Test response",
                provider="test_provider",
                model="test-model",
                usage={"total_tokens": 100},
            )
        )
        provider.generate = AsyncMock(
            return_value=AIResponse(
                content="Generated text",
                provider="test_provider",
                model="test-model",
                usage={"total_tokens": 50},
            )
        )
        return provider

    def test_gateway_initialization(self, gateway):
        """Gateway initializes with empty providers and settings."""
        assert gateway.providers == {}
        assert gateway.provider_priority == []
        assert gateway.default_provider is None
        assert gateway.auto_fallback is True
        assert gateway._usage_log == []

    def test_register_provider_sets_default(self, gateway, mock_provider):
        """First registered provider becomes default."""
        gateway.register_provider(mock_provider)
        assert gateway.default_provider == "test_provider"
        assert "test_provider" in gateway.providers

    def test_register_provider_respects_priority(self, gateway):
        """Providers are ordered by priority."""
        provider1 = MagicMock()
        provider1.name = "low_priority"
        provider2 = MagicMock()
        provider2.name = "high_priority"

        gateway.register_provider(provider1, priority=5)
        gateway.register_provider(provider2, priority=0)

        assert gateway.provider_priority[0] == "high_priority"

    @pytest.mark.asyncio
    async def test_chat_with_no_providers_raises(self, gateway):
        """Chat with no providers raises RuntimeError."""
        with pytest.raises(RuntimeError, match="No providers available for chat"):
            await gateway.chat([AIMessage(role="user", content="Hello")])

    @pytest.mark.asyncio
    async def test_chat_success(self, gateway, mock_provider):
        """Chat succeeds with registered provider."""
        gateway.register_provider(mock_provider)

        messages = [AIMessage(role="user", content="Hello")]
        response = await gateway.chat(messages)

        assert response.content == "Test response"
        assert response.provider == "test_provider"
        mock_provider.chat.assert_called_once()

    @pytest.mark.asyncio
    async def test_chat_logs_usage(self, gateway, mock_provider):
        """Chat logs usage after successful call."""
        gateway.register_provider(mock_provider)

        messages = [AIMessage(role="user", content="Hello")]
        await gateway.chat(messages)

        assert len(gateway._usage_log) == 1
        assert gateway._usage_log[0]["provider"] == "test_provider"
        assert gateway._usage_log[0]["operation"] == "chat"

    @pytest.mark.asyncio
    async def test_chat_fallback_on_failure(self, gateway):
        """Chat falls back to next provider on failure."""
        failing_provider = MagicMock()
        failing_provider.name = "failing"
        failing_provider.capabilities = {AICapability.CHAT}
        failing_provider.is_available.return_value = True
        failing_provider.chat = AsyncMock(side_effect=RuntimeError("Provider error"))

        success_provider = MagicMock()
        success_provider.name = "success"
        success_provider.capabilities = {AICapability.CHAT}
        success_provider.is_available.return_value = True
        success_provider.chat = AsyncMock(
            return_value=AIResponse(
                content="Fallback response",
                provider="success",
                model="test",
                usage={},
            )
        )

        gateway.register_provider(failing_provider, priority=0)
        gateway.register_provider(success_provider, priority=1)

        messages = [AIMessage(role="user", content="Hello")]
        response = await gateway.chat(messages)

        assert response.content == "Fallback response"
        assert failing_provider.chat.called
        assert success_provider.chat.called

    @pytest.mark.asyncio
    async def test_chat_no_fallback_when_disabled(self, gateway):
        """Chat doesn't fallback when auto_fallback is False."""
        gateway.auto_fallback = False

        failing_provider = MagicMock()
        failing_provider.name = "failing"
        failing_provider.capabilities = {AICapability.CHAT}
        failing_provider.is_available.return_value = True
        failing_provider.chat = AsyncMock(side_effect=RuntimeError("Provider error"))

        gateway.register_provider(failing_provider)

        messages = [AIMessage(role="user", content="Hello")]
        with pytest.raises(RuntimeError, match="Provider error"):
            await gateway.chat(messages)

    def test_get_usage_summary(self, gateway):
        """Usage summary aggregates by provider."""
        gateway._usage_log = [
            {"provider": "openai", "operation": "chat", "usage": {"total_tokens": 100}},
            {"provider": "openai", "operation": "chat", "usage": {"total_tokens": 50}},
            {"provider": "anthropic", "operation": "chat", "usage": {"total_tokens": 75}},
        ]

        summary = gateway.get_usage_summary()

        assert summary["openai"]["operations"] == 2
        assert summary["openai"]["tokens"] == 150
        assert summary["anthropic"]["operations"] == 1
        assert summary["anthropic"]["tokens"] == 75


class TestAIMessageDataclass:
    """Tests for AIMessage dataclass."""

    def test_message_creation(self):
        """AIMessage can be created with required fields."""
        msg = AIMessage(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"
        assert msg.name is None

    def test_message_to_dict(self):
        """AIMessage converts to dict correctly."""
        msg = AIMessage(role="user", content="Hello")
        d = msg.to_dict()
        assert d == {"role": "user", "content": "Hello"}

    def test_message_to_dict_with_name(self):
        """AIMessage includes name in dict when present."""
        msg = AIMessage(role="user", content="Hello", name="TestUser")
        d = msg.to_dict()
        assert d == {"role": "user", "content": "Hello", "name": "TestUser"}


class TestGenerationConfig:
    """Tests for GenerationConfig dataclass."""

    def test_config_defaults(self):
        """GenerationConfig has sensible defaults."""
        config = GenerationConfig()
        assert config.max_tokens == 2048
        assert config.temperature == 0.7
        assert config.top_p == 0.9
        assert config.top_k == 40
        assert config.stop_sequences == []
        assert config.stream is False


class TestSimpleModeViewAuditFindings:
    """
    Regression tests for bugs found in SimpleModeView during audit.

    Note: SimpleModeView is a workflow builder, not AI Chat.
    The plan had a naming confusion - these tests document fixes
    to the workflow builder UI component.
    """

    @pytest.fixture
    def mock_page(self):
        """Create a mock Flet page for testing."""
        page = MagicMock()
        page.update = MagicMock()
        page.open = MagicMock()
        page.close = MagicMock()
        return page

    @pytest.fixture
    def mock_workflow(self):
        """Create a mock workflow for testing."""
        from src.core.workflow.models import Workflow
        workflow = Workflow(name="Test Workflow")
        return workflow

    def test_simple_mode_view_initializes_dialog_tracking(self, mock_workflow):
        """SimpleModeView initializes with dialog tracking attribute."""
        from src.ui.views.simple_mode import SimpleModeView
        view = SimpleModeView(workflow=mock_workflow)

        # BUG FIX: Added _current_dialog to track dialogs for proper close
        assert hasattr(view, "_current_dialog")
        assert view._current_dialog is None

    def test_simple_mode_view_state_attributes(self, mock_workflow):
        """SimpleModeView initializes all state attributes correctly."""
        from src.ui.views.simple_mode import SimpleModeView
        view = SimpleModeView(workflow=mock_workflow)

        assert view.workflow == mock_workflow
        assert view.selected_step_index is None
        assert view._steps_column is None
        assert view._properties_container is None


class TestGatewaySingleton:
    """Tests for gateway singleton behavior."""

    def test_get_gateway_returns_singleton(self):
        """get_gateway returns the same instance."""
        # Reset the singleton for testing
        import src.ai.gateway as gateway_module
        gateway_module._gateway = None

        gw1 = get_gateway()
        gw2 = get_gateway()

        assert gw1 is gw2

    def test_get_gateway_creates_instance(self):
        """get_gateway creates instance when none exists."""
        import src.ai.gateway as gateway_module
        gateway_module._gateway = None

        gw = get_gateway()

        assert gw is not None
        assert isinstance(gw, AIGateway)
