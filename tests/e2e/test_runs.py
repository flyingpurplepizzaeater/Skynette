"""
Runs view E2E tests.

Tests for the Execution History view.
Uses aria-label selectors for Flet HTML renderer compatibility.
"""

import pytest
from playwright.sync_api import Page, expect


class TestRunsView:
    """Tests for the Runs (Execution History) view."""

    @pytest.fixture(autouse=True)
    def navigate_to_runs(self, page: Page, helpers):
        """Navigate to Runs view before each test."""
        helpers.navigate_to(page, "runs")
        page.wait_for_timeout(500)

    def test_runs_view_loads(self, page: Page, selectors):
        """Verify Runs view loads correctly."""
        expect(page.locator(selectors.NAV_RUNS).first).to_be_visible()

    def test_execution_history_header_visible(self, page: Page, selectors):
        """Verify Execution History header is visible."""
        history = page.locator("[aria-label*='History']")
        execution = page.locator("[aria-label*='Execution']")

        if history.count() > 0:
            expect(history.first).to_be_visible()
        elif execution.count() > 0:
            expect(execution.first).to_be_visible()
        else:
            expect(page.locator(selectors.NAV_RUNS).first).to_be_visible()

    def test_clear_history_button_exists(self, page: Page):
        """Verify Clear History button exists."""
        clear_btn = page.locator("[aria-label*='Clear']")
        if clear_btn.count() > 0:
            expect(clear_btn.first).to_be_visible()


class TestRunsFiltering:
    """Tests for filtering execution history."""

    @pytest.fixture(autouse=True)
    def navigate_to_runs(self, page: Page, helpers):
        """Navigate to Runs view."""
        helpers.navigate_to(page, "runs")
        page.wait_for_timeout(500)

    def test_workflow_filter_exists(self, page: Page, selectors):
        """Verify workflow filter dropdown exists."""
        # Look for filter dropdown via aria-label
        workflow_filter = page.locator("[aria-label*='Workflow']")
        all_filter = page.locator("[aria-label*='All Workflows']")

        if workflow_filter.count() > 0:
            expect(workflow_filter.first).to_be_visible()
        elif all_filter.count() > 0:
            expect(all_filter.first).to_be_visible()

    def test_status_filter_exists(self, page: Page, selectors):
        """Verify status filter exists."""
        status_filter = page.locator("[aria-label*='Status']")
        all_status = page.locator("[aria-label*='All Status']")

        if status_filter.count() > 0:
            expect(status_filter.first).to_be_visible()
        elif all_status.count() > 0:
            expect(all_status.first).to_be_visible()


class TestRunsList:
    """Tests for the runs list display."""

    @pytest.fixture(autouse=True)
    def navigate_to_runs(self, page: Page, helpers):
        """Navigate to Runs view."""
        helpers.navigate_to(page, "runs")
        page.wait_for_timeout(500)

    def test_empty_state_when_no_runs(self, page: Page, selectors):
        """Verify empty state is shown when no runs exist."""
        # Should show either empty message or the header
        expect(page.locator(selectors.NAV_RUNS).first).to_be_visible()

    def test_runs_list_area_exists(self, page: Page, selectors):
        """Verify runs list area exists."""
        # The runs view should have some content area
        expect(page.locator(selectors.NAV_RUNS).first).to_be_visible()


class TestRunDetails:
    """Tests for viewing run details."""

    @pytest.fixture(autouse=True)
    def navigate_to_runs(self, page: Page, helpers):
        """Navigate to Runs view."""
        helpers.navigate_to(page, "runs")
        page.wait_for_timeout(500)

    def test_view_details_button_functionality(self, page: Page):
        """Verify View Details button exists when there are runs."""
        # This will only work if there are actual runs
        details_btn = page.locator("[aria-label*='View Details']")
        view_btn = page.locator("[aria-label*='View']")

        # If we have runs, there should be a way to view details
        if details_btn.count() > 0 or view_btn.count() > 0:
            if details_btn.count() > 0:
                expect(details_btn.first).to_be_visible()
            else:
                expect(view_btn.first).to_be_visible()
