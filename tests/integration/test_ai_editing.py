# tests/integration/test_ai_editing.py
"""Integration tests for AI-assisted editing features.

Tests the interaction between chat panel, diff preview, ghost text,
and the underlying services.

Note: These tests don't require a running Flet app - they test
the component logic and state management directly.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.ui.views.code_editor.ai_panel import (
    ChatState,
    ChatMessage,
    ChatPanel,
    DiffPreview,
    GhostTextOverlay,
    Suggestion,
)
from src.ai.gateway import AIGateway, GenerationConfig
from src.ai.completions import CompletionService, CompletionRequest, TokenCounter
from src.services.diff import DiffService, DiffHunk, DiffLine


class TestChatState:
    """Tests for ChatState state management."""

    def test_add_message_notifies_listeners(self):
        """Adding a message should notify all listeners."""
        state = ChatState()
        notified = []
        state.add_listener(lambda: notified.append(True))

        state.add_message("user", "Hello")

        assert len(notified) == 1
        assert len(state.messages) == 1
        assert state.messages[0].role == "user"
        assert state.messages[0].content == "Hello"

    def test_update_last_message_for_streaming(self):
        """update_last_message should modify the last message."""
        state = ChatState()
        state.add_message("assistant", "")

        state.update_last_message("Hello")
        assert state.messages[-1].content == "Hello"

        state.update_last_message("Hello world")
        assert state.messages[-1].content == "Hello world"

    def test_clear_messages(self):
        """clear_messages should remove all messages."""
        state = ChatState()
        state.add_message("user", "Test")
        state.add_message("assistant", "Response")

        state.clear_messages()

        assert len(state.messages) == 0

    def test_set_streaming_notifies(self):
        """set_streaming should update state and notify."""
        state = ChatState()
        notified = []
        state.add_listener(lambda: notified.append(True))

        state.set_streaming(True)

        assert state.is_streaming is True
        assert len(notified) == 1

    def test_remove_listener(self):
        """remove_listener should stop notifications."""
        state = ChatState()
        called = []
        callback = lambda: called.append(True)

        state.add_listener(callback)
        state.add_message("user", "Test")
        assert len(called) == 1

        state.remove_listener(callback)
        state.add_message("user", "Test2")
        assert len(called) == 1  # Not called again

    def test_dispose_clears_state(self):
        """dispose should clear all state and listeners."""
        state = ChatState()
        state.add_listener(lambda: None)
        state.add_message("user", "Test")

        state.dispose()

        assert len(state.messages) == 0
        assert len(state._listeners) == 0


class TestTokenCounter:
    """Tests for TokenCounter service."""

    def test_count_tokens_openai(self):
        """Should count tokens using OpenAI encoding."""
        counter = TokenCounter()
        count = counter.count_tokens("Hello world", provider="openai")
        assert count > 0
        assert count < 10  # "Hello world" is about 2-3 tokens

    def test_count_tokens_fallback(self):
        """Should use fallback for non-OpenAI providers."""
        counter = TokenCounter()
        count = counter.count_tokens("Hello world", provider="anthropic")
        assert count > 0

    def test_estimate_heuristic(self):
        """Heuristic should estimate ~4 chars per token."""
        counter = TokenCounter()
        # 40 chars = ~10 tokens by heuristic
        estimate = counter.estimate_heuristic("a" * 40)
        assert estimate == 10

    def test_is_within_limit(self):
        """is_within_limit should check against limit."""
        counter = TokenCounter()
        assert counter.is_within_limit("Hello", limit=100)
        # Very long text should exceed small limit
        long_text = "word " * 1000
        assert not counter.is_within_limit(long_text, limit=100)


class TestDiffService:
    """Tests for DiffService diff generation."""

    def test_generate_diff_single_change(self):
        """Should detect single line change."""
        service = DiffService()
        original = "line1\nline2\nline3"
        modified = "line1\nline2 changed\nline3"

        hunks = service.generate_diff(original, modified)

        assert len(hunks) >= 1
        # Should have both remove and add lines
        line_types = [line.line_type for h in hunks for line in h.lines]
        assert "add" in line_types
        assert "remove" in line_types

    def test_generate_diff_no_changes(self):
        """Should return empty list for identical content."""
        service = DiffService()
        content = "line1\nline2\nline3"

        hunks = service.generate_diff(content, content)

        assert len(hunks) == 0

    def test_generate_diff_addition(self):
        """Should detect line addition."""
        service = DiffService()
        original = "line1\nline2"
        modified = "line1\nline2\nline3"

        hunks = service.generate_diff(original, modified)

        assert len(hunks) >= 1
        add_lines = [line for h in hunks for line in h.lines if line.line_type == "add"]
        assert any("line3" in line.content for line in add_lines)

    def test_apply_hunks(self):
        """Should apply hunks to produce modified content."""
        service = DiffService()
        original = "line1\nline2\nline3"
        modified = "line1\nline2 changed\nline3"

        hunks = service.generate_diff(original, modified)
        result = service.apply_hunks(original, hunks)

        assert result.strip() == modified.strip()


class TestGhostTextOverlay:
    """Tests for GhostTextOverlay suggestions."""

    def test_show_suggestion(self):
        """Should display suggestion."""
        overlay = GhostTextOverlay()
        # Must call build before using - simulates Flet lifecycle
        overlay.build()
        suggestion = Suggestion(text=" + 1", position=10)

        # Mock update to avoid Flet runtime errors
        overlay.update = MagicMock()
        overlay.show_suggestion(suggestion, "x = 5")

        assert overlay.has_suggestion()
        assert overlay.current_text == " + 1"

    def test_accept_returns_text(self):
        """accept should return suggestion text."""
        accepted = []
        overlay = GhostTextOverlay(on_accept=lambda t: accepted.append(t))
        overlay.build()
        overlay.update = MagicMock()
        overlay.show_suggestion(Suggestion(text="test", position=0), "")

        result = overlay.accept()

        assert result == "test"
        assert accepted == ["test"]
        assert not overlay.has_suggestion()

    def test_dismiss_clears_suggestion(self):
        """dismiss should clear suggestion."""
        dismissed = []
        overlay = GhostTextOverlay(on_dismiss=lambda: dismissed.append(True))
        overlay.build()
        overlay.update = MagicMock()
        overlay.show_suggestion(Suggestion(text="test", position=0), "")

        overlay.dismiss()

        assert not overlay.has_suggestion()
        assert len(dismissed) == 1

    def test_accept_without_suggestion_returns_none(self):
        """accept should return None if no suggestion."""
        overlay = GhostTextOverlay()
        overlay.build()
        result = overlay.accept()
        assert result is None


# Run with: pytest tests/integration/test_ai_editing.py -v
