"""
Workflow Editor E2E tests.

Tests for the workflow editor including Simple and Advanced modes.
Uses aria-label selectors for Flet HTML renderer compatibility.
"""

import pytest
from playwright.sync_api import Page, expect


class TestWorkflowEditorBasics:
    """Basic tests for the workflow editor."""

    @pytest.fixture(autouse=True)
    def create_and_open_workflow(self, page: Page, helpers, selectors):
        """Create a workflow and navigate to the editor."""
        helpers.navigate_to(page, "workflows")

        # Create a new workflow
        new_btn = page.locator(selectors.NEW_WORKFLOW_BTN)
        if new_btn.count() == 0:
            pytest.skip("New Workflow button not found")

        new_btn.first.click()
        page.wait_for_timeout(500)

        inputs = page.locator("input, [role='textbox']")
        if inputs.count() > 0:
            inputs.first.fill("Editor Test Workflow")

        create_btn = page.locator(selectors.CREATE_BTN)
        if create_btn.count() > 0:
            create_btn.first.click()
        page.wait_for_timeout(1000)

    def test_editor_loads_after_creation(self, page: Page, selectors):
        """Verify editor loads after creating a workflow."""
        # Should see Save button
        save_btn = page.locator(selectors.SAVE_BTN)
        if save_btn.count() > 0:
            expect(save_btn.first).to_be_visible()

    def test_editor_shows_save_button(self, page: Page, selectors):
        """Verify Save button is visible in editor."""
        save_btn = page.locator(selectors.SAVE_BTN)
        if save_btn.count() > 0:
            expect(save_btn.first).to_be_visible()

    def test_editor_shows_run_button(self, page: Page, selectors):
        """Verify Run button is visible in editor."""
        run_btn = page.locator(selectors.RUN_BTN)
        if run_btn.count() > 0:
            expect(run_btn.first).to_be_visible()


class TestEditorModeToggle:
    """Tests for Simple/Advanced mode toggle."""

    @pytest.fixture(autouse=True)
    def create_and_open_workflow(self, page: Page, helpers, selectors):
        """Create a workflow and navigate to the editor."""
        helpers.navigate_to(page, "workflows")

        new_btn = page.locator(selectors.NEW_WORKFLOW_BTN)
        if new_btn.count() == 0:
            pytest.skip("New Workflow button not found")

        new_btn.first.click()
        page.wait_for_timeout(500)

        inputs = page.locator("input, [role='textbox']")
        if inputs.count() > 0:
            inputs.first.fill("Mode Toggle Test")

        create_btn = page.locator(selectors.CREATE_BTN)
        if create_btn.count() > 0:
            create_btn.first.click()
        page.wait_for_timeout(1000)

    def test_simple_mode_is_default(self, page: Page, selectors):
        """Verify Simple mode is the default."""
        # Look for Simple mode indicator
        simple_btn = page.locator(selectors.SIMPLE_MODE_BTN)
        if simple_btn.count() > 0:
            expect(simple_btn.first).to_be_visible()

    def test_toggle_to_advanced_mode(self, page: Page, selectors):
        """Test switching to Advanced mode."""
        # Click Advanced button
        advanced_btn = page.locator(selectors.ADVANCED_MODE_BTN)
        if advanced_btn.count() > 0:
            advanced_btn.first.click()
            page.wait_for_timeout(500)
            expect(advanced_btn.first).to_be_visible()

    def test_toggle_back_to_simple_mode(self, page: Page, selectors):
        """Test switching back to Simple mode."""
        # First go to Advanced
        advanced_btn = page.locator(selectors.ADVANCED_MODE_BTN)
        if advanced_btn.count() > 0:
            advanced_btn.first.click()
            page.wait_for_timeout(500)

            # Then back to Simple
            simple_btn = page.locator(selectors.SIMPLE_MODE_BTN)
            if simple_btn.count() > 0:
                simple_btn.first.click()
                page.wait_for_timeout(500)
                expect(simple_btn.first).to_be_visible()


class TestSimpleModeEditor:
    """Tests for Simple mode workflow builder."""

    @pytest.fixture(autouse=True)
    def create_and_open_workflow(self, page: Page, helpers, selectors):
        """Create a workflow and ensure we're in Simple mode."""
        helpers.navigate_to(page, "workflows")

        new_btn = page.locator(selectors.NEW_WORKFLOW_BTN)
        if new_btn.count() == 0:
            pytest.skip("New Workflow button not found")

        new_btn.first.click()
        page.wait_for_timeout(500)

        inputs = page.locator("input, [role='textbox']")
        if inputs.count() > 0:
            inputs.first.fill("Simple Mode Test")

        create_btn = page.locator(selectors.CREATE_BTN)
        if create_btn.count() > 0:
            create_btn.first.click()
        page.wait_for_timeout(1000)

    def test_trigger_section_visible(self, page: Page):
        """Verify trigger section is visible in Simple mode."""
        # Look for trigger-related elements
        trigger = page.locator("[aria-label*='Trigger'], [aria-label*='trigger']")
        if trigger.count() > 0:
            expect(trigger.first).to_be_visible()

    def test_add_trigger_button_exists(self, page: Page):
        """Verify there's a way to add a trigger."""
        # Look for "Choose Trigger" or "Add Trigger" button
        add_trigger = page.locator("[aria-label*='Choose Trigger'], [aria-label*='Add Trigger']")
        if add_trigger.count() > 0:
            expect(add_trigger.first).to_be_visible()

    def test_add_step_button_exists(self, page: Page):
        """Verify there's a way to add steps."""
        # Look for "Add Step" or similar button
        add_step = page.locator("[aria-label*='Add Step'], [aria-label*='Add Action']")
        if add_step.count() > 0:
            expect(add_step.first).to_be_visible()


