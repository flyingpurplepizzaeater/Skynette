"""
Agent Panel Component

Resizable right sidebar that subscribes to agent events.
"""

from typing import Literal, Optional

import flet as ft

from src.agent.events.emitter import AgentEventEmitter, EventSubscription
from src.agent.models.event import AgentEvent
from src.agent.models.plan import PlanStep, StepStatus
from src.agent.ui.panel_preferences import (
    PanelPreferences,
    get_panel_preferences,
    save_panel_preferences,
)
from src.agent.ui.status_indicator import AgentStatusIndicator
from src.agent.ui.step_views import StepViewSwitcher
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
        self._view_mode_dropdown: Optional[ft.Dropdown] = None
        self._status_indicator: Optional[AgentStatusIndicator] = None
        self._step_view_switcher: Optional[StepViewSwitcher] = None

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

        # View mode dropdown
        self._view_mode_dropdown = ft.Dropdown(
            value=self._prefs.step_view_mode,
            options=[
                ft.dropdown.Option("checklist", "Checklist"),
                ft.dropdown.Option("timeline", "Timeline"),
                ft.dropdown.Option("cards", "Cards"),
            ],
            width=100,
            height=32,
            text_size=Theme.FONT_XS,
            border_color=Theme.BORDER,
            bgcolor=Theme.BG_TERTIARY,
            focused_border_color=Theme.PRIMARY,
            on_change=self._on_view_mode_change,
            content_padding=ft.padding.symmetric(horizontal=8, vertical=4),
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
                self._view_mode_dropdown,
                collapse_with_badge,
            ],
            spacing=Theme.SPACING_SM,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # Status indicator
        self._status_indicator = AgentStatusIndicator(initial_status="idle")

        # Step view switcher (initialized with empty steps)
        self._step_view_switcher = StepViewSwitcher(
            mode=self._prefs.step_view_mode,
            steps=[],
        )

        # Content area with status indicator and step views
        self._content_area = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Container(
                        content=self._status_indicator,
                        padding=ft.padding.only(
                            left=Theme.SPACING_SM,
                            bottom=Theme.SPACING_SM,
                        ),
                    ),
                    self._step_view_switcher,
                    # Placeholder for audit trail (later)
                ],
                spacing=Theme.SPACING_XS,
                expand=True,
            ),
            expand=True,
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

    def _on_view_mode_change(self, e: ft.ControlEvent) -> None:
        """
        Handle view mode dropdown change.

        Args:
            e: Control event with new value
        """
        mode = e.control.value
        if mode in ("checklist", "timeline", "cards"):
            # Update switcher
            if self._step_view_switcher:
                self._step_view_switcher.set_view_mode(mode)

            # Save preference
            self._prefs.step_view_mode = mode  # type: ignore
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

        # Route to specific handlers
        if event.type == "plan_created":
            self._handle_plan_created(event)
        elif event.type == "step_started":
            self._handle_step_started(event)
        elif event.type == "step_completed":
            self._handle_step_completed(event)
        elif event.type == "tool_result":
            self._handle_tool_result(event)

        # Update status indicator
        if self._status_indicator:
            self._status_indicator.update_from_event(event)

    def _handle_plan_created(self, event: AgentEvent) -> None:
        """
        Handle plan_created event.

        Args:
            event: AgentEvent with plan data
        """
        plan_data = event.data.get("plan", {})
        steps_data = plan_data.get("steps", [])

        # Convert step dicts to PlanStep objects
        steps = []
        for step_data in steps_data:
            step = PlanStep(
                id=step_data.get("id", ""),
                description=step_data.get("description", ""),
                tool_name=step_data.get("tool_name"),
                tool_params=step_data.get("tool_params", {}),
                dependencies=step_data.get("dependencies", []),
                status=StepStatus(step_data.get("status", "pending")),
                result=step_data.get("result"),
                error=step_data.get("error"),
            )
            steps.append(step)

        # Update step view
        if self._step_view_switcher:
            self._step_view_switcher.set_steps(steps)

    def _handle_step_started(self, event: AgentEvent) -> None:
        """
        Handle step_started event.

        Args:
            event: AgentEvent with step_id
        """
        step_id = event.data.get("step_id", "")
        if self._step_view_switcher and step_id:
            self._step_view_switcher.update_step(step_id, StepStatus.RUNNING)

    def _handle_step_completed(self, event: AgentEvent) -> None:
        """
        Handle step_completed event.

        Args:
            event: AgentEvent with step_id and result
        """
        step_id = event.data.get("step_id", "")
        if self._step_view_switcher and step_id:
            self._step_view_switcher.update_step(step_id, StepStatus.COMPLETED)

    def _handle_tool_result(self, event: AgentEvent) -> None:
        """
        Handle tool_result event.

        Optionally stores result in the step for display.

        Args:
            event: AgentEvent with step_id and result
        """
        # Tool results are stored on the step by the agent loop
        # The step view will show them when expanded
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
