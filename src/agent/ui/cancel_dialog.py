"""
Agent Cancel Dialog

Flet dialog for cancellation with mode selection.
"""

from typing import Callable

import flet as ft

from src.agent.models.cancel import CancelMode, CancellationRequest, ResultMode
from src.ui.theme import Theme


class CancelDialog(ft.AlertDialog):
    """
    Dialog for cancelling agent execution with mode options.

    Allows user to choose between immediate cancellation and
    finishing the current step, as well as whether to keep
    or rollback completed work.
    """

    def __init__(
        self,
        on_cancel: Callable[[CancellationRequest], None],
        elapsed_seconds: float = 0,
    ):
        """
        Initialize the cancel dialog.

        Args:
            on_cancel: Callback receiving the CancellationRequest when confirmed
            elapsed_seconds: Time elapsed for long-task warning (>30s shows warning)
        """
        self.on_cancel = on_cancel
        self.elapsed_seconds = elapsed_seconds

        # Internal state - default to safer options
        self.cancel_mode: CancelMode = CancelMode.AFTER_CURRENT
        self.result_mode: ResultMode = ResultMode.KEEP

        # Build dialog content
        super().__init__(
            modal=True,
            title=ft.Text("Cancel Task?", weight=ft.FontWeight.BOLD),
            content=self._build_content(),
            actions=[
                ft.TextButton("Continue Task", on_click=self._close),
                ft.ElevatedButton(
                    "Cancel Task",
                    on_click=self._confirm_cancel,
                    bgcolor=Theme.ERROR,
                    color=Theme.TEXT_PRIMARY,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

    def _build_content(self) -> ft.Column:
        """Build the dialog content."""
        content_items = [
            ft.Text("How would you like to stop?", color=Theme.TEXT_SECONDARY),
            ft.RadioGroup(
                content=ft.Column([
                    ft.Radio(
                        value=CancelMode.AFTER_CURRENT.value,
                        label="Finish current step, then stop",
                    ),
                    ft.Radio(
                        value=CancelMode.IMMEDIATE.value,
                        label="Stop immediately",
                    ),
                ]),
                value=CancelMode.AFTER_CURRENT.value,
                on_change=self._on_mode_change,
            ),
            ft.Divider(height=Theme.SPACING_MD),
            ft.Text("What about completed work?", color=Theme.TEXT_SECONDARY),
            ft.RadioGroup(
                content=ft.Column([
                    ft.Radio(
                        value=ResultMode.KEEP.value,
                        label="Keep changes",
                    ),
                    ft.Radio(
                        value=ResultMode.ROLLBACK.value,
                        label="Rollback changes",
                    ),
                ]),
                value=ResultMode.KEEP.value,
                on_change=self._on_result_change,
            ),
        ]

        # Add warning for long-running tasks
        if self.elapsed_seconds > 30:
            minutes = int(self.elapsed_seconds // 60)
            seconds = int(self.elapsed_seconds % 60)
            time_str = f"{minutes}m {seconds}s" if minutes > 0 else f"{seconds}s"
            content_items.append(ft.Divider(height=Theme.SPACING_MD))
            content_items.append(
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.WARNING_AMBER, color=Theme.WARNING, size=16),
                        ft.Text(
                            f"Task has been running for {time_str}",
                            color=Theme.WARNING,
                            size=Theme.FONT_SM,
                        ),
                    ], spacing=Theme.SPACING_XS),
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

    def _on_mode_change(self, e):
        """Handle cancel mode radio selection."""
        self.cancel_mode = CancelMode(e.control.value)

    def _on_result_change(self, e):
        """Handle result mode radio selection."""
        self.result_mode = ResultMode(e.control.value)

    def _confirm_cancel(self, e):
        """Confirm cancellation and call callback."""
        request = CancellationRequest(
            cancel_mode=self.cancel_mode,
            result_mode=self.result_mode,
            reason="User cancelled via dialog",
        )
        self.on_cancel(request)
        self._close(e)

    def _close(self, e):
        """Close the dialog."""
        self.open = False
        self.update()
