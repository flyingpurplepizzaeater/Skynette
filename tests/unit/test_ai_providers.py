"""Unit tests for AI Hub provider management UI logic."""

import pytest
from unittest.mock import patch, MagicMock
import flet as ft

from src.ui.views.ai_hub import AIHubView
from src.ui.views.ai_hub.providers import ProvidersTab
from tests.helpers import extract_text_from_control


class TestProviderStatusDisplay:
    """Test provider status display logic."""

    @patch('src.ai.security.has_api_key')
    def test_providers_show_configured_status(self, mock_has_key):
        """Test providers display correct status based on stored config."""
        # Setup - OpenAI has API key, Anthropic does not
        def has_key_side_effect(provider):
            return provider == "openai"

        mock_has_key.side_effect = has_key_side_effect

        # Create ProvidersTab instance (page will be None, which is fine for this test)
        from src.ui.views.ai_hub.state import AIHubState
        state = AIHubState()
        providers_tab = ProvidersTab(page=None, state=state)
        
        # Build the UI and get the content
        content = providers_tab.build()

        # Extract all text from the UI
        all_text = extract_text_from_control(content)

        # Verify that "Configured" appears in the output
        assert "Configured" in all_text

    @patch('src.ai.security.has_api_key')
    def test_providers_show_not_configured_status(self, mock_has_key):
        """Test providers show 'Not configured' when no API key exists."""
        # Setup - No API keys stored
        mock_has_key.return_value = False

        # Create ProvidersTab instance
        from src.ui.views.ai_hub.state import AIHubState
        state = AIHubState()
        providers_tab = ProvidersTab(page=None, state=state)
        
        # Build the UI and get the content
        content = providers_tab.build()

        # Extract all text from the UI
        all_text = extract_text_from_control(content)

        # Verify that "Not configured" appears in the output
        assert "Not configured" in all_text

    @patch('src.ai.security.has_api_key')
    def test_local_provider_always_ready(self, mock_has_key):
        """Test local provider shows ready status (no key required)."""
        # Setup
        mock_has_key.return_value = False

        # Create ProvidersTab instance
        from src.ui.views.ai_hub.state import AIHubState
        state = AIHubState()
        providers_tab = ProvidersTab(page=None, state=state)
        
        # Build the UI and get the content
        content = providers_tab.build()

        # Extract all text from the UI
        all_text = extract_text_from_control(content)

        # Verify that local provider shows ready status (check for "Ready" or "Demo")
        assert "Ready" in all_text or "Demo" in all_text
