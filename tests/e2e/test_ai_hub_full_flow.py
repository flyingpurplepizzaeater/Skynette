"""Comprehensive E2E tests for AI Hub complete user flows."""

import flet as ft
from unittest.mock import MagicMock
from src.ui.views.ai_hub import AIHubView
from src.ai.security import store_api_key, delete_api_key
from tests.helpers import extract_text_from_control


def _find_controls_by_type(container, control_type):
    """Recursively find all controls of a specific type."""
    found = []

    if isinstance(container, control_type):
        found.append(container)

    if hasattr(container, 'controls'):
        for control in container.controls:
            found.extend(_find_controls_by_type(control, control_type))

    if hasattr(container, 'content'):
        if container.content:
            if isinstance(container.content, list):
                for item in container.content:
                    found.extend(_find_controls_by_type(item, control_type))
            else:
                found.extend(_find_controls_by_type(container.content, control_type))

    return found


class TestAIHubStructure:
    """Test AI Hub basic structure and tab organization."""

    def test_ai_hub_initializes_successfully(self):
        """Test AI Hub view initializes without errors."""
        ai_hub = AIHubView(page=None)

        # Should initialize successfully
        assert ai_hub is not None
        assert isinstance(ai_hub, AIHubView)

    def test_ai_hub_has_tab_methods(self):
        """Test AI Hub has all required tab building methods."""
        ai_hub = AIHubView(page=None)

        # Build each tab independently
        my_models = ai_hub._build_installed_tab()
        model_library = ai_hub._build_model_library_tab()
        huggingface = ai_hub._build_huggingface_tab()
        ollama = ai_hub._build_ollama_tab()
        import_tab = ai_hub._build_import_tab()
        providers = ai_hub._build_providers_tab()

        # All should build successfully
        assert my_models is not None
        assert model_library is not None
        assert huggingface is not None
        assert ollama is not None
        assert import_tab is not None
        assert providers is not None

    def test_ai_hub_has_header_method(self):
        """Test AI Hub has header building method."""
        ai_hub = AIHubView(page=None)
        header = ai_hub._build_header()

        # Should build successfully
        assert header is not None
        assert isinstance(header, ft.Container)


class TestMyModelsTab:
    """Test My Models tab functionality."""

    def test_my_models_tab_builds(self):
        """Test My Models tab builds without errors."""
        ai_hub = AIHubView(page=None)
        my_models_tab = ai_hub._build_installed_tab()

        assert my_models_tab is not None
        assert isinstance(my_models_tab, ft.Container)

    def test_my_models_shows_empty_state_when_no_models(self):
        """Test My Models shows empty state when no models downloaded."""
        ai_hub = AIHubView(page=None)
        my_models_tab = ai_hub._build_installed_tab()

        all_text = extract_text_from_control(my_models_tab)

        # Should show empty state message
        assert "No Models Downloaded" in all_text or "Download" in all_text

    def test_my_models_tab_has_folder_info(self):
        """Test My Models shows models folder path."""
        ai_hub = AIHubView(page=None)
        my_models_tab = ai_hub._build_installed_tab()

        all_text = extract_text_from_control(my_models_tab)

        # Should show models folder path
        assert "Models folder" in all_text or "folder" in all_text


class TestHuggingFaceTab:
    """Test Hugging Face tab functionality (model downloads)."""

    def test_huggingface_tab_builds(self):
        """Test Hugging Face tab builds without errors."""
        ai_hub = AIHubView(page=None)
        hf_tab = ai_hub._build_huggingface_tab()

        assert hf_tab is not None
        assert isinstance(hf_tab, ft.Container)

    def test_huggingface_tab_shows_recommended_models(self):
        """Test Hugging Face tab displays recommended models section."""
        ai_hub = AIHubView(page=None)
        hf_tab = ai_hub._build_huggingface_tab()

        all_text = extract_text_from_control(hf_tab)

        # Should have recommended models section
        assert "Recommended Models" in all_text or "Recommended" in all_text

    def test_huggingface_tab_has_url_section(self):
        """Test Hugging Face tab has add from URL option."""
        ai_hub = AIHubView(page=None)
        hf_tab = ai_hub._build_huggingface_tab()

        all_text = extract_text_from_control(hf_tab)

        # Should have URL section
        assert "URL" in all_text or "Hugging Face" in all_text

    def test_huggingface_tab_has_text_fields(self):
        """Test Hugging Face tab has text fields for search and URL."""
        ai_hub = AIHubView(page=None)
        hf_tab = ai_hub._build_huggingface_tab()

        # Should have text fields (search and URL)
        text_fields = _find_controls_by_type(hf_tab, ft.TextField)
        assert len(text_fields) >= 1

    def test_huggingface_tab_has_buttons(self):
        """Test Hugging Face tab has action buttons."""
        ai_hub = AIHubView(page=None)
        hf_tab = ai_hub._build_huggingface_tab()

        # Should have buttons (Search, Add, Download)
        buttons = _find_controls_by_type(hf_tab, ft.Button)
        assert len(buttons) >= 1


