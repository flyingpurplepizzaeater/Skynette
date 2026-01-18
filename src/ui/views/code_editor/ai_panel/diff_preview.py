# src/ui/views/code_editor/ai_panel/diff_preview.py
"""Diff preview component for reviewing AI-suggested changes.

Displays a unified diff with color-coded additions (green) and
deletions (red). Supports accepting/rejecting the entire diff
or individual hunks.
"""

from collections.abc import Callable

import flet as ft

from src.services.diff import DiffService, DiffHunk, DiffLine
from src.ui.theme import SkynetteTheme


class DiffPreview(ft.Column):
    """Diff preview component with accept/reject controls.

    Displays a unified diff with color-coded additions (green) and
    deletions (red). Supports accepting/rejecting the entire diff
    or individual hunks.

    Layout:
    - Header with Accept All / Reject All buttons
    - Scrollable diff view with hunks
    - Each hunk has its own accept/reject buttons

    Example:
        preview = DiffPreview(
            original="old code",
            modified="new code",
            on_accept=lambda content: apply_changes(content),
            on_reject=lambda: cancel_preview(),
        )
    """

    # GitHub-style diff colors
    ADDED_BG = "#22863a22"  # Green with transparency
    ADDED_TEXT = "#22863a"
    REMOVED_BG = "#cb243122"  # Red with transparency
    REMOVED_TEXT = "#cb2431"
    CONTEXT_TEXT = "#6a737d"
    HEADER_BG = "#f1f8ff"

    def __init__(
        self,
        original: str,
        modified: str,
        filename: str = "file",
        on_accept: Callable[[str], None] | None = None,
        on_reject: Callable[[], None] | None = None,
    ):
        """Initialize diff preview.

        Args:
            original: Original file content.
            modified: Modified content from AI.
            filename: Filename for diff header.
            on_accept: Callback when changes accepted, receives final content.
            on_reject: Callback when changes rejected.
        """
        super().__init__()
        self._original = original
        self._modified = modified
        self._filename = filename
        self._on_accept = on_accept
        self._on_reject = on_reject

        self._diff_service = DiffService()
        self._hunks: list[DiffHunk] = []
        self._accepted_hunks: set[int] = set()  # Track accepted hunk indices

        self.expand = True
        self.spacing = 0

    def build(self) -> None:
        """Build diff preview UI."""
        # Generate hunks
        self._hunks = self._diff_service.generate_diff(
            self._original,
            self._modified,
            self._filename,
        )

        if not self._hunks:
            # No changes
            self.controls = [
                ft.Container(
                    content=ft.Text("No changes detected", color=self.CONTEXT_TEXT),
                    padding=20,
                    alignment=ft.alignment.center,
                )
            ]
            return

        # Header with global actions
        header = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Text(f"Changes to {self._filename}", weight=ft.FontWeight.BOLD),
                    ft.Row(
                        [
                            ft.ElevatedButton(
                                "Accept All",
                                icon=ft.Icons.CHECK,
                                bgcolor=self.ADDED_TEXT,
                                color="white",
                                on_click=self._accept_all,
                            ),
                            ft.OutlinedButton(
                                "Reject All",
                                icon=ft.Icons.CLOSE,
                                on_click=self._reject_all,
                            ),
                        ],
                        spacing=10,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=10,
            bgcolor=SkynetteTheme.BG_SECONDARY,
        )

        # Diff content
        diff_content = ft.ListView(
            controls=[
                self._build_hunk_view(i, hunk) for i, hunk in enumerate(self._hunks)
            ],
            expand=True,
            spacing=10,
            padding=10,
        )

        self.controls = [header, diff_content]

    def _build_hunk_view(self, index: int, hunk: DiffHunk) -> ft.Control:
        """Build view for a single hunk."""
        # Hunk header
        header_text = f"@@ -{hunk.source_start},{hunk.source_length} +{hunk.target_start},{hunk.target_length} @@"
        if hunk.header:
            header_text += f" {hunk.header}"

        hunk_header = ft.Container(
            content=ft.Row(
                [
                    ft.Text(
                        header_text,
                        font_family="monospace",
                        size=12,
                        color=self.CONTEXT_TEXT,
                    ),
                    ft.Row(
                        [
                            ft.IconButton(
                                icon=ft.Icons.CHECK,
                                icon_color=self.ADDED_TEXT,
                                tooltip="Accept this change",
                                on_click=lambda e, i=index: self._accept_hunk(i),
                            ),
                            ft.IconButton(
                                icon=ft.Icons.CLOSE,
                                icon_color=self.REMOVED_TEXT,
                                tooltip="Reject this change",
                                on_click=lambda e, i=index: self._reject_hunk(i),
                            ),
                        ],
                        spacing=0,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            bgcolor=self.HEADER_BG,
            padding=5,
        )

        # Diff lines
        lines = [self._build_line_view(line) for line in hunk.lines]

        return ft.Container(
            content=ft.Column([hunk_header] + lines, spacing=0),
            border=ft.border.all(1, SkynetteTheme.BORDER),
            border_radius=4,
        )

    def _build_line_view(self, line: DiffLine) -> ft.Control:
        """Build view for a single diff line."""
        if line.line_type == "add":
            bgcolor = self.ADDED_BG
            text_color = self.ADDED_TEXT
            prefix = "+"
        elif line.line_type == "remove":
            bgcolor = self.REMOVED_BG
            text_color = self.REMOVED_TEXT
            prefix = "-"
        else:  # context
            bgcolor = None
            text_color = self.CONTEXT_TEXT
            prefix = " "

        # Line number display
        old_no = str(line.old_line_no) if line.old_line_no else ""
        new_no = str(line.new_line_no) if line.new_line_no else ""

        return ft.Container(
            content=ft.Row(
                [
                    ft.Text(
                        old_no.rjust(4),
                        font_family="monospace",
                        size=12,
                        color=self.CONTEXT_TEXT,
                        width=40,
                    ),
                    ft.Text(
                        new_no.rjust(4),
                        font_family="monospace",
                        size=12,
                        color=self.CONTEXT_TEXT,
                        width=40,
                    ),
                    ft.Text(
                        prefix + line.content,
                        font_family="monospace",
                        size=12,
                        color=text_color,
                        expand=True,
                    ),
                ],
                spacing=0,
            ),
            bgcolor=bgcolor,
            padding=ft.padding.symmetric(horizontal=5, vertical=1),
        )

    def _accept_all(self, e: ft.ControlEvent = None) -> None:
        """Accept all changes."""
        if self._on_accept:
            self._on_accept(self._modified)

    def _reject_all(self, e: ft.ControlEvent = None) -> None:
        """Reject all changes."""
        if self._on_reject:
            self._on_reject()

    def _accept_hunk(self, index: int) -> None:
        """Accept a single hunk."""
        self._accepted_hunks.add(index)
        self._update_preview()

    def _reject_hunk(self, index: int) -> None:
        """Reject a single hunk (remove from accepted if present)."""
        self._accepted_hunks.discard(index)
        self._update_preview()

    def _update_preview(self) -> None:
        """Update preview based on accepted hunks."""
        # Apply only accepted hunks
        accepted = [self._hunks[i] for i in sorted(self._accepted_hunks)]
        result = self._diff_service.apply_hunks(self._original, accepted)

        # Visual feedback - could update UI to show what's accepted
        # For now, just track state
        self.update()

    def get_result(self) -> str:
        """Get resulting content with accepted hunks applied.

        Returns:
            Original content if no hunks accepted, otherwise
            original with accepted hunks applied.
        """
        if not self._accepted_hunks:
            return self._original

        accepted = [self._hunks[i] for i in sorted(self._accepted_hunks)]
        return self._diff_service.apply_hunks(self._original, accepted)

    def has_pending_changes(self) -> bool:
        """Check if there are unaccepted changes."""
        return len(self._accepted_hunks) < len(self._hunks)
