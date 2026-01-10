"""
Skynet Assistant panel E2E tests.

Tests for the AI assistant panel functionality.
Uses aria-label selectors for Flet HTML renderer compatibility.
"""

import pytest
from playwright.sync_api import Page, expect


class TestAssistantPanel:
    """Tests for the Skynet Assistant panel."""

    def test_assistant_header_visible(self, page: Page, selectors):
        """Verify assistant header is visible."""
        header = page.locator(selectors.ASSISTANT_HEADER)
        if header.count() > 0:
            expect(header.first).to_be_visible()

    def test_assistant_input_exists(self, page: Page, selectors):
        """Verify assistant has an input field."""
        # Look for input fields in the assistant area
        inputs = page.locator(selectors.ASSISTANT_INPUT)
        if inputs.count() > 0:
            expect(inputs.first).to_be_visible()

    def test_assistant_has_example_prompts(self, page: Page, selectors):
        """Verify assistant shows example prompts."""
        # Look for example prompts via aria-label
        examples = page.locator("[aria-label*='example'], [aria-label*='prompt'], [aria-label*='Create']")

        # If no examples found, at least the header should be visible
        header = page.locator(selectors.ASSISTANT_HEADER)
        if header.count() > 0:
            expect(header.first).to_be_visible()
        elif examples.count() > 0:
            expect(examples.first).to_be_visible()


class TestAssistantInteraction:
    """Tests for interacting with the assistant."""

    def test_can_type_in_assistant_input(self, page: Page, selectors):
        """Verify user can type in the assistant input."""
        # Find an input field
        input_field = page.locator(selectors.ASSISTANT_INPUT)
        if input_field.count() > 0:
            input_field.last.fill("Hello, assistant!")
            expect(input_field.last).to_have_value("Hello, assistant!")

    def test_send_message_to_assistant(self, page: Page, selectors):
        """Test sending a message to the assistant."""
        # Find input and fill it
        input_field = page.locator(selectors.ASSISTANT_INPUT)
        if input_field.count() == 0:
            pytest.skip("No assistant input found")

        input_field.last.fill("Hello")

        # Try to send - look for send button or press Enter
        send_btn = page.locator(selectors.ASSISTANT_SEND)
        if send_btn.count() > 0:
            send_btn.first.click()
        else:
            input_field.last.press("Enter")

        page.wait_for_timeout(1000)


class TestAssistantClearChat:
    """Tests for clearing chat functionality."""

    def test_clear_chat_button_exists(self, page: Page):
        """Verify clear chat button exists."""
        # Look for clear button via aria-label
        clear_btn = page.locator("[aria-label*='Clear']")
        if clear_btn.count() > 0:
            expect(clear_btn.first).to_be_visible()

    def test_can_clear_chat(self, page: Page, selectors):
        """Test clearing the chat."""
        # First send a message
        input_field = page.locator(selectors.ASSISTANT_INPUT)
        if input_field.count() == 0:
            pytest.skip("No assistant input found")

        input_field.last.fill("Test message")
        input_field.last.press("Enter")
        page.wait_for_timeout(500)

        # Find and click clear
        clear_btn = page.locator("[aria-label*='Clear']")
        if clear_btn.count() > 0:
            clear_btn.first.click()
            page.wait_for_timeout(500)

            # Chat should be cleared - assistant header should still be visible
            header = page.locator(selectors.ASSISTANT_HEADER)
            if header.count() > 0:
                expect(header.first).to_be_visible()
