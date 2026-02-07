# src/ui/views/code_editor/ai_panel/diff_preview.py
"""Diff preview component for reviewing AI-suggested changes.

Displays a unified diff with color-coded additions (green) and
deletions (red). Supports accepting/rejecting the entire diff
or individual hunks.
"""

from collections.abc import Callable

import flet as ft

from src.services.diff import DiffHunk, DiffLine, DiffService
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
        yolo_mode: bool = False,
    ):
        """Initialize diff preview.

        Args:
            original: Original file content.
            modified: Modified content from AI.
            filename: Filename for diff header.
            on_accept: Callback when changes accepted, receives final content.
            on_reject: Callback when changes rejected.
            yolo_mode: If True, auto-accept without showing preview.
        """
        super().__init__()
        self._original = original
        self._modified = modified
        self._filename = filename
        self._on_accept = on_accept
        self._on_reject = on_reject
        self._yolo_mode = yolo_mode

        self._diff_service = DiffService()
        self._hunks: list[DiffHunk] = []
        self._accepted_hunks: set[int] = set()  # Track accepted hunk indices

        # UI references for updates
        self._hunk_containers: list[ft.Container] = []
        self._apply_selected_btn: ft.OutlinedButton | None = None

        self.expand = True
        self.spacing = 0

    def build(self) -> None:
        """Build diff preview UI."""
        # Yolo mode: auto-accept immediately without showing preview
        if self._yolo_mode:
            if self._on_accept:
                self._on_accept(self._modified)
            return

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
                    alignment=ft.Alignment.CENTER,
                )
            ]
            return

        # Apply Selected button (initially hidden)
        self._apply_selected_btn = ft.OutlinedButton(
            "Apply Selected",
            icon=ft.Icons.PLAYLIST_ADD_CHECK,
            on_click=self._apply_selected,
            visible=False,
        )

        # Header with global actions
        header = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Column(
                        [
                            ft.Text(
                                f"Changes to {self._filename}",
                                weight=ft.FontWeight.BOLD,
                            ),
                            self._build_stats(),
                        ],
                        spacing=2,
                    ),
                    ft.Row(
                        [
                            self._apply_selected_btn,
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

        # Build hunk containers and store references
        self._hunk_containers = []
        for i, hunk in enumerate(self._hunks):
            container = self._build_hunk_view(i, hunk)
            self._hunk_containers.append(container)

        # Diff content
        diff_content = ft.ListView(
            controls=self._hunk_containers,
            expand=True,
            spacing=10,
            padding=10,
        )

        self.controls = [header, diff_content]

    def _build_stats(self) -> ft.Control:
        """Build statistics row showing change counts."""
        additions = sum(1 for h in self._hunks for line in h.lines if line.line_type == "add")
        deletions = sum(1 for h in self._hunks for line in h.lines if line.line_type == "remove")

        return ft.Row(
            [
                ft.Text(f"+{additions}", color=self.ADDED_TEXT, size=12),
                ft.Text(f"-{deletions}", color=self.REMOVED_TEXT, size=12),
                ft.Text(
                    f"{len(self._hunks)} hunk{'s' if len(self._hunks) != 1 else ''}",
                    color=self.CONTEXT_TEXT,
                    size=12,
                ),
            ],
            spacing=15,
        )

    def _build_hunk_view(self, index: int, hunk: DiffHunk) -> ft.Container:
        """Build view for a single hunk."""
        is_accepted = index in self._accepted_hunks

        # Hunk header
        header_text = f"@@ -{hunk.source_start},{hunk.source_length} +{hunk.target_start},{hunk.target_length} @@"
        if hunk.header:
            header_text += f" {hunk.header}"

        # Visual indicator for accepted state
        status_icon = (
            ft.Icon(ft.Icons.CHECK_CIRCLE, color=self.ADDED_TEXT, size=16) if is_accepted else None
        )

        hunk_header = ft.Container(
            content=ft.Row(
                [
                    ft.Row(
                        [
                            status_icon,
                            ft.Text(
                                header_text,
                                font_family="monospace",
                                size=12,
                                color=self.CONTEXT_TEXT,
                            ),
                        ]
                        if status_icon
                        else [
                            ft.Text(
                                header_text,
                                font_family="monospace",
                                size=12,
                                color=self.CONTEXT_TEXT,
                            ),
                        ],
                        spacing=5,
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

        # Visual feedback: thicker green border for accepted hunks
        border_color = self.ADDED_TEXT if is_accepted else SkynetteTheme.BORDER
        border_width = 2 if is_accepted else 1

        return ft.Container(
            content=ft.Column([hunk_header] + lines, spacing=0),
            border=ft.border.all(border_width, border_color),
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

    def _apply_selected(self, e: ft.ControlEvent = None) -> None:
        """Apply only the selected (accepted) hunks."""
        result = self.get_result()
        if self._on_accept:
            self._on_accept(result)

    def _update_preview(self) -> None:
        """Update preview based on accepted hunks."""
        # Update apply selected button visibility
        if self._apply_selected_btn:
            self._apply_selected_btn.visible = len(self._accepted_hunks) > 0
            self._apply_selected_btn.update()

        # Rebuild hunk containers with updated accepted state
        for i, container in enumerate(self._hunk_containers):
            is_accepted = i in self._accepted_hunks
            border_color = self.ADDED_TEXT if is_accepted else SkynetteTheme.BORDER
            border_width = 2 if is_accepted else 1
            container.border = ft.border.all(border_width, border_color)

            # Update the hunk header to show/hide status icon
            hunk_column = container.content
            if isinstance(hunk_column, ft.Column) and hunk_column.controls:
                header_container = hunk_column.controls[0]
                if isinstance(header_container, ft.Container):
                    header_row = header_container.content
                    if isinstance(header_row, ft.Row) and header_row.controls:
                        left_row = header_row.controls[0]
                        if isinstance(left_row, ft.Row):
                            # Rebuild with or without status icon
                            header_text = f"@@ -{self._hunks[i].source_start},{self._hunks[i].source_length} +{self._hunks[i].target_start},{self._hunks[i].target_length} @@"
                            if self._hunks[i].header:
                                header_text += f" {self._hunks[i].header}"
                            text_control = ft.Text(
                                header_text,
                                font_family="monospace",
                                size=12,
                                color=self.CONTEXT_TEXT,
                            )
                            if is_accepted:
                                left_row.controls = [
                                    ft.Icon(
                                        ft.Icons.CHECK_CIRCLE,
                                        color=self.ADDED_TEXT,
                                        size=16,
                                    ),
                                    text_control,
                                ]
                            else:
                                left_row.controls = [text_control]

            container.update()

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

    def dispose(self) -> None:
        """Clean up resources."""
        self._hunks.clear()
        self._accepted_hunks.clear()
        self._hunk_containers.clear()
        self._on_accept = None
        self._on_reject = None
        self._apply_selected_btn = None
        self.controls.clear()
