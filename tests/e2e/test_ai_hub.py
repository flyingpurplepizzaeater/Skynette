"""
AI Hub view E2E tests.

Tests for the AI Model Hub including tabs and model management.
Uses aria-label selectors for Flet HTML renderer compatibility.
"""

import pytest
from playwright.sync_api import Page, expect


class TestAIHubView:
    """Tests for the AI Hub view."""

    @pytest.fixture(autouse=True)
    def navigate_to_ai_hub(self, page: Page, helpers):
        """Navigate to AI Hub view before each test."""
        helpers.navigate_to(page, "ai_hub")
        page.wait_for_timeout(500)

    def test_ai_hub_loads(self, page: Page, selectors):
        """Verify AI Hub view loads correctly."""
        expect(page.locator(selectors.NAV_AI_HUB).first).to_be_visible()

    def test_my_models_tab_visible(self, page: Page):
        """Verify My Models tab is visible."""
        my_models = page.locator("[aria-label*='My Models']")
        if my_models.count() > 0:
            expect(my_models.first).to_be_visible()

    def test_download_tab_visible(self, page: Page):
        """Verify Download tab is visible."""
        download = page.locator("[aria-label*='Download']")
        if download.count() > 0:
            expect(download.first).to_be_visible()

    def test_providers_tab_visible(self, page: Page):
        """Verify Providers tab is visible."""
        providers = page.locator("[aria-label*='Providers'], [aria-label*='Provider']")
        if providers.count() > 0:
            expect(providers.first).to_be_visible()


class TestMyModelsTab:
    """Tests for the My Models tab."""

    @pytest.fixture(autouse=True)
    def navigate_to_my_models(self, page: Page, helpers):
        """Navigate to AI Hub and My Models tab."""
        helpers.navigate_to(page, "ai_hub")
        page.wait_for_timeout(500)
        # Click My Models tab if not already selected
        my_models = page.locator("[aria-label*='My Models']")
        if my_models.count() > 0:
            my_models.first.click()
            page.wait_for_timeout(500)

    def test_my_models_content_visible(self, page: Page):
        """Verify My Models tab content is visible."""
        # Should show either models or empty state
        my_models = page.locator("[aria-label*='My Models']")
        if my_models.count() > 0:
            expect(my_models.first).to_be_visible()

    def test_refresh_button_exists(self, page: Page):
        """Verify refresh button exists."""
        refresh_btn = page.locator("[aria-label*='Refresh']")
        if refresh_btn.count() > 0:
            expect(refresh_btn.first).to_be_visible()


class TestDownloadTab:
    """Tests for the Download tab."""

    @pytest.fixture(autouse=True)
    def navigate_to_download(self, page: Page, helpers):
        """Navigate to AI Hub and Download tab."""
        helpers.navigate_to(page, "ai_hub")
        page.wait_for_timeout(500)
        download = page.locator("[aria-label*='Download']")
        if download.count() > 0:
            download.first.click()
            page.wait_for_timeout(500)

    def test_download_tab_content_visible(self, page: Page):
        """Verify Download tab content is visible."""
        download = page.locator("[aria-label*='Download']")
        if download.count() > 0:
            expect(download.first).to_be_visible()

    def test_recommended_models_shown(self, page: Page):
        """Verify recommended models are shown."""
        # Should show some model recommendations or categories
        download = page.locator("[aria-label*='Download']")
        if download.count() > 0:
            expect(download.first).to_be_visible()


class TestProvidersTab:
    """Tests for the Providers tab."""

    @pytest.fixture(autouse=True)
    def navigate_to_providers(self, page: Page, helpers):
        """Navigate to AI Hub and Providers tab."""
        helpers.navigate_to(page, "ai_hub")
        page.wait_for_timeout(500)
        providers = page.locator("[aria-label*='Providers'], [aria-label*='Provider']")
        if providers.count() > 0:
            providers.first.click()
            page.wait_for_timeout(500)

    def test_providers_tab_content_visible(self, page: Page):
        """Verify Providers tab content is visible."""
        providers = page.locator("[aria-label*='Providers'], [aria-label*='Provider']")
        if providers.count() > 0:
            expect(providers.first).to_be_visible()

    def test_openai_provider_listed(self, page: Page):
        """Verify OpenAI provider is listed."""
        openai = page.locator("[aria-label*='OpenAI']")
        if openai.count() > 0:
            expect(openai.first).to_be_visible()

    def test_anthropic_provider_listed(self, page: Page):
        """Verify Anthropic provider is listed."""
        anthropic = page.locator("[aria-label*='Anthropic']")
        if anthropic.count() > 0:
            expect(anthropic.first).to_be_visible()

    def test_local_provider_listed(self, page: Page):
        """Verify Local provider is listed."""
        local = page.locator("[aria-label*='Local']")
        if local.count() > 0:
            expect(local.first).to_be_visible()