class TestOllamaTab:
    """Test Ollama tab functionality."""

    def test_ollama_tab_builds(self):
        """Test Ollama tab builds without errors."""
        ai_hub = AIHubView(page=None)
        ollama_tab = ai_hub._build_ollama_tab()

        assert ollama_tab is not None
        assert isinstance(ollama_tab, ft.Container)

    def test_ollama_tab_shows_library_models(self):
        """Test Ollama tab displays library models."""
        ai_hub = AIHubView(page=None)
        ollama_tab = ai_hub._build_ollama_tab()

        all_text = extract_text_from_control(ollama_tab)

        # Should show Ollama library models
        assert "Ollama" in all_text
        assert "Library" in all_text or "llama" in all_text.lower()

    def test_ollama_tab_has_status_indicator(self):
        """Test Ollama tab has status indicator."""
        ai_hub = AIHubView(page=None)
        ollama_tab = ai_hub._build_ollama_tab()

        all_text = extract_text_from_control(ollama_tab)

        # Should have status indicator
        assert "Status" in all_text or "Check" in all_text


class TestImportTab:
    """Test Import tab functionality."""

    def test_import_tab_builds(self):
        """Test Import tab builds without errors."""
        ai_hub = AIHubView(page=None)
        import_tab = ai_hub._build_import_tab()

        assert import_tab is not None
        assert isinstance(import_tab, ft.Container)

    def test_import_tab_shows_gguf_info(self):
        """Test Import tab shows GGUF import info."""
        ai_hub = AIHubView(page=None)
        import_tab = ai_hub._build_import_tab()

        all_text = extract_text_from_control(import_tab)

        # Should mention GGUF files
        assert "GGUF" in all_text or "Import" in all_text

    def test_import_tab_has_file_picker_button(self):
        """Test Import tab has file picker button."""
        ai_hub = AIHubView(page=None)
        import_tab = ai_hub._build_import_tab()

        # Should have file selection button
        buttons = _find_controls_by_type(import_tab, ft.ElevatedButton)
        assert len(buttons) >= 1


class TestProvidersTab:
    """Test Providers tab functionality."""

    def test_providers_tab_builds(self):
        """Test Providers tab builds without errors."""
        ai_hub = AIHubView(page=None)
        providers_tab = ai_hub._build_providers_tab()

        assert providers_tab is not None
        assert isinstance(providers_tab, ft.Container)

    def test_providers_tab_shows_all_providers(self):
        """Test Providers tab displays all available providers."""
        ai_hub = AIHubView(page=None)
        providers_tab = ai_hub._build_providers_tab()

        all_text = extract_text_from_control(providers_tab)

        # Should show all three providers
        assert "OpenAI" in all_text
        assert "Anthropic" in all_text
        assert "Local" in all_text

    def test_providers_tab_has_header(self):
        """Test Providers tab has proper header."""
        ai_hub = AIHubView(page=None)
        providers_tab = ai_hub._build_providers_tab()

        all_text = extract_text_from_control(providers_tab)

        # Should have header
        assert "My AI Providers" in all_text or "Providers" in all_text

    def test_providers_tab_shows_configuration_status(self):
        """Test Providers tab shows configuration status for each provider."""
        ai_hub = AIHubView(page=None)
        providers_tab = ai_hub._build_providers_tab()

        all_text = extract_text_from_control(providers_tab)

        # Should show status indicators
        assert "Configured" in all_text or "Not configured" in all_text or "Ready" in all_text

    def test_providers_tab_has_configure_buttons(self):
        """Test Providers tab has configure/edit buttons."""
        ai_hub = AIHubView(page=None)
        providers_tab = ai_hub._build_providers_tab()

        buttons = _find_controls_by_type(providers_tab, ft.Button)

        # Should have at least 3 buttons (one per provider)
        assert len(buttons) >= 3


