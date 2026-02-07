# src/ui/views/code_editor/ai_panel/ghost_text.py
"""Ghost text overlay for inline code suggestions.

Displays dimmed suggestion text that appears after the cursor position,
designed to be layered on top of a TextField in a Stack.
"""

from collections.abc import Callable
from dataclasses import dataclass

import flet as ft


@dataclass
class Suggestion:
    """An inline code suggestion."""

    text: str
    position: int  # Character position in editor
    is_multiline: bool = False


class GhostTextOverlay(ft.Container):
    """Overlay component that displays ghost text suggestions.

    Designed to be layered on top of a TextField in a Stack.
    Shows dimmed suggestion text that appears after the cursor.

    The overlay matches the TextField's font and positioning to
    ensure the ghost text aligns perfectly with typed text.

    Example:
        overlay = GhostTextOverlay(on_accept=handle_accept, on_dismiss=handle_dismiss)
        stack = ft.Stack([text_field, overlay])
    """

    # Ghost text styling (user configurable in future)
    GHOST_COLOR = ft.Colors.with_opacity(0.4, ft.Colors.WHITE)
    GHOST_FONT = "monospace"
    GHOST_SIZE = 13

    def __init__(
        self,
        on_accept: Callable[[str], None] | None = None,
        on_dismiss: Callable[[], None] | None = None,
    ):
        """Initialize ghost text overlay.

        Args:
            on_accept: Callback when suggestion accepted, receives suggestion text.
            on_dismiss: Callback when suggestion dismissed.
        """
        super().__init__()
        self._on_accept = on_accept
        self._on_dismiss = on_dismiss
        self._current_suggestion: Suggestion | None = None
        self._ghost_text: ft.Text | None = None

        self.visible = False
        self.expand = True

    def build(self) -> None:
        """Build ghost text display."""
        self._ghost_text = ft.Text(
            value="",
            color=self.GHOST_COLOR,
            font_family=self.GHOST_FONT,
            size=self.GHOST_SIZE,
            selectable=False,
        )

        self.content = ft.Container(
            content=self._ghost_text,
            padding=ft.padding.all(8),  # Match TextField padding
        )

    def show_suggestion(self, suggestion: Suggestion, prefix_text: str) -> None:
        """Show a suggestion at the specified position.

        Args:
            suggestion: The suggestion to display.
            prefix_text: Text before cursor (used for positioning).
        """
        self._current_suggestion = suggestion

        # Build display text: prefix (invisible) + suggestion
        # This positions the ghost text after the typed content
        display = prefix_text + suggestion.text

        self._ghost_text.value = display
        self._ghost_text.spans = [
            # Invisible prefix (same as typed text)
            ft.TextSpan(prefix_text, style=ft.TextStyle(color="transparent")),
            # Visible ghost suggestion
            ft.TextSpan(suggestion.text, style=ft.TextStyle(color=self.GHOST_COLOR)),
        ]

        self.visible = True
        self.update()

    def hide_suggestion(self) -> None:
        """Hide current suggestion."""
        self._current_suggestion = None
        self._ghost_text.value = ""
        self._ghost_text.spans = []
        self.visible = False
        self.update()

    def accept(self) -> str | None:
        """Accept current suggestion.

        Returns:
            Accepted suggestion text, or None if no suggestion.
        """
        if self._current_suggestion is None:
            return None

        text = self._current_suggestion.text
        self.hide_suggestion()

        if self._on_accept:
            self._on_accept(text)

        return text

    def dismiss(self) -> None:
        """Dismiss current suggestion without accepting."""
        self.hide_suggestion()
        if self._on_dismiss:
            self._on_dismiss()

    def has_suggestion(self) -> bool:
        """Check if a suggestion is currently displayed."""
        return self._current_suggestion is not None

    @property
    def current_text(self) -> str | None:
        """Get current suggestion text, or None."""
        return self._current_suggestion.text if self._current_suggestion else None
