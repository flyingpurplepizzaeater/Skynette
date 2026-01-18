# tests/unit/test_ai_hub_refactor.py
"""Tests for refactored AIHubView components.

These tests verify the modular AIHubView components work correctly:
- AIHubState: Centralized state container with listener pattern
- SetupWizard: Multi-step provider configuration
- ProvidersTab: Provider management with API keys
- ModelLibraryTab: Model browsing and downloading
"""

import pytest
from unittest.mock import MagicMock, patch

from src.ui.views.ai_hub.state import AIHubState
from src.ui.views.ai_hub.wizard import SetupWizard
from src.ui.views.ai_hub.providers import ProvidersTab
from src.ui.views.ai_hub.model_library import ModelLibraryTab


class TestAIHubState:
    """Tests for centralized state container."""

    def test_initial_state(self):
        """Verify initial state values are correct."""
        state = AIHubState()
        assert state.wizard_step == 0
        assert state.selected_providers == []
        assert state.provider_configs == {}
        assert state.ollama_connected is False
        assert state.ollama_models == []

    def test_wizard_step_mutation_notifies_listeners(self):
        """Verify set_wizard_step calls registered listeners."""
        state = AIHubState()
        listener = MagicMock()
        state.add_listener(listener)

        state.set_wizard_step(1)

        assert state.wizard_step == 1
        listener.assert_called_once()

    def test_toggle_provider_adds_and_removes(self):
        """Verify toggle_provider correctly adds and removes providers."""
        state = AIHubState()

        # First toggle adds provider
        state.toggle_provider("openai")
        assert "openai" in state.selected_providers

        # Second toggle removes provider
        state.toggle_provider("openai")
        assert "openai" not in state.selected_providers

    def test_toggle_provider_notifies_listeners(self):
        """Verify toggle_provider calls registered listeners."""
        state = AIHubState()
        listener = MagicMock()
        state.add_listener(listener)

        state.toggle_provider("openai")

        listener.assert_called_once()

    def test_remove_listener(self):
        """Verify removed listeners are not called."""
        state = AIHubState()
        listener = MagicMock()
        state.add_listener(listener)
        state.remove_listener(listener)

        state.set_wizard_step(1)

        listener.assert_not_called()

    def test_set_provider_config(self):
        """Verify set_provider_config stores full config dict."""
        state = AIHubState()
        config = {"api_key": "test-key", "org_id": "test-org"}

        state.set_provider_config("openai", config)

        assert state.provider_configs["openai"] == config

    def test_update_provider_config(self):
        """Verify update_provider_config updates single key."""
        state = AIHubState()

        state.update_provider_config("openai", "api_key", "test-key")

        assert state.provider_configs["openai"]["api_key"] == "test-key"

    def test_update_provider_config_creates_dict_if_missing(self):
        """Verify update_provider_config creates provider dict if needed."""
        state = AIHubState()

        state.update_provider_config("anthropic", "api_key", "test-key")

        assert "anthropic" in state.provider_configs
        assert state.provider_configs["anthropic"]["api_key"] == "test-key"

    def test_set_ollama_status(self):
        """Verify set_ollama_status updates connection status."""
        state = AIHubState()

        state.set_ollama_status(True, ["llama3.2", "mistral"])

        assert state.ollama_connected is True
        assert state.ollama_models == ["llama3.2", "mistral"]

    def test_reset_wizard(self):
        """Verify reset_wizard clears wizard-related state."""
        state = AIHubState()
        state.set_wizard_step(2)
        state.toggle_provider("openai")
        state.set_provider_config("openai", {"api_key": "test"})

        state.reset_wizard()

        assert state.wizard_step == 0
        assert state.selected_providers == []
        assert state.provider_configs == {}

    def test_multiple_listeners(self):
        """Verify multiple listeners are all called."""
        state = AIHubState()
        listener1 = MagicMock()
        listener2 = MagicMock()
        state.add_listener(listener1)
        state.add_listener(listener2)

        state.set_wizard_step(1)

        listener1.assert_called_once()
        listener2.assert_called_once()


class TestSetupWizard:
    """Tests for extracted SetupWizard component."""

    @pytest.fixture
    def mock_page(self):
        """Create a mock Flet page."""
        page = MagicMock()
        page.update = MagicMock()
        return page

    @pytest.fixture
    def wizard(self, mock_page):
        """Create a SetupWizard with mocked page."""
        state = AIHubState()
        return SetupWizard(page=mock_page, state=state)

    def test_wizard_initial_step_is_zero(self, wizard):
        """Verify wizard starts at step 0."""
        assert wizard.state.wizard_step == 0

    def test_wizard_state_shared_with_component(self, wizard):
        """Verify state object is correctly shared."""
        wizard.state.toggle_provider("openai")
        assert "openai" in wizard.state.selected_providers

    def test_wizard_state_preserved_on_back(self, wizard):
        """Verify provider selection is preserved when going back."""
        wizard.state.toggle_provider("openai")
        wizard.state.set_wizard_step(1)
        wizard.state.set_wizard_step(0)

        assert "openai" in wizard.state.selected_providers

    def test_wizard_builds_without_error(self, wizard):
        """Verify build() runs without raising exceptions."""
        # Should not raise
        result = wizard.build()
        assert result is not None

    def test_wizard_step_navigation(self, wizard):
        """Verify step navigation updates state correctly."""
        wizard._wizard_next_step()
        assert wizard.state.wizard_step == 1

        wizard._wizard_prev_step()
        assert wizard.state.wizard_step == 0

    def test_wizard_prev_step_at_zero_stays_zero(self, wizard):
        """Verify going back at step 0 stays at 0."""
        assert wizard.state.wizard_step == 0
        wizard._wizard_prev_step()
        assert wizard.state.wizard_step == 0


