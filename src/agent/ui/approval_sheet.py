"""
Approval Sheet Component

Bottom sheet for human-in-the-loop action approval.
Supports detail levels, parameter editing, and batch approval.
"""

import json
from typing import Callable, Literal, Optional

import flet as ft

from src.agent.safety.classification import ActionClassification
from src.agent.safety.approval import ApprovalRequest, ApprovalManager
from src.agent.ui.risk_badge import RiskBadge
from src.agent.ui.approval_detail_levels import (
    render_minimal,
    render_detailed,
    render_progressive,
)
from src.ui.theme import Theme


# Detail level type
DetailLevel = Literal["minimal", "detailed", "progressive"]

# Remember scope type
RememberScope = Literal["session", "type"]


class ApprovalSheet(ft.BottomSheet):
    """
    Bottom sheet for action approval.

    Displays action details and provides Approve/Approve All Similar/Reject options.
    Does not dismiss on outside click - requires explicit decision.

    Features:
    - Configurable detail levels (minimal, detailed, progressive)
    - Parameter editing before approval
    - Remember choice option with session/type scope
    - Batch approval for similar pending actions
    """

    def __init__(
        self,
        request: ApprovalRequest,
        on_approve: Callable[[bool], None],  # bool = approve_similar
        on_reject: Callable[[], None],
        on_timeout: Optional[Callable[[], None]] = None,
        detail_level: DetailLevel = "detailed",
        approval_manager: Optional[ApprovalManager] = None,
    ):
        """
        Initialize approval sheet.

        Args:
            request: The approval request with classification
            on_approve: Callback when approved. Can accept:
                - (approve_similar: bool)  # Legacy
                - (approve_similar: bool, modified_params: Optional[dict], remember_scope: Optional[str])
            on_reject: Callback when rejected
            on_timeout: Optional callback for timeout handling
            detail_level: Display detail level ("minimal", "detailed", "progressive")
            approval_manager: Optional manager for batch approval lookup
        """
        self.request = request
        self.classification = request.classification
        self._on_approve_callback = on_approve
        self.on_reject = on_reject
        self.on_timeout = on_timeout
        self.detail_level = detail_level
        self._approval_manager = approval_manager

        # Internal state for editing
        self._modified_params: Optional[dict] = None
        self._edit_mode: bool = False
        self._remember_choice: bool = False
        self._remember_scope: Optional[RememberScope] = None

        # UI references
        self._params_display: Optional[ft.Container] = None
        self._params_editor: Optional[ft.TextField] = None
        self._edit_btn: Optional[ft.TextButton] = None
        self._remember_checkbox: Optional[ft.Checkbox] = None
        self._remember_dropdown: Optional[ft.Dropdown] = None
        self._batch_card: Optional[ft.Container] = None

        super().__init__(
            content=self._build_content(),
            show_drag_handle=True,
            # Critical: Don't dismiss on outside click - require explicit decision
            dismissible=False,
        )

    def _get_similar_pending(self) -> list[ApprovalRequest]:
        """Get list of similar pending requests (excluding current)."""
        if not self._approval_manager:
            return []

        pending = self._approval_manager.get_pending()
        similar = []

        for req in pending:
            if req.id == self.request.id:
                continue
            if ApprovalManager.are_similar(self.classification, req.classification):
                similar.append(req)

        return similar

    def _build_content(self) -> ft.Control:
        """Build the sheet content."""
        # Get similar pending for batch approval display
        similar = self._get_similar_pending()

        # Build content based on detail level
        if self.detail_level == "minimal":
            detail_content = render_minimal(self.classification)
        elif self.detail_level == "progressive":
            detail_content = render_progressive(self.classification, expanded=False)
        else:
            detail_content = render_detailed(self.classification)

        # Build parameters editor (hidden by default)
        params_str = json.dumps(self.classification.parameters, indent=2)
        self._params_editor = ft.TextField(
            value=params_str,
            multiline=True,
            min_lines=3,
            max_lines=10,
            text_style=ft.TextStyle(
                font_family="monospace",
                size=Theme.FONT_XS,
            ),
            visible=False,
        )

        # Edit button
        self._edit_btn = ft.TextButton(
            "Edit parameters",
            icon=ft.Icons.EDIT,
            on_click=self._toggle_edit_mode,
        )

        # Remember choice UI
        self._remember_checkbox = ft.Checkbox(
            label="Remember this choice",
            value=False,
            on_change=self._handle_remember_change,
        )

        self._remember_dropdown = ft.Dropdown(
            label="Scope",
            width=180,
            visible=False,
            options=[
                ft.dropdown.Option("session", "For this session"),
                ft.dropdown.Option("type", "For this tool type"),
            ],
            on_select=self._handle_scope_change,
        )

        # Batch approval card (only if similar actions exist)
        self._batch_card = self._build_batch_card(similar) if similar else None

        controls = [
            # Content section (detail level dependent)
            detail_content,

            # Edit parameters section (only for non-minimal)
            ft.Container(
                visible=self.detail_level != "minimal",
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[self._edit_btn],
                            alignment=ft.MainAxisAlignment.END,
                        ),
                        self._params_editor,
                    ],
                    tight=True,
                    spacing=Theme.SPACING_XS,
                ),
            ),

            ft.Divider(height=Theme.SPACING_SM),

            # Remember choice section
            ft.Row(
                controls=[
                    self._remember_checkbox,
                    self._remember_dropdown,
                ],
                spacing=Theme.SPACING_SM,
            ),
        ]

        # Add batch card if present
        if self._batch_card:
            controls.append(ft.Divider(height=Theme.SPACING_SM))
            controls.append(self._batch_card)

        controls.append(ft.Divider(height=Theme.SPACING_MD))

        # Action buttons
        controls.append(
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
            )
        )

        return ft.Container(
            padding=Theme.SPACING_LG,
            content=ft.Column(
                controls=controls,
                spacing=Theme.SPACING_SM,
                tight=True,
                scroll=ft.ScrollMode.AUTO,
            ),
        )

    def _build_batch_card(self, similar: list[ApprovalRequest]) -> ft.Container:
        """Build batch approval card for similar pending actions."""
        count = len(similar)

        # Build expandable list of similar actions
        action_list = ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        RiskBadge(req.classification.risk_level, compact=True),
                        ft.Text(
                            req.classification.tool_name,
                            size=Theme.FONT_SM,
                        ),
                        ft.Text(
                            f"- {req.classification.reason[:50]}...",
                            size=Theme.FONT_XS,
                            color=Theme.TEXT_SECONDARY,
                            expand=True,
                        ),
                    ],
                    spacing=Theme.SPACING_SM,
                )
                for req in similar[:5]  # Limit to 5 shown
            ],
            tight=True,
            spacing=Theme.SPACING_XS,
            visible=False,
        )

        if count > 5:
            action_list.controls.append(
                ft.Text(
                    f"... and {count - 5} more",
                    size=Theme.FONT_XS,
                    color=Theme.TEXT_MUTED,
                    italic=True,
                )
            )

        # Expand button
        def toggle_list(e):
            action_list.visible = not action_list.visible
            e.control.icon = ft.Icons.EXPAND_LESS if action_list.visible else ft.Icons.EXPAND_MORE
            e.control.update()
            action_list.update()

        expand_btn = ft.IconButton(
            icon=ft.Icons.EXPAND_MORE,
            on_click=toggle_list,
            icon_size=16,
        )

        return ft.Container(
            bgcolor=Theme.BG_TERTIARY,
            border_radius=Theme.RADIUS_SM,
            padding=Theme.SPACING_SM,
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.LAYERS, size=16, color=Theme.INFO),
                            ft.Text(
                                f"{count} similar action{'s' if count != 1 else ''} pending",
                                size=Theme.FONT_SM,
                                weight=ft.FontWeight.W_500,
                            ),
                            expand_btn,
                        ],
                        spacing=Theme.SPACING_SM,
                    ),
                    action_list,
                ],
                tight=True,
                spacing=Theme.SPACING_XS,
            ),
        )

    def _toggle_edit_mode(self, e):
        """Toggle parameter editing mode."""
        self._edit_mode = not self._edit_mode

        if self._edit_mode:
            # Switch to edit mode
            self._edit_btn.text = "Cancel edit"
            self._edit_btn.icon = ft.Icons.CLOSE
            self._params_editor.visible = True
        else:
            # Switch back to view mode, reset any edits
            self._edit_btn.text = "Edit parameters"
            self._edit_btn.icon = ft.Icons.EDIT
            self._params_editor.visible = False
            # Reset editor to original
            self._params_editor.value = json.dumps(self.classification.parameters, indent=2)
            self._modified_params = None

        self.update()

    def _handle_remember_change(self, e):
        """Handle remember choice checkbox change."""
        self._remember_choice = e.control.value
        self._remember_dropdown.visible = self._remember_choice

        if not self._remember_choice:
            self._remember_scope = None
            self._remember_dropdown.value = None

        self.update()

    def _handle_scope_change(self, e):
        """Handle remember scope dropdown change."""
        self._remember_scope = e.control.value

    def _parse_edited_params(self) -> bool:
        """
        Parse edited parameters from the editor.

        Returns:
            True if parsing succeeded, False otherwise
        """
        if not self._edit_mode:
            return True

        try:
            self._modified_params = json.loads(self._params_editor.value)
            return True
        except json.JSONDecodeError as ex:
            # Show error indicator
            self._params_editor.error_text = f"Invalid JSON: {ex.msg}"
            self._params_editor.update()
            return False

    def _handle_approve(self, approve_similar: bool):
        """Handle approve button click."""
        # Parse edited params if in edit mode
        if not self._parse_edited_params():
            return  # Don't approve if params are invalid

        self.open = False
        self.update()

        # Call callback with extended signature if supported
        try:
            # Try extended signature
            self._on_approve_callback(
                approve_similar,
                self._modified_params,
                self._remember_scope,
            )
        except TypeError:
            # Fall back to legacy signature
            self._on_approve_callback(approve_similar)

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

    def get_modified_params(self) -> Optional[dict]:
        """Get the modified parameters if any were edited."""
        return self._modified_params

    def get_remember_scope(self) -> Optional[RememberScope]:
        """Get the remember scope if user checked remember checkbox."""
        return self._remember_scope if self._remember_choice else None