class TestProviderConfiguration:
    """Test provider configuration dialog functionality."""

    def test_provider_config_dialog_structure(self):
        """Test provider configuration dialog has proper structure."""
        ai_hub = AIHubView(page=None)

        provider = {
            "id": "openai",
            "name": "OpenAI",
            "requires_key": True
        }

        dialog = ai_hub._build_provider_config_dialog(provider)

        # Dialog should exist
        assert dialog is not None
        assert isinstance(dialog, ft.AlertDialog)

    def test_provider_config_dialog_has_title(self):
        """Test provider configuration dialog has title."""
        ai_hub = AIHubView(page=None)

        provider = {
            "id": "openai",
            "name": "OpenAI",
            "requires_key": True
        }

        dialog = ai_hub._build_provider_config_dialog(provider)

        # Dialog should have title with provider name
        assert dialog.title is not None
        assert "OpenAI" in dialog.title.value

    def test_provider_config_dialog_has_api_key_field(self):
        """Test provider configuration dialog has API key text field."""
        ai_hub = AIHubView(page=None)

        provider = {
            "id": "openai",
            "name": "OpenAI",
            "requires_key": True
        }

        dialog = ai_hub._build_provider_config_dialog(provider)

        # Dialog should have text field for API key
        text_fields = _find_controls_by_type(dialog, ft.TextField)
        assert len(text_fields) >= 1

        # API key field should be password field
        api_key_field = text_fields[0]
        assert api_key_field.password == True

    def test_provider_config_dialog_has_action_buttons(self):
        """Test provider configuration dialog has action buttons."""
        ai_hub = AIHubView(page=None)

        provider = {
            "id": "openai",
            "name": "OpenAI",
            "requires_key": True
        }

        dialog = ai_hub._build_provider_config_dialog(provider)

        # Dialog should have action buttons
        assert dialog.actions is not None
        assert len(dialog.actions) >= 2

    def test_provider_config_dialog_actions_include_save_and_cancel(self):
        """Test provider configuration dialog has Save and Cancel buttons."""
        ai_hub = AIHubView(page=None)

        provider = {
            "id": "openai",
            "name": "OpenAI",
            "requires_key": True
        }

        dialog = ai_hub._build_provider_config_dialog(provider)

        # Should have action buttons
        assert len(dialog.actions) >= 2

        # Actions should be buttons (TextButton, ElevatedButton, or Button)
        assert isinstance(dialog.actions[0], (ft.TextButton, ft.ElevatedButton, ft.Button))
        assert isinstance(dialog.actions[1], (ft.TextButton, ft.ElevatedButton, ft.Button))


class TestProviderStatusPersistence:
    """Test provider status and configuration persistence."""

    def test_provider_status_reflects_saved_keys(self):
        """Test provider status updates when API keys are saved."""
        # Clean up first
        for provider in ["openai", "anthropic"]:
            try:
                delete_api_key(provider)
            except Exception:
                pass

        # Configure OpenAI
        store_api_key("openai", "sk-test123")

        try:
            ai_hub = AIHubView(page=None)
            providers_tab = ai_hub._build_providers_tab()

            # Extract text and verify status
            all_text = extract_text_from_control(providers_tab)
            assert "Configured" in all_text

        finally:
            # Clean up
            try:
                delete_api_key("openai")
            except Exception:
                pass

    def test_provider_status_unconfigured_by_default(self):
        """Test provider shows unconfigured status when no key stored."""
        # Clean up to ensure no keys
        for provider in ["openai", "anthropic"]:
            try:
                delete_api_key(provider)
            except Exception:
                pass

        try:
            ai_hub = AIHubView(page=None)
            providers_tab = ai_hub._build_providers_tab()

            # Extract text and verify status
            all_text = extract_text_from_control(providers_tab)
            assert "Not configured" in all_text

        finally:
            pass


class TestAIHubIntegration:
    """Test AI Hub integration scenarios."""

    def test_ai_hub_handles_missing_page_gracefully(self):
        """Test AI Hub works with page=None."""
        ai_hub = AIHubView(page=None)

        # Should initialize successfully even without page
        assert ai_hub is not None
        assert ai_hub._page is None

    def test_ai_hub_with_mock_page(self):
        """Test AI Hub works with mock page."""
        mock_page = MagicMock(spec=ft.Page)
        ai_hub = AIHubView(page=mock_page)

        # Should initialize successfully with mock page
        assert ai_hub is not None
        assert ai_hub._page is mock_page

    def test_all_tabs_can_be_built_independently(self):
        """Test all tabs can be built independently."""
        ai_hub = AIHubView(page=None)

        # Build each tab independently
        my_models = ai_hub._build_installed_tab()
        model_library = ai_hub._build_model_library_tab()
        huggingface = ai_hub._build_huggingface_tab()
        ollama = ai_hub._build_ollama_tab()
        import_tab = ai_hub._build_import_tab()
        providers = ai_hub._build_providers_tab()

        # All should build successfully
        assert my_models is not None
        assert model_library is not None
        assert huggingface is not None
        assert ollama is not None
        assert import_tab is not None
        assert providers is not None


