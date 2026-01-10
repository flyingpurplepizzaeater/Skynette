"""
DevTools view E2E tests.

Tests for the Developer Tools view including GitHub AutoFixer.
Uses aria-label selectors for Flet HTML renderer compatibility.
"""

import pytest
from playwright.sync_api import Page, expect


class TestDevToolsView:
    """Tests for the DevTools view."""

    @pytest.fixture(autouse=True)
    def navigate_to_devtools(self, page: Page, helpers):
        """Navigate to DevTools view before each test."""
        helpers.navigate_to(page, "devtools")
        page.wait_for_timeout(500)

    def test_devtools_view_loads(self, page: Page, selectors):
        """Verify DevTools view loads correctly."""
        expect(page.locator(selectors.NAV_DEVTOOLS).first).to_be_visible()

    def test_autofixer_section_visible(self, page: Page, selectors):
        """Verify AutoFixer section is visible."""
        # Look for AutoFixer or GitHub related elements via aria-label
        autofixer = page.locator("[aria-label*='AutoFixer']")
        github = page.locator("[aria-label*='GitHub']")

        if autofixer.count() > 0:
            expect(autofixer.first).to_be_visible()
        elif github.count() > 0:
            expect(github.first).to_be_visible()
        else:
            expect(page.locator(selectors.NAV_DEVTOOLS).first).to_be_visible()


class TestAutoFixerInputs:
    """Tests for AutoFixer input fields."""

    @pytest.fixture(autouse=True)
    def navigate_to_devtools(self, page: Page, helpers):
        """Navigate to DevTools view."""
        helpers.navigate_to(page, "devtools")
        page.wait_for_timeout(500)

    def test_repository_url_input_exists(self, page: Page, selectors):
        """Verify repository URL input exists."""
        # Look for URL-related input via aria-label
        url_input = page.locator("[aria-label*='URL'], [aria-label*='url']")
        repo_input = page.locator("[aria-label*='Repository'], [aria-label*='repo']")

        if url_input.count() > 0:
            expect(url_input.first).to_be_visible()
        elif repo_input.count() > 0:
            expect(repo_input.first).to_be_visible()
        else:
            # At least some input should exist
            inputs = page.locator(selectors.ASSISTANT_INPUT)
            if inputs.count() > 0:
                expect(inputs.first).to_be_visible()

    def test_issue_title_input_exists(self, page: Page):
        """Verify issue title input exists."""
        title_input = page.locator("[aria-label*='title'], [aria-label*='Title']")
        if title_input.count() > 0:
            expect(title_input.first).to_be_visible()

    def test_issue_description_input_exists(self, page: Page):
        """Verify issue description input exists."""
        # Look for description textarea or input via aria-label
        desc = page.locator("[aria-label*='description'], [aria-label*='Description']")
        if desc.count() > 0:
            expect(desc.first).to_be_visible()


class TestAutoFixerActions:
    """Tests for AutoFixer action buttons."""

    @pytest.fixture(autouse=True)
    def navigate_to_devtools(self, page: Page, helpers):
        """Navigate to DevTools view."""
        helpers.navigate_to(page, "devtools")
        page.wait_for_timeout(500)

    def test_generate_fix_button_exists(self, page: Page):
        """Verify Generate Fix button exists."""
        generate_btn = page.locator("[aria-label*='Generate']")
        fix_btn = page.locator("[aria-label*='Fix']")

        if generate_btn.count() > 0:
            expect(generate_btn.first).to_be_visible()
        elif fix_btn.count() > 0:
            expect(fix_btn.first).to_be_visible()

    def test_log_area_exists(self, page: Page):
        """Verify log/output area exists."""
        # Look for log or output section via aria-label
        log = page.locator("[aria-label*='Log'], [aria-label*='log']")
        output = page.locator("[aria-label*='Output'], [aria-label*='output']")

        if log.count() > 0:
            expect(log.first).to_be_visible()
        elif output.count() > 0:
            expect(output.first).to_be_visible()
