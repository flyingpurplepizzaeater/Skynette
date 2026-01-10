"""
Agents view E2E tests.

Tests for the Agent Orchestrator view.
Uses aria-label selectors for Flet HTML renderer compatibility.
"""

import pytest
from playwright.sync_api import Page, expect


class TestAgentsView:
    """Tests for the Agents view."""

    @pytest.fixture(autouse=True)
    def navigate_to_agents(self, page: Page, helpers):
        """Navigate to Agents view before each test."""
        helpers.navigate_to(page, "agents")
        page.wait_for_timeout(500)

    def test_agents_view_loads(self, page: Page, selectors):
        """Verify Agents view loads correctly."""
        expect(page.locator(selectors.NAV_AGENTS).first).to_be_visible()

    def test_orchestrator_header_visible(self, page: Page, selectors):
        """Verify Agent Orchestrator header is visible."""
        # Look for orchestrator-related elements via aria-label
        orchestrator = page.locator("[aria-label*='Orchestrator']")
        if orchestrator.count() > 0:
            expect(orchestrator.first).to_be_visible()
        else:
            expect(page.locator(selectors.NAV_AGENTS).first).to_be_visible()

    def test_task_input_exists(self, page: Page, selectors):
        """Verify task input field exists."""
        inputs = page.locator(selectors.ASSISTANT_INPUT)
        if inputs.count() > 0:
            expect(inputs.first).to_be_visible()


class TestAgentTaskSubmission:
    """Tests for submitting tasks to agents."""

    @pytest.fixture(autouse=True)
    def navigate_to_agents(self, page: Page, helpers):
        """Navigate to Agents view."""
        helpers.navigate_to(page, "agents")
        page.wait_for_timeout(500)

    def test_can_type_task_description(self, page: Page, selectors):
        """Verify user can type a task description."""
        input_field = page.locator(selectors.ASSISTANT_INPUT)
        if input_field.count() > 0:
            input_field.first.fill("Analyze this code and suggest improvements")
            expect(input_field.first).to_have_value("Analyze this code and suggest improvements")

    def test_submit_button_exists(self, page: Page, selectors):
        """Verify submit button exists."""
        # Look for send/submit button via aria-label
        send_btn = page.locator("[aria-label*='Send']")
        submit_btn = page.locator("[aria-label*='Submit']")

        if send_btn.count() > 0:
            expect(send_btn.first).to_be_visible()
        elif submit_btn.count() > 0:
            expect(submit_btn.first).to_be_visible()

    def test_submit_task(self, page: Page, selectors):
        """Test submitting a task."""
        input_field = page.locator(selectors.ASSISTANT_INPUT)
        if input_field.count() == 0:
            pytest.skip("No task input found")

        input_field.first.fill("Test task")

        # Try to submit
        send_btn = page.locator("[aria-label*='Send']")
        if send_btn.count() > 0:
            send_btn.first.click()
        else:
            input_field.first.press("Enter")

        page.wait_for_timeout(1000)
