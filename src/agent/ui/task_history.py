"""
Task History View

Flet UI component for displaying past agent task executions
with replay capability.
"""

from datetime import datetime, timezone
from typing import Callable, Optional

import flet as ft

from src.agent.observability.trace_models import TraceSession
from src.agent.observability.trace_store import TraceStore
from src.ui.theme import Theme


# Status icons for session states
SESSION_STATUS_ICONS = {
    "running": ft.Icons.PLAY_CIRCLE,
    "completed": ft.Icons.CHECK_CIRCLE,
    "failed": ft.Icons.ERROR,
    "cancelled": ft.Icons.CANCEL,
}

SESSION_STATUS_COLORS = {
    "running": Theme.PRIMARY,
    "completed": Theme.SUCCESS,
    "failed": Theme.ERROR,
    "cancelled": Theme.WARNING,
}


def _safe_update(control: ft.Control) -> None:
    """Safely update a control, handling page attachment errors."""
    try:
        control.update()
    except RuntimeError:
        # Control not attached to page yet
        pass


def _format_relative_time(dt: datetime) -> str:
    """Format datetime as relative time string."""
    now = datetime.now(timezone.utc)

    # Ensure dt is timezone-aware
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    delta = now - dt
    seconds = delta.total_seconds()

    if seconds < 60:
        return "Just now"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        return f"{minutes}m ago"
    elif seconds < 86400:
        hours = int(seconds // 3600)
        return f"{hours}h ago"
    elif seconds < 604800:
        days = int(seconds // 86400)
        return f"{days}d ago"
    else:
        return dt.strftime("%b %d, %Y")


def _format_duration(started_at: datetime, completed_at: Optional[datetime]) -> str:
    """Format duration between start and end times."""
    if not completed_at:
        return "Running..."

    # Ensure timezone awareness
    if started_at.tzinfo is None:
        started_at = started_at.replace(tzinfo=timezone.utc)
    if completed_at.tzinfo is None:
        completed_at = completed_at.replace(tzinfo=timezone.utc)

    delta = completed_at - started_at
    seconds = delta.total_seconds()

    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


def _format_cost(cost: Optional[float]) -> str:
    """Format cost as currency string."""
    if cost is None or cost == 0:
        return "$0.00"
    elif cost < 0.01:
        return f"${cost:.4f}"
    else:
        return f"${cost:.2f}"


class TaskSessionRow(ft.Container):
    """
    A single row displaying a TraceSession.

    Shows status icon, task description, timestamp, and optional expand
    for details like token count and cost.
    """

    def __init__(
        self,
        session: TraceSession,
        on_replay: Optional[Callable[[str], None]] = None,
    ):
        """
        Initialize session row.

        Args:
            session: TraceSession to display
            on_replay: Callback when replay button clicked (receives task description)
        """
        self._session = session
        self._on_replay = on_replay
        self._is_expanded = False

        super().__init__(
            content=self._build_content(),
            bgcolor=Theme.BG_TERTIARY,
            border_radius=Theme.RADIUS_MD,
            padding=Theme.SPACING_SM,
            ink=True,
            on_click=self._toggle_expand,
        )

    def _build_content(self) -> ft.Control:
        """Build the row content."""
        status = self._session.status
        icon = SESSION_STATUS_ICONS.get(status, ft.Icons.RADIO_BUTTON_UNCHECKED)
        color = SESSION_STATUS_COLORS.get(status, Theme.TEXT_MUTED)

        # Truncate task description
        task_text = self._session.task
        if len(task_text) > 50:
            task_text = task_text[:47] + "..."

        # Main row
        main_row = ft.Row(
            controls=[
                ft.Icon(icon, size=18, color=color),
                ft.Container(
                    content=ft.Text(
                        task_text,
                        size=Theme.FONT_SM,
                        color=Theme.TEXT_PRIMARY,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                    expand=True,
                ),
                ft.Text(
                    _format_relative_time(self._session.started_at),
                    size=Theme.FONT_XS,
                    color=Theme.TEXT_MUTED,
                ),
                ft.IconButton(
                    icon=ft.Icons.REPLAY,
                    icon_size=16,
                    icon_color=Theme.PRIMARY,
                    tooltip="Replay this task",
                    on_click=self._on_replay_click,
                ),
                ft.Icon(
                    ft.Icons.EXPAND_MORE if not self._is_expanded else ft.Icons.EXPAND_LESS,
                    size=14,
                    color=Theme.TEXT_MUTED,
                ),
            ],
            spacing=Theme.SPACING_SM,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # Build column content
        column_content = [main_row]

        # Expanded details
        if self._is_expanded:
            details = self._build_details()
            if details:
                column_content.append(details)

        return ft.Column(
            controls=column_content,
            spacing=Theme.SPACING_XS,
        )

    def _build_details(self) -> ft.Control:
        """Build expanded details section."""
        details_row = ft.Row(
            controls=[
                # Duration
                ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.TIMER, size=12, color=Theme.TEXT_MUTED),
                        ft.Text(
                            _format_duration(
                                self._session.started_at,
                                self._session.completed_at
                            ),
                            size=Theme.FONT_XS,
                            color=Theme.TEXT_SECONDARY,
                        ),
                    ],
                    spacing=4,
                ),
                # Tokens
                ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.TOKEN, size=12, color=Theme.TEXT_MUTED),
                        ft.Text(
                            f"{self._session.total_tokens:,} tokens",
                            size=Theme.FONT_XS,
                            color=Theme.TEXT_SECONDARY,
                        ),
                    ],
                    spacing=4,
                ),
                # Cost
                ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.ATTACH_MONEY, size=12, color=Theme.TEXT_MUTED),
                        ft.Text(
                            _format_cost(self._session.total_cost_usd),
                            size=Theme.FONT_XS,
                            color=Theme.TEXT_SECONDARY,
                        ),
                    ],
                    spacing=4,
                ),
                # Status badge
                ft.Container(
                    content=ft.Text(
                        self._session.status.upper(),
                        size=10,
                        color=Theme.TEXT_PRIMARY,
                        weight=ft.FontWeight.W_500,
                    ),
                    bgcolor=SESSION_STATUS_COLORS.get(
                        self._session.status, Theme.TEXT_MUTED
                    ),
                    border_radius=Theme.RADIUS_SM,
                    padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                ),
            ],
            spacing=Theme.SPACING_MD,
            wrap=True,
        )

        return ft.Container(
            content=details_row,
            padding=ft.padding.only(left=26, top=Theme.SPACING_XS),
            border=ft.border.only(top=ft.BorderSide(1, Theme.BORDER)),
        )

    def _toggle_expand(self, e: ft.ControlEvent) -> None:
        """Toggle expanded state."""
        self._is_expanded = not self._is_expanded
        self.content = self._build_content()
        _safe_update(self)

    def _on_replay_click(self, e: ft.ControlEvent) -> None:
        """Handle replay button click."""
        e.control.page  # Stop propagation
        if self._on_replay:
            self._on_replay(self._session.task)