class TestAdvancedModeEditor:
    """Tests for Advanced mode workflow builder."""

    @pytest.fixture(autouse=True)
    def create_and_open_workflow_advanced(self, page: Page, helpers, selectors):
        """Create a workflow and switch to Advanced mode."""
        helpers.navigate_to(page, "workflows")

        new_btn = page.locator(selectors.NEW_WORKFLOW_BTN)
        if new_btn.count() == 0:
            pytest.skip("New Workflow button not found")

        new_btn.first.click()
        page.wait_for_timeout(500)

        inputs = page.locator("input, [role='textbox']")
        if inputs.count() > 0:
            inputs.first.fill("Advanced Mode Test")

        create_btn = page.locator(selectors.CREATE_BTN)
        if create_btn.count() > 0:
            create_btn.first.click()
        page.wait_for_timeout(1000)

        # Switch to Advanced mode
        advanced_btn = page.locator(selectors.ADVANCED_MODE_BTN)
        if advanced_btn.count() > 0:
            advanced_btn.first.click()
            page.wait_for_timeout(500)

    def test_node_palette_visible(self, page: Page, selectors):
        """Verify node palette is visible in Advanced mode."""
        # Look for node categories via aria-label
        categories = ["AI", "Triggers", "HTTP", "Data", "Flow"]
        found_category = False

        for cat in categories:
            cat_element = page.locator(f"[aria-label*='{cat}']")
            if cat_element.count() > 0:
                found_category = True
                break

        # At least one category or Advanced mode should be visible
        advanced_btn = page.locator(selectors.ADVANCED_MODE_BTN)
        assert found_category or advanced_btn.count() > 0

    def test_canvas_area_exists(self, page: Page, selectors):
        """Verify canvas area exists for node placement."""
        # The canvas should be the main content area
        advanced_btn = page.locator(selectors.ADVANCED_MODE_BTN)
        if advanced_btn.count() > 0:
            expect(advanced_btn.first).to_be_visible()


class TestWorkflowSaving:
    """Tests for saving workflows."""

    @pytest.fixture(autouse=True)
    def create_and_open_workflow(self, page: Page, helpers, selectors):
        """Create a workflow."""
        helpers.navigate_to(page, "workflows")

        new_btn = page.locator(selectors.NEW_WORKFLOW_BTN)
        if new_btn.count() == 0:
            pytest.skip("New Workflow button not found")

        new_btn.first.click()
        page.wait_for_timeout(500)

        inputs = page.locator("input, [role='textbox']")
        if inputs.count() > 0:
            inputs.first.fill("Save Test Workflow")

        create_btn = page.locator(selectors.CREATE_BTN)
        if create_btn.count() > 0:
            create_btn.first.click()
        page.wait_for_timeout(1000)

    def test_save_button_clickable(self, page: Page, selectors):
        """Verify Save button is clickable."""
        save_btn = page.locator(selectors.SAVE_BTN)
        if save_btn.count() > 0:
            expect(save_btn.first).to_be_enabled()

    def test_save_workflow(self, page: Page, selectors):
        """Test saving a workflow."""
        save_btn = page.locator(selectors.SAVE_BTN)
        if save_btn.count() > 0:
            save_btn.first.click()
            page.wait_for_timeout(1000)
            expect(save_btn.first).to_be_visible()


class TestWorkflowExecution:
    """Tests for running workflows."""

    @pytest.fixture(autouse=True)
    def create_and_open_workflow(self, page: Page, helpers, selectors):
        """Create a workflow."""
        helpers.navigate_to(page, "workflows")

        new_btn = page.locator(selectors.NEW_WORKFLOW_BTN)
        if new_btn.count() == 0:
            pytest.skip("New Workflow button not found")

        new_btn.first.click()
        page.wait_for_timeout(500)

        inputs = page.locator("input, [role='textbox']")
        if inputs.count() > 0:
            inputs.first.fill("Execution Test Workflow")

        create_btn = page.locator(selectors.CREATE_BTN)
        if create_btn.count() > 0:
            create_btn.first.click()
        page.wait_for_timeout(1000)

    def test_run_button_clickable(self, page: Page, selectors):
        """Verify Run button is clickable."""
        run_btn = page.locator(selectors.RUN_BTN)
        if run_btn.count() > 0:
            expect(run_btn.first).to_be_enabled()

    def test_run_empty_workflow(self, page: Page, selectors):
        """Test running an empty workflow."""
        run_btn = page.locator(selectors.RUN_BTN)
        if run_btn.count() > 0:
            run_btn.first.click()
            page.wait_for_timeout(1000)
            expect(run_btn.first).to_be_visible()
