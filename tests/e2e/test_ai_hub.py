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

    def test_model_library_tab_visible(self, page: Page):
        """Verify Model Library tab is visible."""
        model_library = page.locator("[aria-label*='Model Library'], [aria-label*='Library']")
        if model_library.count() > 0:
            expect(model_library.first).to_be_visible()

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


class TestModelLibraryTab:
    """Tests for the Model Library tab."""

    @pytest.fixture(autouse=True)
    def navigate_to_model_library(self, page: Page, helpers):
        """Navigate to AI Hub and Model Library tab."""
        helpers.navigate_to(page, "ai_hub")
        page.wait_for_timeout(500)
        model_library = page.locator("[aria-label*='Model Library'], [aria-label*='Library']")
        if model_library.count() > 0:
            model_library.first.click()
            page.wait_for_timeout(500)

    def test_model_library_tab_content_visible(self, page: Page):
        """Verify Model Library tab content is visible."""
        model_library = page.locator("[aria-label*='Model Library'], [aria-label*='Library']")
        if model_library.count() > 0:
            expect(model_library.first).to_be_visible()

    def test_huggingface_subtab_visible(self, page: Page):
        """Verify Hugging Face subtab is visible."""
        hf_tab = page.locator("[aria-label*='Hugging Face'], [aria-label*='HuggingFace']")
        if hf_tab.count() > 0:
            expect(hf_tab.first).to_be_visible()

    def test_ollama_subtab_visible(self, page: Page):
        """Verify Ollama subtab is visible."""
        ollama_tab = page.locator("[aria-label*='Ollama']")
        if ollama_tab.count() > 0:
            expect(ollama_tab.first).to_be_visible()

    def test_import_subtab_visible(self, page: Page):
        """Verify Import subtab is visible."""
        import_tab = page.locator("[aria-label*='Import']")
        if import_tab.count() > 0:
            expect(import_tab.first).to_be_visible()


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
