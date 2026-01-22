"""
Approval Sheet Component

Bottom sheet for human-in-the-loop action approval.
"""

import json
from typing import Callable, Optional

import flet as ft

from src.agent.safety.classification import ActionClassification
from src.agent.safety.approval import ApprovalRequest
from src.agent.ui.risk_badge import RiskBadge
from src.ui.theme import Theme


class ApprovalSheet(ft.BottomSheet):
    """
    Bottom sheet for action approval.

    Displays action details and provides Approve/Approve All Similar/Reject options.
    Does not dismiss on outside click - requires explicit decision.
    """

    def __init__(
        self,
        request: ApprovalRequest,
        on_approve: Callable[[bool], None],  # bool = approve_similar
        on_reject: Callable[[], None],
        on_timeout: Optional[Callable[[], None]] = None,
    ):
        """
        Initialize approval sheet.

        Args:
            request: The approval request with classification
            on_approve: Callback when approved (bool indicates approve_similar)
            on_reject: Callback when rejected
            on_timeout: Optional callback for timeout handling
        """
        self.request = request
        self.classification = request.classification
        self.on_approve = on_approve
        self.on_reject = on_reject
        self.on_timeout = on_timeout

        super().__init__(
            content=self._build_content(),
            show_drag_handle=True,
            # Critical: Don't dismiss on outside click - require explicit decision
            dismissible=False,
        )

    def _build_content(self) -> ft.Control:
        """Build the sheet content."""
        # Truncate parameters for display (first 500 chars)
        params_str = json.dumps(self.classification.parameters, indent=2)
        if len(params_str) > 500:
            params_str = params_str[:500] + "\n..."

        return ft.Container(
            padding=Theme.SPACING_LG,
            content=ft.Column(
                controls=[
                    # Header: Risk badge + tool name
                    ft.Row(
                        controls=[
                            RiskBadge(self.classification.risk_level),
                            ft.Text(
                                self.classification.tool_name,
                                weight=ft.FontWeight.BOLD,
                                size=Theme.FONT_LG,
                            ),
                        ],
                        spacing=Theme.SPACING_SM,
                    ),

                    # Reason
                    ft.Text(
                        self.classification.reason,
                        color=Theme.TEXT_SECONDARY,
                        size=Theme.FONT_SM,
                    ),

                    ft.Divider(height=Theme.SPACING_SM),

                    # Parameters preview
                    ft.Text(
                        "Parameters:",
                        size=Theme.FONT_SM,
                        weight=ft.FontWeight.W_500,
                    ),
                    ft.Container(
                        bgcolor=Theme.BG_TERTIARY,
                        border_radius=Theme.RADIUS_SM,
                        padding=Theme.SPACING_SM,
                        content=ft.Text(
                            params_str,
                            font_family="monospace",
                            size=Theme.FONT_XS,
                            selectable=True,
                        ),
                    ),

                    ft.Divider(height=Theme.SPACING_MD),

                    # Action buttons
                    ft.Row(
                        controls=[
                            ft.OutlinedButton(
                                "Reject",
                                on_click=self._handle_reject,
                                style=ft.ButtonStyle(
                                    color=Theme.ERROR,
                                ),
                            ),
                            ft.FilledButton(
                                "Approve",
                                on_click=lambda _: self._handle_approve(False),
                                style=ft.ButtonStyle(
                                    bgcolor=Theme.SUCCESS,
                                    color=Theme.TEXT_PRIMARY,
                                ),
                            ),
                            ft.FilledTonalButton(
                                "Approve All Similar",
                                on_click=lambda _: self._handle_approve(True),
                                tooltip="Auto-approve similar actions in this session",
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.END,
                        spacing=Theme.SPACING_SM,
                    ),
                ],
                spacing=Theme.SPACING_SM,
                tight=True,
                scroll=ft.ScrollMode.AUTO,
            ),
        )

    def _handle_approve(self, approve_similar: bool):
        """Handle approve button click."""
        self.open = False
        self.update()
        self.on_approve(approve_similar)

    def _handle_reject(self, e):
        """Handle reject button click."""
        self.open = False
        self.update()
        self.on_reject()

    def show(self, page: ft.Page):
        """Show the approval sheet."""
        self.open = True
        if self not in page.overlay:
            page.overlay.append(self)
        page.update()

    def hide(self):
        """Hide the approval sheet."""
        self.open = False
        self.update()
