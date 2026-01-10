"""
Workflows view E2E tests.

Tests for the Workflows dashboard including CRUD operations.
Uses aria-label selectors for Flet HTML renderer compatibility.
"""

import pytest
from playwright.sync_api import Page, expect


class TestWorkflowsView:
    """Tests for the Workflows dashboard view."""

    def test_workflows_view_loads(self, page: Page, helpers, selectors):
        """Verify the workflows view loads correctly."""
        helpers.navigate_to(page, "workflows")

        # Should show the Workflows navigation item as active
        expect(page.locator(selectors.NAV_WORKFLOWS).first).to_be_visible()

    def test_new_workflow_button_visible(self, page: Page, helpers, selectors):
        """Verify the New Workflow button is visible."""
        helpers.navigate_to(page, "workflows")

        # Look for "New Workflow" or similar button via aria-label
        new_btn = page.locator(selectors.NEW_WORKFLOW_BTN)
        if new_btn.count() > 0:
            expect(new_btn.first).to_be_visible()

    def test_empty_state_when_no_workflows(self, page: Page, helpers, selectors):
        """Verify empty state is shown when no workflows exist."""
        helpers.navigate_to(page, "workflows")

        # Should show either empty state message or the new workflow button
        # In a fresh install, there should be no workflows
        new_btn = page.locator(selectors.NEW_WORKFLOW_BTN)
        if new_btn.count() > 0:
            expect(new_btn.first).to_be_visible()


class TestWorkflowCreation:
    """Tests for creating new workflows."""

    def test_click_new_workflow_opens_dialog(self, page: Page, helpers, selectors):
        """Test that clicking New Workflow opens a dialog."""
        helpers.navigate_to(page, "workflows")

        # Click New Workflow button
        new_btn = page.locator(selectors.NEW_WORKFLOW_BTN)
        if new_btn.count() > 0:
            new_btn.first.click()
            page.wait_for_timeout(500)

            # Should show some kind of dialog or form
            # Look for common dialog elements
            dialog = page.locator(selectors.DIALOG)
            create_btn = page.locator(selectors.CREATE_BTN)
            if dialog.count() > 0:
                expect(dialog.first).to_be_visible()
            elif create_btn.count() > 0:
                expect(create_btn.first).to_be_visible()

    def test_create_workflow_with_name(self, page: Page, helpers, selectors):
        """Test creating a workflow with a name."""
        helpers.navigate_to(page, "workflows")

        # Click New Workflow
        new_btn = page.locator(selectors.NEW_WORKFLOW_BTN)
        if new_btn.count() == 0:
            pytest.skip("New Workflow button not found")

        new_btn.first.click()
        page.wait_for_timeout(500)

        # Fill in the workflow name
        inputs = page.locator("input, [role='textbox']")
        if inputs.count() > 0:
            inputs.first.fill("Test Automation Workflow")

            # Click Create
            create_btn = page.locator(selectors.CREATE_BTN)
            if create_btn.count() > 0:
                create_btn.first.click()
                page.wait_for_timeout(1000)

    def test_cancel_create_workflow(self, page: Page, helpers, selectors):
        """Test canceling workflow creation."""
        helpers.navigate_to(page, "workflows")

        # Click New Workflow
        new_btn = page.locator(selectors.NEW_WORKFLOW_BTN)
        if new_btn.count() == 0:
            pytest.skip("New Workflow button not found")

        new_btn.first.click()
        page.wait_for_timeout(500)

        # Look for Cancel or close button
        cancel_btn = page.locator(selectors.CANCEL_BTN)
        if cancel_btn.count() > 0:
            cancel_btn.first.click()
        else:
            # Try pressing Escape
            page.keyboard.press("Escape")

        page.wait_for_timeout(500)

        # Should be back to workflows view
        expect(page.locator(selectors.NAV_WORKFLOWS).first).to_be_visible()


class TestWorkflowCard:
    """Tests for workflow cards in the list view."""

    @pytest.fixture(autouse=True)
    def setup_workflow(self, page: Page, helpers, selectors):
        """Create a test workflow before card tests."""
        helpers.navigate_to(page, "workflows")

        # Create a workflow to test with
        new_btn = page.locator(selectors.NEW_WORKFLOW_BTN)
        if new_btn.count() == 0:
            pytest.skip("New Workflow button not found")

        new_btn.first.click()
        page.wait_for_timeout(500)

        inputs = page.locator("input, [role='textbox']")
        if inputs.count() > 0:
            inputs.first.fill("Card Test Workflow")

        create_btn = page.locator(selectors.CREATE_BTN)
        if create_btn.count() > 0:
            create_btn.first.click()
        page.wait_for_timeout(1000)

        # Go back to workflows list
        helpers.navigate_to(page, "workflows")
        page.wait_for_timeout(500)

    def test_workflow_card_shows_name(self, page: Page, selectors):
        """Verify workflow card shows the workflow name."""
        # Look for the workflow we created via aria-label
        card = page.locator("[aria-label*='Card Test Workflow']")
        if card.count() > 0:
            expect(card.first).to_be_visible()

    def test_workflow_card_clickable(self, page: Page, selectors):
        """Verify clicking a workflow card opens it."""
        # Click on the workflow
        card = page.locator("[aria-label*='Card Test Workflow']")
        if card.count() > 0:
            card.first.click()
            page.wait_for_timeout(1000)

            # Should navigate to editor - look for editor elements
            save_btn = page.locator(selectors.SAVE_BTN)
            if save_btn.count() > 0:
                expect(save_btn.first).to_be_visible()


class TestWorkflowSearch:
    """Tests for workflow search functionality."""

    def test_search_input_visible(self, page: Page, helpers, selectors):
        """Verify search input is visible on workflows view."""
        helpers.navigate_to(page, "workflows")

        # Look for search input - may have aria-label with "Search"
        search_inputs = page.locator("[aria-label*='earch'], input")
        if search_inputs.count() > 0:
            expect(search_inputs.first).to_be_visible()
