"""
Audit Trail View Component

Displays scrollable, filterable audit trail of agent actions.
"""

import json
from typing import Optional

import flet as ft

from src.agent.safety.audit import AuditEntry, get_audit_store
from src.agent.safety.classification import RiskLevel, RISK_COLORS, RISK_LABELS
from src.agent.ui.risk_badge import RiskBadge
from src.ui.theme import Theme


# Approval decision display
APPROVAL_BADGES: dict[str, tuple[str, str]] = {
    "approved": ("Approved", Theme.SUCCESS),
    "rejected": ("Rejected", Theme.ERROR),
    "auto": ("Auto", Theme.INFO),
    "not_required": ("", ""),  # No badge needed
}


class AuditEntryRow(ft.Container):
    """
    Single audit entry with expandable details.

    Collapsed: RiskBadge + tool_name + timestamp + duration
    Expanded: Parameters, result/error, full timestamp, approved_by
    """

    def __init__(self, entry: AuditEntry):
        """
        Initialize audit entry row.

        Args:
            entry: AuditEntry to display
        """
        self._entry = entry
        self._expanded = False

        # Build UI components
        super().__init__(
            content=self._build_content(),
            bgcolor=Theme.BG_SECONDARY,
            border=ft.border.all(1, Theme.BORDER),
            border_radius=Theme.RADIUS_SM,
            padding=Theme.SPACING_SM,
            on_click=self._toggle_expand,
        )

    def _build_content(self) -> ft.Control:
        """Build the entry content (collapsed or expanded)."""
        # Collapsed row: risk badge + tool + time + duration
        risk_badge = RiskBadge(self._entry.risk_level, compact=True)

        # Format timestamp (HH:MM:SS)
        time_str = self._entry.timestamp.strftime("%H:%M:%S")

        # Duration
        duration_str = f"{self._entry.duration_ms:.0f}ms"

        # Approval badge if needed
        approval_controls = []
        if self._entry.approval_required:
            badge_text, badge_color = APPROVAL_BADGES.get(
                self._entry.approval_decision, ("", "")
            )
            if badge_text:
                approval_controls.append(
                    ft.Container(
                        content=ft.Text(
                            badge_text,
                            size=Theme.FONT_XS,
                            color=badge_color,
                        ),
                        bgcolor=f"{badge_color}20",
                        border=ft.border.all(1, badge_color),
                        border_radius=Theme.RADIUS_SM,
                        padding=ft.padding.symmetric(horizontal=4, vertical=2),
                    )
                )

        # Collapsed row
        collapsed_row = ft.Row(
            controls=[
                risk_badge,
                ft.Text(
                    self._entry.tool_name,
                    size=Theme.FONT_SM,
                    color=Theme.TEXT_PRIMARY,
                    weight=ft.FontWeight.W_500,
                    expand=True,
                ),
                *approval_controls,
                ft.Text(
                    time_str,
                    size=Theme.FONT_XS,
                    color=Theme.TEXT_MUTED,
                ),
                ft.Text(
                    duration_str,
                    size=Theme.FONT_XS,
                    color=Theme.TEXT_SECONDARY,
                    width=50,
                    text_align=ft.TextAlign.RIGHT,
                ),
                ft.Icon(
                    ft.Icons.EXPAND_MORE if not self._expanded else ft.Icons.EXPAND_LESS,
                    size=16,
                    color=Theme.TEXT_MUTED,
                ),
            ],
            spacing=Theme.SPACING_SM,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        if not self._expanded:
            return collapsed_row

        # Expanded view with details
        details = self._build_details()

        return ft.Column(
            controls=[
                collapsed_row,
                ft.Container(
                    content=details,
                    padding=ft.padding.only(
                        top=Theme.SPACING_SM,
                        left=Theme.SPACING_MD,
                    ),
                    border=ft.border.only(top=ft.BorderSide(1, Theme.BORDER)),
                    margin=ft.margin.only(top=Theme.SPACING_SM),
                ),
            ],
            spacing=0,
        )

    def _build_details(self) -> ft.Control:
        """Build expanded detail view."""
        detail_rows = []

        # Full timestamp
        full_time = self._entry.timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        detail_rows.append(
            ft.Row(
                controls=[
                    ft.Text("Timestamp:", size=Theme.FONT_XS, color=Theme.TEXT_MUTED),
                    ft.Text(full_time, size=Theme.FONT_XS, color=Theme.TEXT_SECONDARY),
                ],
                spacing=Theme.SPACING_SM,
            )
        )

        # Approved by (if applicable)
        if self._entry.approved_by:
            detail_rows.append(
                ft.Row(
                    controls=[
                        ft.Text("Approved by:", size=Theme.FONT_XS, color=Theme.TEXT_MUTED),
                        ft.Text(
                            self._entry.approved_by,
                            size=Theme.FONT_XS,
                            color=Theme.TEXT_SECONDARY,
                        ),
                    ],
                    spacing=Theme.SPACING_SM,
                )
            )

        # Parameters (code block, truncated)
        if self._entry.parameters:
            try:
                params_str = json.dumps(self._entry.parameters, indent=2)
                if len(params_str) > 500:
                    params_str = params_str[:500] + "\n..."
            except (TypeError, ValueError):
                params_str = str(self._entry.parameters)[:500]

            detail_rows.append(
                ft.Column(
                    controls=[
                        ft.Text("Parameters:", size=Theme.FONT_XS, color=Theme.TEXT_MUTED),
                        ft.Container(
                            content=ft.Text(
                                params_str,
                                size=Theme.FONT_XS,
                                color=Theme.TEXT_SECONDARY,
                                font_family="monospace",
                            ),
                            bgcolor=Theme.BG_TERTIARY,
                            border_radius=Theme.RADIUS_SM,
                            padding=Theme.SPACING_XS,
                        ),
                    ],
                    spacing=2,
                )
            )

        # Result or error
        if self._entry.error:
            detail_rows.append(
                ft.Column(
                    controls=[
                        ft.Text("Error:", size=Theme.FONT_XS, color=Theme.ERROR),
                        ft.Container(
                            content=ft.Text(
                                self._entry.error[:500],
                                size=Theme.FONT_XS,
                                color=Theme.ERROR,
                                font_family="monospace",
                            ),
                            bgcolor=f"{Theme.ERROR}10",
                            border_radius=Theme.RADIUS_SM,
                            padding=Theme.SPACING_XS,
                        ),
                    ],
                    spacing=2,
                )
            )
        elif self._entry.result:
            try:
                result_str = json.dumps(self._entry.result, indent=2)
                if len(result_str) > 500:
                    result_str = result_str[:500] + "\n..."
            except (TypeError, ValueError):
                result_str = str(self._entry.result)[:500]

            detail_rows.append(
                ft.Column(
                    controls=[
                        ft.Text("Result:", size=Theme.FONT_XS, color=Theme.TEXT_MUTED),
                        ft.Container(
                            content=ft.Text(
                                result_str,
                                size=Theme.FONT_XS,
                                color=Theme.TEXT_SECONDARY,
                                font_family="monospace",
                            ),
                            bgcolor=Theme.BG_TERTIARY,
                            border_radius=Theme.RADIUS_SM,
                            padding=Theme.SPACING_XS,
                        ),
                    ],
                    spacing=2,
                )
            )

        return ft.Column(
            controls=detail_rows,
            spacing=Theme.SPACING_SM,
        )

    def _toggle_expand(self, e: ft.ControlEvent) -> None:
        """Toggle expanded state."""
        self._expanded = not self._expanded
        self.content = self._build_content()
        self._safe_update()

    def _safe_update(self) -> None:
        """Safely update the control."""
        try:
            self.update()
        except RuntimeError:
            # Not attached to page yet
            pass


class AuditTrailView(ft.Column):
    """
    Audit trail display with filtering and real-time updates.

    Shows scrollable list of audit entries with risk filter dropdown.
    Supports real-time updates via add_entry() method.
    """

    def __init__(self, session_id: Optional[str] = None):
        """
        Initialize audit trail view.

        Args:
            session_id: Session to display entries for
        """
        super().__init__()
        self._session_id = session_id
        self._filter_risk: Optional[RiskLevel] = None
        self._entries: list[AuditEntry] = []
        self._audit_store = get_audit_store()

        # UI references
        self._filter_dropdown: Optional[ft.Dropdown] = None
        self._list_view: Optional[ft.ListView] = None
        self._summary_row: Optional[ft.Container] = None

        # Column settings
        self.spacing = 0
        self.expand = True

    def build(self) -> None:
        """Build the audit trail layout."""
        # Filter dropdown
        self._filter_dropdown = ft.Dropdown(
            value="all",
            options=[
                ft.dropdown.Option("all", "All"),
                ft.dropdown.Option("safe", "Safe"),
                ft.dropdown.Option("moderate", "Moderate"),
                ft.dropdown.Option("destructive", "Destructive"),
                ft.dropdown.Option("critical", "Critical"),
            ],
            width=110,
            height=32,
            text_size=Theme.FONT_XS,
            border_color=Theme.BORDER,
            bgcolor=Theme.BG_TERTIARY,
            focused_border_color=Theme.PRIMARY,
            on_change=self._on_filter_change,
            content_padding=ft.padding.symmetric(horizontal=8, vertical=4),
        )

        # Refresh button
        refresh_btn = ft.IconButton(
            icon=ft.Icons.REFRESH,
            icon_size=16,
            icon_color=Theme.TEXT_SECONDARY,
            tooltip="Refresh",
            on_click=lambda _: self.refresh(),
        )

        # Header
        header = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Text(
                        "Audit Trail",
                        size=Theme.FONT_SM,
                        weight=ft.FontWeight.W_600,
                        color=Theme.TEXT_PRIMARY,
                    ),
                    ft.Container(expand=True),
                    self._filter_dropdown,
                    refresh_btn,
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.padding.symmetric(
                horizontal=Theme.SPACING_SM,
                vertical=Theme.SPACING_XS,
            ),
        )

        # Entry list
        self._list_view = ft.ListView(
            controls=[],
            spacing=Theme.SPACING_XS,
            padding=ft.padding.symmetric(horizontal=Theme.SPACING_SM),
            auto_scroll=False,
            expand=True,
        )

        # Summary row
        self._summary_row = ft.Container(
            content=ft.Text(
                "No entries",
                size=Theme.FONT_XS,
                color=Theme.TEXT_MUTED,
            ),
            padding=ft.padding.symmetric(
                horizontal=Theme.SPACING_SM,
                vertical=Theme.SPACING_XS,
            ),
            border=ft.border.only(top=ft.BorderSide(1, Theme.BORDER)),
        )

        self.controls = [
            header,
            self._list_view,
            self._summary_row,
        ]

        # Initial load
        if self._session_id:
            self.refresh()

    def _on_filter_change(self, e: ft.ControlEvent) -> None:
        """Handle filter dropdown change."""
        value = e.control.value
        if value == "all":
            self.set_filter(None)
        else:
            self.set_filter(value)  # type: ignore

    def refresh(self) -> None:
        """Query audit store and rebuild entry list."""
        if not self._session_id:
            self._entries = []
        else:
            self._entries = self._audit_store.query(
                session_id=self._session_id,
                risk_level=self._filter_risk,
                limit=100,
            )

        self._rebuild_list()
        self._update_summary()

    def set_session(self, session_id: str) -> None:
        """
        Change session and refresh entries.

        Args:
            session_id: New session ID
        """
        self._session_id = session_id
        self.refresh()

    def set_filter(self, risk_level: Optional[RiskLevel]) -> None:
        """
        Apply risk level filter and refresh.

        Args:
            risk_level: Risk level to filter by (None for all)
        """
        self._filter_risk = risk_level
        self.refresh()

    def add_entry(self, entry: AuditEntry) -> None:
        """
        Add single entry to top of list (real-time update).

        Args:
            entry: AuditEntry to add
        """
        # Check if entry matches current filter
        if self._filter_risk and entry.risk_level != self._filter_risk:
            return

        # Check if entry belongs to current session
        if self._session_id and entry.session_id != self._session_id:
            return

        # Insert at beginning
        self._entries.insert(0, entry)

        # Add row to list view
        if self._list_view:
            row = self._build_entry_row(entry)
            self._list_view.controls.insert(0, row)
            self._safe_update()

        self._update_summary()

    def _build_entry_row(self, entry: AuditEntry) -> AuditEntryRow:
        """Build a row for an audit entry."""
        return AuditEntryRow(entry)

    def _rebuild_list(self) -> None:
        """Rebuild the entire entry list."""
        if not self._list_view:
            return

        self._list_view.controls.clear()
        for entry in self._entries:
            row = self._build_entry_row(entry)
            self._list_view.controls.append(row)

        self._safe_update()

    def _update_summary(self) -> None:
        """Update the summary row with statistics."""
        if not self._summary_row or not self._session_id:
            return

        summary = self._audit_store.get_session_summary(self._session_id)

        total = summary["total_actions"]
        approved = summary["approved"]
        rejected = summary["rejected"]
        duration_ms = summary["total_duration_ms"]

        # Format duration
        if duration_ms >= 1000:
            duration_str = f"{duration_ms/1000:.1f}s"
        else:
            duration_str = f"{duration_ms:.0f}ms"

        summary_text = f"{total} total | {approved} approved | {rejected} rejected | {duration_str}"

        self._summary_row.content = ft.Text(
            summary_text,
            size=Theme.FONT_XS,
            color=Theme.TEXT_MUTED,
        )
        self._safe_update()

    def _safe_update(self) -> None:
        """Safely update the control."""
        try:
            self.update()
        except RuntimeError:
            # Not attached to page yet
            pass
