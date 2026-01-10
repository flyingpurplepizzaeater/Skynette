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


def _find_controls_by_type(container, control_type):
    """Recursively find all controls of a specific type."""
    found = []

    if isinstance(container, control_type):
        found.append(container)

    if hasattr(container, 'controls'):
        for control in container.controls:
            found.extend(_find_controls_by_type(control, control_type))

    if hasattr(container, 'content'):
        if isinstance(container.content, list):
            for item in container.content:
                found.extend(_find_controls_by_type(item, control_type))
        elif container.content:
            found.extend(_find_controls_by_type(container.content, control_type))

    return found


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


def test_wizard_shows_provider_checkboxes(page: ft.Page = None):
    """Test wizard displays provider selection checkboxes."""
    ai_hub = AIHubView(page=page)
    wizard = ai_hub._build_wizard_tab()

    # Find checkboxes
    checkboxes = _find_controls_by_type(wizard, ft.Checkbox)
    checkbox_labels = [cb.label for cb in checkboxes]

    assert "OpenAI" in checkbox_labels
    assert "Anthropic" in checkbox_labels
    assert "Local Models" in checkbox_labels
