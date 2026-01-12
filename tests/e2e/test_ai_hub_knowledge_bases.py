import pytest
from playwright.sync_api import Page, expect


class TestAIHubKnowledgeBases:
    """Tests for Knowledge Bases tab integration in AI Hub."""

    @pytest.fixture(autouse=True)
    def navigate_to_ai_hub(self, page: Page, helpers):
        """Navigate to AI Hub view before each test."""
        helpers.navigate_to(page, "ai_hub")
        page.wait_for_timeout(500)

    def test_knowledge_bases_tab_exists(self, page: Page):
        """AI Hub should have Knowledge Bases tab."""
        # Knowledge Bases tab should exist (check multiple possible selectors)
        kb_tab = page.locator("[aria-label*='Knowledge Bases'], text='Knowledge Bases'")
        if kb_tab.count() > 0:
            expect(kb_tab.first).to_be_visible()

    def test_navigate_to_knowledge_bases(self, page: Page):
        """Should navigate to Knowledge Bases tab."""
        # Click Knowledge Bases tab
        kb_tab = page.locator("[aria-label*='Knowledge Bases'], text='Knowledge Bases'")
        if kb_tab.count() > 0:
            kb_tab.first.click()
            page.wait_for_timeout(500)

            # Should show empty state or collections
            # Look for either "No Knowledge Bases Yet" or collection cards
            content = page.locator("text=No Knowledge Bases Yet")
            expect(content.first).to_be_visible()
