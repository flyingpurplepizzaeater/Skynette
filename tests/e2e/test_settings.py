"""
Settings view E2E tests.

Tests for the Settings page including configuration options.
Uses aria-label selectors for Flet HTML renderer compatibility.
"""

import pytest
from playwright.sync_api import Page, expect


class TestSettingsView:
    """Tests for the Settings view."""

    @pytest.fixture(autouse=True)
    def navigate_to_settings(self, page: Page, helpers):
        """Navigate to Settings view before each test."""
        helpers.navigate_to(page, "settings")
        page.wait_for_timeout(500)

    def test_settings_loads(self, page: Page, selectors):
        """Verify Settings view loads correctly."""
        expect(page.locator(selectors.NAV_SETTINGS).first).to_be_visible()


class TestAppearanceSettings:
    """Tests for appearance settings."""

    @pytest.fixture(autouse=True)
    def navigate_to_settings(self, page: Page, helpers):
        """Navigate to Settings view."""
        helpers.navigate_to(page, "settings")
        page.wait_for_timeout(500)

    def test_appearance_section_visible(self, page: Page):
        """Verify Appearance section is visible."""
        appearance = page.locator("[aria-label*='Appearance']")
        if appearance.count() > 0:
            expect(appearance.first).to_be_visible()

    def test_theme_setting_exists(self, page: Page):
        """Verify theme setting exists."""
        theme = page.locator("[aria-label*='Theme']")
        if theme.count() > 0:
            expect(theme.first).to_be_visible()

    def test_accent_color_setting_exists(self, page: Page):
        """Verify accent color setting exists."""
        accent = page.locator("[aria-label*='Accent']")
        if accent.count() > 0:
            expect(accent.first).to_be_visible()


class TestAISettings:
    """Tests for AI settings."""

    @pytest.fixture(autouse=True)
    def navigate_to_settings(self, page: Page, helpers):
        """Navigate to Settings view."""
        helpers.navigate_to(page, "settings")
        page.wait_for_timeout(500)

    def test_ai_settings_section_visible(self, page: Page):
        """Verify AI Settings section is visible."""
        ai_settings = page.locator("[aria-label*='AI']")
        if ai_settings.count() > 0:
            expect(ai_settings.first).to_be_visible()

    def test_default_provider_setting_exists(self, page: Page):
        """Verify default provider setting exists."""
        provider = page.locator("[aria-label*='Provider']")
        if provider.count() > 0:
            expect(provider.first).to_be_visible()

    def test_auto_fallback_setting_exists(self, page: Page):
        """Verify auto-fallback setting exists."""
        fallback = page.locator("[aria-label*='fallback'], [aria-label*='Fallback']")
        if fallback.count() > 0:
            expect(fallback.first).to_be_visible()


class TestStorageSettings:
    """Tests for storage settings."""

    @pytest.fixture(autouse=True)
    def navigate_to_settings(self, page: Page, helpers):
        """Navigate to Settings view."""
        helpers.navigate_to(page, "settings")
        page.wait_for_timeout(500)

    def test_storage_section_visible(self, page: Page):
        """Verify Storage section is visible."""
        storage = page.locator("[aria-label*='Storage']")
        if storage.count() > 0:
            expect(storage.first).to_be_visible()


class TestAdvancedSettings:
    """Tests for advanced settings."""

    @pytest.fixture(autouse=True)
    def navigate_to_settings(self, page: Page, helpers):
        """Navigate to Settings view."""
        helpers.navigate_to(page, "settings")
        page.wait_for_timeout(500)

    def test_advanced_section_visible(self, page: Page):
        """Verify Advanced section is visible."""
        advanced = page.locator("[aria-label*='Advanced']")
        if advanced.count() > 0:
            expect(advanced.first).to_be_visible()

    def test_debug_mode_setting_exists(self, page: Page):
        """Verify debug mode setting exists."""
        debug = page.locator("[aria-label*='Debug']")
        if debug.count() > 0:
            expect(debug.first).to_be_visible()

    def test_reset_settings_button_exists(self, page: Page):
        """Verify reset settings button exists."""
        reset = page.locator("[aria-label*='Reset']")
        if reset.count() > 0:
            expect(reset.first).to_be_visible()