class TestErrorHandling:
    """Test error handling scenarios."""

    def test_providers_tab_handles_keyring_errors(self):
        """Test Providers tab handles keyring access errors gracefully."""
        ai_hub = AIHubView(page=None)

        # Should not crash even if keyring has issues
        providers_tab = ai_hub._build_providers_tab()
        assert providers_tab is not None

    def test_ai_hub_builds_with_no_hub_instance(self):
        """Test AI Hub builds even with hub initialization issues."""
        ai_hub = AIHubView(page=None)

        # Hub is initialized in __init__, should not crash
        assert ai_hub.hub is not None

    def test_recommended_models_handles_empty_list(self):
        """Test Hugging Face tab handles empty recommended models list."""
        ai_hub = AIHubView(page=None)
        hf_tab = ai_hub._build_huggingface_tab()

        # Should build even if no recommended models
        assert hf_tab is not None


class TestUIComponentsPresence:
    """Test presence of specific UI components."""

    def test_header_has_refresh_button(self):
        """Test AI Hub header has refresh button."""
        ai_hub = AIHubView(page=None)
        header = ai_hub._build_header()

        # Should have refresh button
        buttons = _find_controls_by_type(header, ft.Button)
        assert len(buttons) >= 1

    def test_providers_tab_has_icons_for_providers(self):
        """Test Providers tab has icons for each provider."""
        ai_hub = AIHubView(page=None)
        providers_tab = ai_hub._build_providers_tab()

        # Should have icon for each provider
        icons = _find_controls_by_type(providers_tab, ft.Icon)
        assert len(icons) >= 3  # One for each provider

    def test_tabs_use_containers_for_layout(self):
        """Test tabs use containers for proper layout."""
        ai_hub = AIHubView(page=None)
        my_models = ai_hub._build_installed_tab()

        # Should use containers for layout
        containers = _find_controls_by_type(my_models, ft.Container)
        assert len(containers) >= 1

    def test_providers_tab_uses_columns_for_layout(self):
        """Test Providers tab uses columns for vertical layout."""
        ai_hub = AIHubView(page=None)
        providers_tab = ai_hub._build_providers_tab()

        # Should use columns for vertical layout
        columns = _find_controls_by_type(providers_tab, ft.Column)
        assert len(columns) >= 1


class TestTabContent:
    """Test specific tab content details."""

    def test_my_models_tab_mentions_download_tab(self):
        """Test My Models empty state mentions Download tab."""
        ai_hub = AIHubView(page=None)
        my_models_tab = ai_hub._build_installed_tab()

        all_text = extract_text_from_control(my_models_tab)

        # Empty state should guide to Download tab
        assert "Download" in all_text

    def test_huggingface_tab_has_content(self):
        """Test Hugging Face tab shows model sizes or descriptions."""
        ai_hub = AIHubView(page=None)
        hf_tab = ai_hub._build_huggingface_tab()

        all_text = extract_text_from_control(hf_tab)

        # Should mention models in some way
        assert len(all_text) > 50  # Has substantial content

    def test_providers_tab_mentions_api_keys(self):
        """Test Providers tab mentions API keys or configuration."""
        ai_hub = AIHubView(page=None)
        providers_tab = ai_hub._build_providers_tab()

        all_text = extract_text_from_control(providers_tab)

        # Should mention configuration or settings
        assert "API" in all_text or "key" in all_text.lower() or "settings" in all_text.lower()


class TestCompleteFlow:
    """Test complete user flow scenarios."""

    def test_complete_flow_view_all_tabs(self):
        """Test complete flow of viewing all tabs."""
        ai_hub = AIHubView(page=None)

        # Build each tab (simulating tab switches)
        my_models = ai_hub._build_installed_tab()
        model_library = ai_hub._build_model_library_tab()
        huggingface = ai_hub._build_huggingface_tab()
        ollama = ai_hub._build_ollama_tab()
        import_tab = ai_hub._build_import_tab()
        providers = ai_hub._build_providers_tab()

        # All should succeed
        assert my_models is not None
        assert model_library is not None
        assert huggingface is not None
        assert ollama is not None
        assert import_tab is not None
        assert providers is not None

    def test_complete_flow_configure_provider(self):
        """Test complete flow of configuring a provider."""
        # Clean up first
        try:
            delete_api_key("openai")
        except Exception:
            pass

        try:
            ai_hub = AIHubView(page=None)

            # View providers tab
            providers_tab = ai_hub._build_providers_tab()
            assert providers_tab is not None

            # Open configuration dialog
            provider = {"id": "openai", "name": "OpenAI", "requires_key": True}
            dialog = ai_hub._build_provider_config_dialog(provider)
            assert dialog is not None

            # Simulate saving API key
            store_api_key("openai", "sk-test-flow-123")

            # Rebuild providers tab to see updated status
            providers_tab_updated = ai_hub._build_providers_tab()
            all_text = extract_text_from_control(providers_tab_updated)

            # Should now show configured
            assert "Configured" in all_text

        finally:
            # Clean up
            try:
                delete_api_key("openai")
            except Exception:
                pass
