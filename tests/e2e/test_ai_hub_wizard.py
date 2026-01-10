"""
AI Hub Setup Wizard tests.

Unit tests for the setup wizard tab structure and navigation.
"""

import flet as ft
import pytest
from src.ui.views.ai_hub import AIHubView


def _find_tabs_control(view):
    """Helper to find the Tabs control in the view hierarchy."""
    def find_in_controls(control):
        if isinstance(control, ft.Tabs):
            return control
        if hasattr(control, 'controls'):
            for child in control.controls:
                result = find_in_controls(child)
                if result:
                    return result
        if hasattr(control, 'content'):
            return find_in_controls(control.content)
        return None

    return find_in_controls(view)


def test_wizard_tab_exists():
    """Test that setup wizard tab is visible."""
    # AIHubView accepts page=None for testing
    ai_hub = AIHubView(page=None)
    view = ai_hub.build()

    # Find tabs
    tabs = _find_tabs_control(view)
    assert tabs is not None, "Tabs control not found in view"

    # In Flet 0.80.1, tabs use 'label' instead of 'text'
    tab_labels = [tab.label for tab in tabs.content]

    assert "Setup" in tab_labels, f"Setup tab not found. Available tabs: {tab_labels}"
    assert "My Providers" in tab_labels, f"My Providers tab not found. Available tabs: {tab_labels}"
    assert "Model Library" in tab_labels, f"Model Library tab not found. Available tabs: {tab_labels}"
