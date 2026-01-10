"""Unit tests for AI Hub provider management UI logic."""

import pytest
from unittest.mock import patch, MagicMock
import flet as ft

from src.ui.views.ai_hub import AIHubView


def extract_text_from_control(control):
    """Extract all text content from a Flet control tree."""
    texts = []

    if isinstance(control, ft.Text):
        texts.append(control.value or "")
    elif isinstance(control, ft.ElevatedButton):
        # Button text is stored in content attribute
        if isinstance(control.content, str):
            texts.append(control.content)
        elif control.content:
            texts.extend(extract_text_from_control(control.content))

    # Recursively search in content (skip for buttons since we handled it above)
    if not isinstance(control, ft.ElevatedButton) and hasattr(control, 'content') and control.content:
        if isinstance(control.content, str):
            texts.append(control.content)
        else:
            texts.extend(extract_text_from_control(control.content))

    # Recursively search in controls
    if hasattr(control, 'controls') and control.controls:
        for child in control.controls:
            texts.extend(extract_text_from_control(child))

    return texts


class TestProviderStatusDisplay:
    """Test provider status display logic."""

    @patch('src.ai.security.has_api_key')
    def test_providers_show_configured_status(self, mock_has_key):
        """Test providers display correct status based on stored config."""
        # Setup - OpenAI has API key, Anthropic does not
        def has_key_side_effect(provider):
            return provider == "openai"

        mock_has_key.side_effect = has_key_side_effect

        # Create AIHubView instance (page will be None, which is fine for this test)
        ai_hub = AIHubView()
        providers_tab = ai_hub._build_providers_tab()

        # Extract all text from the UI
        all_text = extract_text_from_control(providers_tab)
        all_text_str = " ".join(all_text)

        # Verify that "Configured ✓" appears in the output
        assert "Configured ✓" in all_text_str or "Configured" in all_text_str

    @patch('src.ai.security.has_api_key')
    def test_providers_show_not_configured_status(self, mock_has_key):
        """Test providers show 'Not configured' when no API key exists."""
        # Setup - No API keys stored
        mock_has_key.return_value = False

        # Create AIHubView instance
        ai_hub = AIHubView()
        providers_tab = ai_hub._build_providers_tab()

        # Extract all text from the UI
        all_text = extract_text_from_control(providers_tab)
        all_text_str = " ".join(all_text)

        # Verify that "Not configured" appears in the output
        assert "Not configured" in all_text_str

    @patch('src.ai.security.has_api_key')
    def test_local_provider_always_ready(self, mock_has_key):
        """Test local provider shows ready status (no key required)."""
        # Setup
        mock_has_key.return_value = False

        # Create AIHubView instance
        ai_hub = AIHubView()
        providers_tab = ai_hub._build_providers_tab()

        # Extract all text from the UI
        all_text = extract_text_from_control(providers_tab)
        all_text_str = " ".join(all_text)

        # Verify that local provider shows ready status
        assert "Ready (no key required)" in all_text_str or "Ready" in all_text_str