class TestProvidersTab:
    """Tests for extracted ProvidersTab component."""

    @pytest.fixture
    def mock_page(self):
        """Create a mock Flet page."""
        page = MagicMock()
        page.update = MagicMock()
        page.open = MagicMock()
        page.close = MagicMock()
        return page

    @pytest.fixture
    def providers_tab(self, mock_page):
        """Create a ProvidersTab with mocked page."""
        state = AIHubState()
        return ProvidersTab(page=mock_page, state=state)

    def test_providers_tab_uses_state(self, providers_tab):
        """Verify ProvidersTab has access to state."""
        providers_tab.state.set_provider_config("openai", {"api_key": "test"})
        assert providers_tab.state.provider_configs["openai"]["api_key"] == "test"

    def test_providers_tab_builds_without_error(self, providers_tab):
        """Verify build() runs without raising exceptions."""
        with patch("src.ai.security.has_api_key", return_value=False):
            result = providers_tab.build()
            assert result is not None

    def test_providers_tab_shows_all_providers(self, providers_tab):
        """Verify build includes all expected providers."""
        from src.ui.views.ai_hub.providers import PROVIDER_DEFINITIONS

        # Should have 6 providers defined (including Ollama)
        assert len(PROVIDER_DEFINITIONS) == 6
        provider_ids = [p["id"] for p in PROVIDER_DEFINITIONS]
        assert "openai" in provider_ids
        assert "anthropic" in provider_ids
        assert "ollama" in provider_ids
        assert "local" in provider_ids


class TestModelLibraryTab:
    """Tests for extracted ModelLibraryTab component."""

    @pytest.fixture
    def mock_page(self):
        """Create a mock Flet page."""
        page = MagicMock()
        page.update = MagicMock()
        page.open = MagicMock()
        page.close = MagicMock()
        page.overlay = []
        return page

    @pytest.fixture
    def model_library(self, mock_page):
        """Create a ModelLibraryTab with mocked page."""
        return ModelLibraryTab(page=mock_page)

    def test_model_library_initializes(self, model_library):
        """Verify ModelLibraryTab initializes correctly."""
        assert model_library is not None
        assert model_library.hub is not None

    def test_model_library_has_required_methods(self, model_library):
        """Verify ModelLibraryTab has all expected methods."""
        assert hasattr(model_library, "build")
        assert hasattr(model_library, "refresh_models")
        assert hasattr(model_library, "_build_installed_tab")
        assert hasattr(model_library, "_build_huggingface_tab")
        assert hasattr(model_library, "_build_ollama_tab")
        assert hasattr(model_library, "_build_import_tab")

    def test_model_library_builds_without_error(self, model_library):
        """Verify build() runs without raising exceptions."""
        result = model_library.build()
        assert result is not None

    def test_ollama_library_models_defined(self):
        """Verify Ollama library models are properly defined."""
        from src.ui.views.ai_hub.model_library import OLLAMA_LIBRARY_MODELS

        assert len(OLLAMA_LIBRARY_MODELS) >= 6
        model_names = [m["name"] for m in OLLAMA_LIBRARY_MODELS]
        assert "llama3.2" in model_names
        assert "mistral" in model_names


class TestAIHubViewIntegration:
    """Integration tests for AIHubView coordinator."""

    @pytest.fixture
    def mock_page(self):
        """Create a mock Flet page."""
        page = MagicMock()
        page.update = MagicMock()
        return page

    def test_ai_hub_view_imports(self):
        """Verify AIHubView can be imported from package."""
        from src.ui.views.ai_hub import AIHubView
        assert AIHubView is not None

    def test_ai_hub_view_creates_state(self, mock_page):
        """Verify AIHubView creates its state container."""
        from src.ui.views.ai_hub import AIHubView

        view = AIHubView(page=mock_page)
        assert view.state is not None
        assert isinstance(view.state, AIHubState)

    @patch("src.ui.views.usage_dashboard.asyncio.create_task")
    def test_ai_hub_view_builds_without_error(self, mock_task, mock_page):
        """Verify AIHubView.build() runs without raising exceptions."""
        from src.ui.views.ai_hub import AIHubView

        view = AIHubView(page=mock_page)
        result = view.build()
        assert result is not None

    @patch("src.ui.views.usage_dashboard.asyncio.create_task")
    def test_ai_hub_view_creates_components(self, mock_task, mock_page):
        """Verify AIHubView creates all sub-components."""
        from src.ui.views.ai_hub import AIHubView

        view = AIHubView(page=mock_page)
        view.build()

        assert view._wizard is not None
        assert view._providers is not None
        assert view._library is not None

    @patch("src.ui.views.usage_dashboard.asyncio.create_task")
    def test_components_share_state(self, mock_task, mock_page):
        """Verify wizard and providers share the same state."""
        from src.ui.views.ai_hub import AIHubView

        view = AIHubView(page=mock_page)
        view.build()

        # Both wizard and providers should reference the same state
        assert view._wizard.state is view.state
        assert view._providers.state is view.state
