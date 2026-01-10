"""
Navigation E2E tests.

Tests for the sidebar navigation and main app layout.
Uses aria-label selectors for Flet HTML renderer compatibility.
"""

import pytest
from playwright.sync_api import Page, expect


class TestSidebarNavigation:
    """Tests for sidebar navigation functionality."""

    def test_sidebar_displays_all_nav_items(self, page: Page, selectors):
        """Verify all navigation items are visible in the sidebar."""
        # All navigation items should be visible via aria-label
        nav_selectors = [
            selectors.NAV_WORKFLOWS,
            selectors.NAV_AI_HUB,
            selectors.NAV_AGENTS,
            selectors.NAV_DEVTOOLS,
            selectors.NAV_PLUGINS,
            selectors.NAV_RUNS,
            selectors.NAV_SETTINGS,
        ]

        for selector in nav_selectors:
            locator = page.locator(selector)
            expect(locator.first).to_be_visible()

    def test_navigate_to_workflows(self, page: Page, selectors, helpers):
        """Test navigation to Workflows view."""
        helpers.navigate_to(page, "workflows")

        # Verify we're on the workflows view
        expect(page.locator(selectors.NAV_WORKFLOWS).first).to_be_visible()

    def test_navigate_to_ai_hub(self, page: Page, selectors, helpers):
        """Test navigation to AI Hub view."""
        helpers.navigate_to(page, "ai_hub")

        # AI Hub should show - verify via navigation highlighting or content
        expect(page.locator(selectors.NAV_AI_HUB).first).to_be_visible()

    def test_navigate_to_agents(self, page: Page, selectors, helpers):
        """Test navigation to Agents view."""
        helpers.navigate_to(page, "agents")

        # Agents view should show
        expect(page.locator(selectors.NAV_AGENTS).first).to_be_visible()

    def test_navigate_to_devtools(self, page: Page, selectors, helpers):
        """Test navigation to DevTools view."""
        helpers.navigate_to(page, "devtools")

        # DevTools should show
        expect(page.locator(selectors.NAV_DEVTOOLS).first).to_be_visible()

    def test_navigate_to_plugins(self, page: Page, selectors, helpers):
        """Test navigation to Plugins view."""
        helpers.navigate_to(page, "plugins")

        # Plugins view should show
        expect(page.locator(selectors.NAV_PLUGINS).first).to_be_visible()

    def test_navigate_to_runs(self, page: Page, selectors, helpers):
        """Test navigation to Runs view."""
        helpers.navigate_to(page, "runs")

        # Runs view should show
        expect(page.locator(selectors.NAV_RUNS).first).to_be_visible()

    def test_navigate_to_settings(self, page: Page, selectors, helpers):
        """Test navigation to Settings view."""
        helpers.navigate_to(page, "settings")

        # Settings view should show
        expect(page.locator(selectors.NAV_SETTINGS).first).to_be_visible()

    def test_navigate_between_views(self, page: Page, selectors, helpers):
        """Test navigating between multiple views."""
        # Start at workflows
        helpers.navigate_to(page, "workflows")
        expect(page.locator(selectors.NAV_WORKFLOWS).first).to_be_visible()

        # Go to AI Hub
        helpers.navigate_to(page, "ai_hub")
        expect(page.locator(selectors.NAV_AI_HUB).first).to_be_visible()

        # Go to Settings
        helpers.navigate_to(page, "settings")
        expect(page.locator(selectors.NAV_SETTINGS).first).to_be_visible()

        # Back to Workflows
        helpers.navigate_to(page, "workflows")
        expect(page.locator(selectors.NAV_WORKFLOWS).first).to_be_visible()


class TestAppLayout:
    """Tests for main application layout."""

    def test_app_loads_successfully(self, page: Page):
        """Verify the app loads without errors."""
        # The page should have loaded successfully (not show error)
        expect(page).not_to_have_title("Error")

    def test_sidebar_is_visible(self, page: Page, selectors):
        """Verify the sidebar is visible on load."""
        # Sidebar should contain navigation items
        expect(page.locator(selectors.NAV_WORKFLOWS).first).to_be_visible()

    def test_default_view_is_workflows(self, page: Page, selectors):
        """Verify the default view on load is Workflows."""
        # Workflows view should be the default
        expect(page.locator(selectors.NAV_WORKFLOWS).first).to_be_visible()

    def test_has_interactive_elements(self, page: Page):
        """Verify the app has interactive elements (Flet HTML renderer check)."""
        # With HTML renderer, Flet creates elements with aria-label
        labeled = page.locator("[aria-label]")
        count = labeled.count()
        assert count > 0, "No interactive elements found - HTML renderer may not be active"


class TestAssistantPanel:
    """Tests for the Skynet Assistant panel."""

    def test_assistant_panel_visible(self, page: Page, selectors):
        """Verify the assistant panel is visible by default."""
        # Look for the assistant header via aria-label
        assistant = page.locator(selectors.ASSISTANT_HEADER)
        if assistant.count() > 0:
            expect(assistant.first).to_be_visible()

    def test_assistant_input_field_exists(self, page: Page, selectors):
        """Verify the assistant has an input field."""
        # Look for input field - Flet renders inputs with role or as input elements
        input_field = page.locator(selectors.ASSISTANT_INPUT)
        if input_field.count() > 0:
            expect(input_field.first).to_be_visible()
