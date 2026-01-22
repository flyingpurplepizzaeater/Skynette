"""
Agent Panel Component

Resizable right sidebar that subscribes to agent events.
"""

from typing import Optional

import flet as ft

from src.agent.events.emitter import AgentEventEmitter, EventSubscription
from src.agent.models.event import AgentEvent
from src.agent.ui.panel_preferences import (
    PanelPreferences,
    get_panel_preferences,
    save_panel_preferences,
)
from src.ui.theme import Theme


class AgentPanel(ft.Row):
    """
    Resizable right sidebar for agent interaction.

    Subscribes to AgentEventEmitter and displays agent state.
    Panel width and visibility persist across sessions.
    Badge indicator shows when collapsed and events pending.
    """

    MIN_WIDTH = 280
    MAX_WIDTH = 600
    DEFAULT_WIDTH = 350

    def __init__(self, page: ft.Page):
        """
        Initialize the agent panel.

        Args:
            page: Flet page for UI updates
        """
        super().__init__()
        self._page = page
        self._subscription: Optional[EventSubscription] = None
        self._badge_count: int = 0

        # Load preferences
        self._prefs = get_panel_preferences()
        self._width = self._prefs.width
        self._visible = self._prefs.visible

        # UI references (set in build)
        self._content_container: Optional[ft.Container] = None
        self._content_area: Optional[ft.Container] = None
        self._header: Optional[ft.Row] = None
        self._collapse_button: Optional[ft.IconButton] = None
        self._badge_indicator: Optional[ft.Container] = None
        self._divider_container: Optional[ft.Container] = None

        # Row settings
        self.expand = False
        self.spacing = 0
        self.visible = self._visible

    def build(self) -> None:
        """Build the panel layout with divider and content."""
        # Divider for drag resize (4px wide on left edge)
        divider = ft.GestureDetector(
            content=ft.Container(
                width=4,
                bgcolor=Theme.BORDER,
                expand=True,
            ),
            on_horizontal_drag_update=self._on_drag_update,
            mouse_cursor=ft.MouseCursor.RESIZE_LEFT_RIGHT,
        )
        self._divider_container = ft.Container(
            content=divider,
            height=float("inf"),
        )

        # Badge indicator (shown when collapsed with pending events)
        self._badge_indicator = ft.Container(
            content=ft.Text(
                str(self._badge_count),
                size=10,
                color=Theme.TEXT_PRIMARY,
                text_align=ft.TextAlign.CENTER,
            ),
            bgcolor=Theme.ERROR,
            border_radius=8,
            width=16,
            height=16,
            alignment=ft.alignment.center,
            visible=False,
        )

        # Collapse button with badge stack
        self._collapse_button = ft.IconButton(
            icon=ft.Icons.CHEVRON_RIGHT,
            icon_size=18,
            icon_color=Theme.TEXT_SECONDARY,
            tooltip="Collapse panel",
            on_click=lambda _: self.toggle_visibility(),
        )

        collapse_with_badge = ft.Stack(
            controls=[
                self._collapse_button,
                ft.Container(
                    content=self._badge_indicator,
                    right=0,
                    top=0,
                ),
            ],
            width=36,
            height=36,
        )

        # Header row
        self._header = ft.Row(
            controls=[
                ft.Icon(ft.Icons.SMART_TOY, size=18, color=Theme.PRIMARY),
                ft.Text(
                    "Agent",
                    size=Theme.FONT_MD,
                    weight=ft.FontWeight.W_600,
                    color=Theme.TEXT_PRIMARY,
                ),
                ft.Container(expand=True),  # Spacer
                collapse_with_badge,
            ],
            spacing=Theme.SPACING_SM,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # Content area (placeholder for step/plan views)
        self._content_area = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "Agent panel ready",
                        color=Theme.TEXT_SECONDARY,
                        size=Theme.FONT_SM,
                    ),
                ],
                spacing=Theme.SPACING_SM,
                expand=True,
            ),
            expand=True,
            padding=Theme.SPACING_SM,
        )

        # Main content container
        self._content_container = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Container(
                        content=self._header,
                        padding=ft.padding.only(
                            left=Theme.SPACING_SM,
                            right=Theme.SPACING_XS,
                            top=Theme.SPACING_SM,
                            bottom=Theme.SPACING_XS,
                        ),
                        border=ft.border.only(bottom=ft.BorderSide(1, Theme.BORDER)),
                    ),
                    self._content_area,
                ],
                spacing=0,
                expand=True,
            ),
            width=self._width,
            bgcolor=Theme.BG_SECONDARY,
            border=ft.border.only(left=ft.BorderSide(1, Theme.BORDER)),
        )

        self.controls = [
            self._divider_container,
            self._content_container,
        ]

    def _on_drag_update(self, e: ft.DragUpdateEvent) -> None:
        """
        Handle drag to resize panel.

        For right sidebar: moving left (negative delta_x) increases width.
        """
        # Invert delta for right sidebar
        new_width = self._width - e.delta_x
        new_width = max(self.MIN_WIDTH, min(self.MAX_WIDTH, new_width))

        if int(new_width) != self._width:
            self._width = int(new_width)
            if self._content_container:
                self._content_container.width = self._width
                self._content_container.update()

            # Save preference
            self._prefs.width = self._width
            save_panel_preferences(self._prefs)

    def toggle_visibility(self) -> None:
        """Toggle panel visibility and save preference."""
        self.set_visible(not self._visible)

    def set_visible(self, visible: bool) -> None:
        """
        Set panel visibility explicitly.

        Args:
            visible: Whether panel should be visible
        """
        self._visible = visible
        self.visible = visible

        # Clear badge when expanded
        if visible:
            self._clear_badge()

        # Save preference
        self._prefs.visible = visible
        save_panel_preferences(self._prefs)

        self.update()

    def start_listening(self, emitter: AgentEventEmitter) -> None:
        """
        Subscribe to event emitter and start event loop.

        Args:
            emitter: AgentEventEmitter to subscribe to
        """
        if self._subscription:
            self._subscription.close()

        self._subscription = emitter.subscribe(maxsize=100)

    def stop_listening(self) -> None:
        """Close the event subscription."""
        if self._subscription:
            self._subscription.close()
            self._subscription = None

    async def _event_loop(self) -> None:
        """
        Async event processing loop.

        Routes events to appropriate handlers.
        """
        if not self._subscription:
            return

        async for event in self._subscription:
            self._handle_event(event)
            self._page.update()

    def _handle_event(self, event: AgentEvent) -> None:
        """
        Route event to appropriate handler.

        Args:
            event: AgentEvent to process
        """
        # If panel collapsed, increment badge for relevant events
        if not self._visible:
            if event.type in (
                "step_started",
                "step_completed",
                "approval_requested",
                "error",
            ):
                self._increment_badge()

        # Placeholder handlers - will be implemented by child views
        # For now, just process terminal events
        if event.type in ("completed", "cancelled", "error"):
            # Terminal events handled by subscription auto-close
            pass

    def _increment_badge(self) -> None:
        """Increment badge count and update visibility."""
        self._badge_count += 1
        if self._badge_indicator:
            self._badge_indicator.visible = True
            text = self._badge_indicator.content
            if isinstance(text, ft.Text):
                text.value = str(min(self._badge_count, 99))  # Cap at 99
            self._badge_indicator.update()

    def _clear_badge(self) -> None:
        """Reset badge count to 0."""
        self._badge_count = 0
        if self._badge_indicator:
            self._badge_indicator.visible = False
            text = self._badge_indicator.content
            if isinstance(text, ft.Text):
                text.value = "0"
            self._badge_indicator.update()

    @property
    def width(self) -> int:
        """Get current panel width."""
        return self._width

    @property
    def is_visible(self) -> bool:
        """Get current visibility state."""
        return self._visible

    @property
    def subscription(self) -> Optional[EventSubscription]:
        """Get current event subscription."""
        return self._subscription
