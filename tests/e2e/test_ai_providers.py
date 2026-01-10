"""E2E tests for AI Hub provider management."""

import flet as ft
from src.ui.views.ai_hub import AIHubView


def extract_text_from_control(control):
    """Recursively extract all text values from a Flet control."""
    texts = []

    if hasattr(control, 'value') and isinstance(control.value, str):
        texts.append(control.value)

    if hasattr(control, 'controls'):
        for child in control.controls:
            texts.extend(extract_text_from_control(child))

    if hasattr(control, 'content') and control.content:
        texts.extend(extract_text_from_control(control.content))

    return texts


def test_providers_show_configured_status(page: ft.Page):
    """Test providers display correct status based on stored config."""
    from src.ai.security import store_api_key, delete_api_key

    # Clean up first in case previous test failed
    try:
        delete_api_key("openai")
    except:
        pass

    # Set up - store API key for OpenAI
    store_api_key("openai", "sk-test123")

    try:
        ai_hub = AIHubView(page=page)
        providers_tab = ai_hub._build_providers_tab()

        # Extract all text from the providers tab
        all_texts = extract_text_from_control(providers_tab)
        all_text = " ".join(all_texts)

        # Find OpenAI provider card
        # Should show "Configured" status
        assert "Configured" in all_text, f"Expected 'Configured' in UI text, but got: {all_text}"
    finally:
        # Clean up - remove test API key
        try:
            delete_api_key("openai")
        except:
            pass
