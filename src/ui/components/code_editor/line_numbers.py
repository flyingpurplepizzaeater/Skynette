# src/ui/components/code_editor/line_numbers.py
"""Line number gutter component for code editor."""

import flet as ft

from src.ui.theme import SkynetteTheme


class LineNumbers(ft.Container):
    """Line number gutter for code editor.

    Displays line numbers that sync with the editor content.
    Current line is highlighted with brighter color.
    Width auto-adjusts based on max line number digits.

    Example:
        line_nums = LineNumbers(line_count=100, current_line=42)
        # Update when content changes:
        line_nums.update_lines(150, current_line=60)
    """

    def __init__(
        self,
        line_count: int = 1,
        current_line: int = 1,
        line_height: int = 20,
    ):
        """Initialize line numbers gutter.

        Args:
            line_count: Total number of lines to display.
            current_line: Currently focused line (1-indexed).
            line_height: Height of each line in pixels.
        """
        super().__init__()
        self.line_count = line_count
        self.current_line = current_line
        self.line_height = line_height
        self._column: ft.Column | None = None

        # Build initial content
        self._build_content()

    def _build_content(self) -> None:
        """Build line numbers column content."""
        # Calculate width based on max line number digits
        max_digits = len(str(self.line_count))
        self.width = max(30, max_digits * 10 + 16)

        numbers = []
        for i in range(1, self.line_count + 1):
            is_current = i == self.current_line
            numbers.append(
                ft.Text(
                    str(i),
                    size=13,
                    font_family="monospace",
                    color=(
                        SkynetteTheme.TEXT_PRIMARY if is_current else SkynetteTheme.TEXT_SECONDARY
                    ),
                    text_align=ft.TextAlign.RIGHT,
                )
            )

        self._column = ft.Column(
            controls=numbers,
            spacing=0,
            scroll=ft.ScrollMode.HIDDEN,  # Synced externally
        )

        self.content = self._column
        self.padding = ft.padding.only(right=8)
        self.bgcolor = SkynetteTheme.BG_SECONDARY
        self.border = ft.border.only(right=ft.BorderSide(1, SkynetteTheme.BORDER))

    def update_lines(self, line_count: int, current_line: int = 1) -> None:
        """Update line count and current line.

        Args:
            line_count: New total number of lines.
            current_line: New current line (1-indexed).
        """
        self.line_count = line_count
        self.current_line = current_line
        self._build_content()
        self.update()
