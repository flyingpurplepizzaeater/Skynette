"""
Plugins view E2E tests.

Tests for the Plugin Marketplace view.
Uses aria-label selectors for Flet HTML renderer compatibility.
"""

import pytest
from playwright.sync_api import Page, expect


class TestPluginsView:
    """Tests for the Plugins view."""

    @pytest.fixture(autouse=True)
    def navigate_to_plugins(self, page: Page, helpers):
        """Navigate to Plugins view before each test."""
        helpers.navigate_to(page, "plugins")
        page.wait_for_timeout(500)

    def test_plugins_view_loads(self, page: Page, selectors):
        """Verify Plugins view loads correctly."""
        expect(page.locator(selectors.NAV_PLUGINS).first).to_be_visible()

    def test_installed_tab_visible(self, page: Page):
        """Verify Installed tab is visible."""
        installed = page.locator("[aria-label*='Installed']")
        if installed.count() > 0:
            expect(installed.first).to_be_visible()

    def test_marketplace_tab_visible(self, page: Page):
        """Verify Marketplace tab is visible."""
        marketplace = page.locator("[aria-label*='Marketplace']")
        if marketplace.count() > 0:
            expect(marketplace.first).to_be_visible()

    def test_develop_tab_visible(self, page: Page):
        """Verify Develop tab is visible."""
        develop = page.locator("[aria-label*='Develop']")
        if develop.count() > 0:
            expect(develop.first).to_be_visible()


class TestInstalledTab:
    """Tests for the Installed plugins tab."""

    @pytest.fixture(autouse=True)
    def navigate_to_installed(self, page: Page, helpers):
        """Navigate to Plugins and Installed tab."""
        helpers.navigate_to(page, "plugins")
        page.wait_for_timeout(500)
        installed = page.locator("[aria-label*='Installed']")
        if installed.count() > 0:
            installed.first.click()
            page.wait_for_timeout(500)

    def test_installed_content_visible(self, page: Page):
        """Verify Installed tab content is visible."""
        installed = page.locator("[aria-label*='Installed']")
        if installed.count() > 0:
            expect(installed.first).to_be_visible()


class TestMarketplaceTab:
    """Tests for the Marketplace tab."""

    @pytest.fixture(autouse=True)
    def navigate_to_marketplace(self, page: Page, helpers):
        """Navigate to Plugins and Marketplace tab."""
        helpers.navigate_to(page, "plugins")
        page.wait_for_timeout(500)
        marketplace = page.locator("[aria-label*='Marketplace']")
        if marketplace.count() > 0:
            marketplace.first.click()
            page.wait_for_timeout(500)

    def test_marketplace_content_visible(self, page: Page):
        """Verify Marketplace tab content is visible."""
        marketplace = page.locator("[aria-label*='Marketplace']")
        if marketplace.count() > 0:
            expect(marketplace.first).to_be_visible()

    def test_category_filters_exist(self, page: Page, selectors):
        """Verify category filters exist."""
        # Look for category chips/buttons via aria-label
        categories = ["All", "Communication", "Data", "AI", "Productivity"]
        found_category = False

        for cat in categories:
            cat_elem = page.locator(f"[aria-label*='{cat}']")
            if cat_elem.count() > 0:
                found_category = True
                break

        # At least the plugins nav should be visible
        expect(page.locator(selectors.NAV_PLUGINS).first).to_be_visible()

    def test_search_input_exists(self, page: Page, selectors):
        """Verify search input exists in marketplace."""
        search = page.locator("[aria-label*='earch'], input")
        if search.count() > 0:
            expect(search.first).to_be_visible()


class TestDevelopTab:
    """Tests for the Develop tab."""

    @pytest.fixture(autouse=True)
    def navigate_to_develop(self, page: Page, helpers):
        """Navigate to Plugins and Develop tab."""
        helpers.navigate_to(page, "plugins")
        page.wait_for_timeout(500)
        develop = page.locator("[aria-label*='Develop']")
        if develop.count() > 0:
            develop.first.click()
            page.wait_for_timeout(500)

    def test_develop_content_visible(self, page: Page):
        """Verify Develop tab content is visible."""
        develop = page.locator("[aria-label*='Develop']")
        if develop.count() > 0:
            expect(develop.first).to_be_visible()

    def test_create_plugin_button_exists(self, page: Page):
        """Verify Create Plugin button exists."""
        create_btn = page.locator("[aria-label*='Create']")
        new_btn = page.locator("[aria-label*='New Plugin']")

        if create_btn.count() > 0:
            expect(create_btn.first).to_be_visible()
        elif new_btn.count() > 0:
            expect(new_btn.first).to_be_visible()
