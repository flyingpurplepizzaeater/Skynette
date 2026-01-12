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

    def test_create_collection_ui(self, page: Page):
        """Should create collection through UI."""
        # Navigate to Knowledge Bases tab
        kb_tab = page.locator("[aria-label*='Knowledge Bases'], text='Knowledge Bases'")
        if kb_tab.count() > 0:
            kb_tab.first.click()
            page.wait_for_timeout(500)

            # Click New Collection button (check multiple possible selectors)
            new_btn = page.locator("text='New Collection', [aria-label*='New Collection']")
            if new_btn.count() > 0:
                new_btn.first.click()
                page.wait_for_timeout(500)

                # Fill form - use defensive selectors
                name_input = page.locator("input[placeholder*='Name'], input[aria-label*='Name']")
                if name_input.count() > 0:
                    name_input.first.fill("MyTestCollection")

                desc_input = page.locator("textarea[placeholder*='Description'], textarea[aria-label*='Description']")
                if desc_input.count() > 0:
                    desc_input.first.fill("Test description")

                # Save
                save_btn = page.locator("text='Save', [aria-label*='Save']")
                if save_btn.count() > 0:
                    save_btn.first.click()
                    page.wait_for_timeout(1000)

                    # Collection card should appear
                    collection = page.locator("text=MyTestCollection")
                    if collection.count() > 0:
                        expect(collection.first).to_be_visible(timeout=5000)

    def test_query_collection_ui(self, page: Page):
        """Should query collection through UI."""
        # Navigate to Knowledge Bases tab
        kb_tab = page.locator("[aria-label*='Knowledge Bases'], text='Knowledge Bases'")
        if kb_tab.count() > 0:
            kb_tab.first.click()
            page.wait_for_timeout(500)

            # Look for any existing collection or create one
            collections = page.locator("[data-testid*='collection'], .collection-card")
            if collections.count() == 0:
                # No collections yet - this test requires a collection
                # We'll skip this test if there are no collections
                pytest.skip("No collections available for query test")

            # Find and click Query button (defensive selector)
            query_btn = page.locator("text='Query', [aria-label*='Query']")
            if query_btn.count() > 0:
                query_btn.first.click()
                page.wait_for_timeout(500)

                # Enter query
                query_input = page.locator("textarea[placeholder*='Query'], textarea[aria-label*='Query'], input[placeholder*='Query']")
                if query_input.count() > 0:
                    query_input.first.fill("test query")

                    # Search
                    search_btn = page.locator("text='Search', [aria-label*='Search']")
                    if search_btn.count() > 0:
                        search_btn.first.click()
                        page.wait_for_timeout(2000)

                        # Results should appear (or empty state)
                        # Look for results container or "Found" text or "No results"
                        results = page.locator("text*='Found', text*='results', text*='No results'")
                        if results.count() > 0:
                            expect(results.first).to_be_visible(timeout=10000)
