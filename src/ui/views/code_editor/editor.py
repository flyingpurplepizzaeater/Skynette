# src/ui/views/code_editor/editor.py
"""Code editor component with syntax highlighting and ghost text suggestions."""

import asyncio
from collections.abc import Callable

import flet as ft

from src.services.editor import PygmentsHighlighter
from src.ui.components.code_editor import LineNumbers
from src.ui.theme import SkynetteTheme
from src.ui.views.code_editor.ai_panel import GhostTextOverlay, Suggestion


class CodeEditor(ft.Container):
    """Code editor with syntax highlighting.

    Uses TextField for editing with syntax-highlighted overlay.
    Includes line numbers gutter.

    The TextField is transparent but captures all keyboard input.
    The highlighted Text renders below it.
    This approach avoids cursor/selection sync issues.

    Example:
        editor = CodeEditor(
            content="def hello(): pass",
            language="python",
            on_change=lambda content: print("Changed:", content),
        )
    """

    def __init__(
        self,
        content: str = "",
        language: str = "text",
        on_change: Callable[[str], None] | None = None,
        on_request_completion: Callable[[str, str], None] | None = None,
        read_only: bool = False,
    ):
        """Initialize code editor.

        Args:
            content: Initial code content.
            language: Language for syntax highlighting (e.g., "python", "javascript").
            on_change: Callback when content changes, receives new content.
            on_request_completion: Callback to request AI completion, receives (code, language).
            read_only: If True, editor is read-only.
        """
        super().__init__()
        # Use _code_content to avoid conflict with ft.Container.content
        self._code_content = content
        self.language = language
        self.on_change = on_change
        self._on_request_completion = on_request_completion
        self.read_only = read_only

        self.highlighter = PygmentsHighlighter()
        self._text_field: ft.TextField | None = None
        self._line_numbers: LineNumbers | None = None
        self._highlighted_text: ft.Text | None = None

        # Ghost text for inline suggestions
        self._ghost_overlay: GhostTextOverlay | None = None
        self._completion_timer: asyncio.Task | None = None

        # Build initial UI content
        self._build_ui()

    def _build_ui(self) -> None:
        """Build editor with line numbers and editing area."""
        line_count = self._code_content.count("\n") + 1
        self._line_numbers = LineNumbers(line_count=line_count)

        # TextField for actual editing (invisible text, captures input)
        self._text_field = ft.TextField(
            value=self._code_content,
            multiline=True,
            min_lines=20,
            expand=True,
            border=ft.InputBorder.NONE,
            bgcolor="transparent",
            color="transparent",  # Hide actual text
            cursor_color=SkynetteTheme.TEXT_PRIMARY,
            text_style=ft.TextStyle(
                font_family="monospace",
                size=13,
            ),
            on_change=self._handle_change,
            read_only=self.read_only,
        )

        # Highlighted text overlay (display only)
        spans = self.highlighter.highlight(self._code_content, self.language)
        self._highlighted_text = ft.Text(
            spans=spans,
            font_family="monospace",
            size=13,
            selectable=False,
        )

        # Ghost text overlay for inline suggestions
        self._ghost_overlay = GhostTextOverlay(
            on_accept=self._accept_suggestion,
            on_dismiss=self._dismiss_suggestion,
        )

        # Stack TextField, highlighted text, and ghost overlay
        editor_stack = ft.Stack(
            controls=[
                # Highlighted text at bottom (display)
                ft.Container(
                    content=self._highlighted_text,
                    padding=ft.padding.all(8),
                ),
                # TextField on top (editing, transparent text)
                ft.Container(
                    content=self._text_field,
                    padding=ft.padding.all(8),
                ),
                # Ghost text overlay (on top for visual display)
                self._ghost_overlay,
            ],
            expand=True,
        )

        editor_row = ft.Row(
            controls=[
                self._line_numbers,
                ft.Container(
                    content=editor_stack,
                    expand=True,
                    bgcolor=SkynetteTheme.BG_PRIMARY,
                ),
            ],
            spacing=0,
            expand=True,
        )

        # Set container content (ft.Container.content property)
        self.content = editor_row
        self.expand = True

    def _handle_change(self, e: ft.ControlEvent) -> None:
        """Handle text changes - update highlighting and notify."""
        self._code_content = e.control.value
        line_count = self._code_content.count("\n") + 1
        self._line_numbers.update_lines(line_count)

        # Re-highlight
        spans = self.highlighter.highlight(self._code_content, self.language)
        self._highlighted_text.spans = spans
        self._highlighted_text.update()

        # Hide any existing suggestion on typing
        if self._ghost_overlay and self._ghost_overlay.has_suggestion():
            self._ghost_overlay.hide_suggestion()

        # Trigger completion after typing pause
        self._schedule_completion()

        if self.on_change:
            self.on_change(self._code_content)

    def _schedule_completion(self) -> None:
        """Schedule completion request after debounce delay."""
        # Cancel any pending completion request
        if self._completion_timer and not self._completion_timer.done():
            self._completion_timer.cancel()

        async def request_after_delay() -> None:
            await asyncio.sleep(0.5)  # 500ms debounce
            if self._on_request_completion:
                self._on_request_completion(self._code_content, self.language)

        self._completion_timer = asyncio.create_task(request_after_delay())

    def show_suggestion(self, suggestion: str) -> None:
        """Show inline suggestion as ghost text.

        Args:
            suggestion: The completion text to display.
        """
        if self._ghost_overlay:
            self._ghost_overlay.show_suggestion(
                Suggestion(text=suggestion, position=len(self._code_content)),
                self._code_content,
            )

    def _accept_suggestion(self, text: str) -> None:
        """Accept suggestion - append to content.

        Args:
            text: Suggestion text to append.
        """
        self._code_content += text
        if self._text_field:
            self._text_field.value = self._code_content
            self._text_field.update()
        # Trigger re-highlight without callback (avoid loop)
        line_count = self._code_content.count("\n") + 1
        self._line_numbers.update_lines(line_count)
        spans = self.highlighter.highlight(self._code_content, self.language)
        self._highlighted_text.spans = spans
        self._highlighted_text.update()
        # Notify of content change
        if self.on_change:
            self.on_change(self._code_content)

    def _dismiss_suggestion(self) -> None:
        """Dismiss suggestion without accepting."""
        pass  # Ghost overlay handles hide

    def set_content(self, content: str, language: str | None = None) -> None:
        """Set editor content and optionally language.

        Args:
            content: New code content.
            language: New language for highlighting (optional).
        """
        self._code_content = content
        if language:
            self.language = language
        if self._text_field:
            self._text_field.value = content
            # Trigger re-highlight
            line_count = content.count("\n") + 1
            self._line_numbers.update_lines(line_count)
            spans = self.highlighter.highlight(content, self.language)
            self._highlighted_text.spans = spans
            self._highlighted_text.update()
            self._text_field.update()

    def get_content(self) -> str:
        """Get current editor content.

        Returns:
            Current content string.
        """
        return self._code_content

    def dispose(self) -> None:
        """Clean up editor resources."""
        # Cancel any pending completion request
        if self._completion_timer and not self._completion_timer.done():
            self._completion_timer.cancel()
        self._completion_timer = None
        self._text_field = None
        self._line_numbers = None
        self._highlighted_text = None
        self._ghost_overlay = None
