"""
YOLO Confirmation Dialog

Flet dialog for confirming L5 (YOLO) mode activation.
"""

from typing import Callable

import flet as ft

from src.ui.theme import Theme

# YOLO mode purple color
YOLO_COLOR = "#8B5CF6"


class YoloConfirmationDialog(ft.AlertDialog):
    """
    Confirmation dialog for enabling YOLO (L5) mode.

    Unlike L1-L4 which switch instantly, L5 requires explicit confirmation
    since it bypasses all approval prompts. Shows additional warning when
    not in a sandboxed environment.
    """

    def __init__(
        self,
        is_sandboxed: bool,
        on_confirm: Callable[[], None],
        on_dont_warn_again: Callable[[], None] | None = None,
    ):
        """
        Initialize the YOLO confirmation dialog.

        Args:
            is_sandboxed: Whether the environment is sandboxed
            on_confirm: Callback when user confirms enabling YOLO mode
            on_dont_warn_again: Optional callback for "don't warn again" option
        """
        self.is_sandboxed = is_sandboxed
        self.on_confirm = on_confirm
        self.on_dont_warn_again = on_dont_warn_again

        # Build dialog
        super().__init__(
            modal=True,
            title=ft.Text("Enable YOLO Mode?", weight=ft.FontWeight.BOLD),
            content=self._build_content(),
            actions=self._build_actions(),
            actions_alignment=ft.MainAxisAlignment.END,
        )

    def _build_content(self) -> ft.Column:
        """Build the dialog content."""
        content_items = [
            ft.Text(
                "Actions will execute without approval prompts",
                color=Theme.TEXT_SECONDARY,
            ),
        ]

        # Add warning for non-sandboxed environment
        if not self.is_sandboxed:
            content_items.append(ft.Divider(height=Theme.SPACING_MD))
            content_items.append(
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Icon(ft.Icons.WARNING_AMBER, color=Theme.WARNING, size=16),
                            ft.Text(
                                "Not detected as sandboxed environment",
                                color=Theme.WARNING,
                                size=Theme.FONT_SM,
                            ),
                        ],
                        spacing=Theme.SPACING_XS,
                    ),
                    padding=Theme.SPACING_SM,
                    bgcolor=f"{Theme.WARNING}20",
                    border_radius=Theme.RADIUS_SM,
                )
            )

        return ft.Column(
            controls=content_items,
            spacing=Theme.SPACING_SM,
            tight=True,
        )

    def _build_actions(self) -> list:
        """Build the dialog action buttons."""
        actions = [
            ft.TextButton("Cancel", on_click=self._close),
        ]

        # Add "Don't warn again" button for non-sandboxed + callback provided
        if not self.is_sandboxed and self.on_dont_warn_again is not None:
            actions.append(
                ft.TextButton(
                    "Don't warn again",
                    on_click=self._dont_warn_again,
                )
            )

        # Main confirm button
        actions.append(
            ft.ElevatedButton(
                "Enable YOLO Mode",
                on_click=self._confirm,
                bgcolor=YOLO_COLOR,
                color=Theme.TEXT_PRIMARY,
            )
        )

        return actions

    def _confirm(self, e=None):
        """Confirm YOLO mode and close dialog."""
        self.on_confirm()
        self._close(e)

    def _dont_warn_again(self, e=None):
        """Handle 'don't warn again' - calls callback then confirms."""
        if self.on_dont_warn_again is not None:
            self.on_dont_warn_again()
        self._confirm(e)

    def _close(self, e=None):
        """Close the dialog."""
        self.open = False
        self.update()
