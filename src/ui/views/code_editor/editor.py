# src/ui/views/code_editor/editor.py
"""Code editor component with syntax highlighting."""

from collections.abc import Callable

import flet as ft

from src.services.editor import PygmentsHighlighter
from src.ui.components.code_editor import LineNumbers
from src.ui.theme import SkynetteTheme


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
        read_only: bool = False,
    ):
        """Initialize code editor.

        Args:
            content: Initial code content.
            language: Language for syntax highlighting (e.g., "python", "javascript").
            on_change: Callback when content changes, receives new content.
            read_only: If True, editor is read-only.
        """
        super().__init__()
        # Use _code_content to avoid conflict with ft.Container.content
        self._code_content = content
        self.language = language
        self.on_change = on_change
        self.read_only = read_only

        self.highlighter = PygmentsHighlighter()
        self._text_field: ft.TextField | None = None
        self._line_numbers: LineNumbers | None = None
        self._highlighted_text: ft.Text | None = None

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

        # Stack TextField and highlighted text
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

        if self.on_change:
            self.on_change(self._code_content)

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
