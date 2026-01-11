"""Tests for Usage Dashboard view."""

import pytest
from playwright.sync_api import Page, expect


class TestUsageDashboard:
    """Tests for Usage Dashboard view."""

    @pytest.fixture(autouse=True)
    def navigate_to_ai_hub(self, page: Page, helpers):
        """Navigate to AI Hub before each test."""
        helpers.navigate_to(page, "ai_hub")
        page.wait_for_timeout(500)

    def test_usage_tab_exists_in_ai_hub(self, page: Page):
        """AI Hub should have a Usage tab."""
        # Already at AI Hub from fixture
        # Look for the Usage text - it should be visible as a tab
        usage_locator = page.get_by_text("Usage", exact=False)
        expect(usage_locator.first).to_be_visible(timeout=10000)

    def test_usage_dashboard_view_loads(self, page: Page):
        """Usage dashboard view should load successfully."""
        # Click on Usage tab
        usage_tab = page.locator(":has-text('Usage')").filter(has=page.locator("flt-semantics"))
        usage_tab.first.click()
        page.wait_for_timeout(500)
        expect(page.locator("text=Usage Dashboard")).to_be_visible(timeout=10000)