class TaskHistoryView(ft.Column):
    """
    View for displaying past agent task executions.

    Shows list of past sessions with:
    - Status icon
    - Task description
    - Timestamp
    - Replay button
    - Expandable details (tokens, cost, duration)

    Supports pagination with "Load more" button.
    """

    PAGE_SIZE = 20

    def __init__(
        self,
        on_replay: Optional[Callable[[str], None]] = None,
        trace_store: Optional[TraceStore] = None,
    ):
        """
        Initialize task history view.

        Args:
            on_replay: Callback when replay clicked (receives task description)
            trace_store: Optional TraceStore instance (creates new one if not provided)
        """
        self._on_replay = on_replay
        self._trace_store = trace_store
        self._sessions: list[TraceSession] = []
        self._offset = 0
        self._has_more = True

        super().__init__(
            controls=self._build_controls(),
            spacing=Theme.SPACING_SM,
            expand=True,
        )

    def _build_controls(self) -> list[ft.Control]:
        """Build view controls."""
        controls = []

        # Header
        header = ft.Row(
            controls=[
                ft.Text(
                    "Recent Tasks",
                    size=Theme.FONT_LG,
                    color=Theme.TEXT_PRIMARY,
                    weight=ft.FontWeight.W_600,
                ),
                ft.Container(expand=True),
                ft.IconButton(
                    icon=ft.Icons.REFRESH,
                    icon_size=18,
                    icon_color=Theme.TEXT_SECONDARY,
                    tooltip="Refresh",
                    on_click=lambda e: self.refresh(),
                ),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        controls.append(header)

        # Session list or empty state
        if not self._sessions:
            controls.append(self._build_empty_state())
        else:
            # Session rows in a ListView for scrolling
            session_list = ft.ListView(
                controls=[
                    TaskSessionRow(session, on_replay=self._on_replay)
                    for session in self._sessions
                ],
                spacing=Theme.SPACING_XS,
                expand=True,
            )
            controls.append(session_list)

            # Load more button
            if self._has_more:
                load_more_btn = ft.TextButton(
                    "Load more",
                    icon=ft.Icons.EXPAND_MORE,
                    on_click=lambda e: self.load_more(),
                )
                controls.append(
                    ft.Container(
                        content=load_more_btn,
                        alignment=ft.Alignment(0, 0),
                    )
                )

        return controls

    def _build_empty_state(self) -> ft.Control:
        """Build empty state content."""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(
                        ft.Icons.HISTORY,
                        size=48,
                        color=Theme.TEXT_MUTED,
                    ),
                    ft.Text(
                        "No tasks yet",
                        size=Theme.FONT_MD,
                        color=Theme.TEXT_SECONDARY,
                    ),
                    ft.Text(
                        "Your agent task history will appear here",
                        size=Theme.FONT_SM,
                        color=Theme.TEXT_MUTED,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=Theme.SPACING_SM,
            ),
            alignment=ft.Alignment(0, 0),
            expand=True,
            padding=Theme.SPACING_XL,
        )

    def _get_trace_store(self) -> TraceStore:
        """Get or create trace store instance."""
        if self._trace_store is None:
            self._trace_store = TraceStore()
        return self._trace_store

    def refresh(self) -> None:
        """Refresh sessions from TraceStore."""
        self._offset = 0
        self._sessions = []

        try:
            store = self._get_trace_store()
            sessions = store.get_sessions(limit=self.PAGE_SIZE, offset=0)
            self._sessions = sessions
            self._has_more = len(sessions) == self.PAGE_SIZE
        except Exception:
            # Gracefully handle database errors
            self._sessions = []
            self._has_more = False

        self.controls = self._build_controls()
        _safe_update(self)

    def load_more(self) -> None:
        """Load more sessions (pagination)."""
        self._offset += self.PAGE_SIZE

        try:
            store = self._get_trace_store()
            new_sessions = store.get_sessions(
                limit=self.PAGE_SIZE,
                offset=self._offset
            )
            self._sessions.extend(new_sessions)
            self._has_more = len(new_sessions) == self.PAGE_SIZE
        except Exception:
            # Gracefully handle database errors
            self._has_more = False

        self.controls = self._build_controls()
        _safe_update(self)

    def _on_replay_click(self, task: str) -> None:
        """Handle replay callback."""
        if self._on_replay:
            self._on_replay(task)

    @property
    def sessions(self) -> list[TraceSession]:
        """Get current sessions list."""
        return self._sessions
