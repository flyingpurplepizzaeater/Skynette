"""
Agent Status Indicator

Flet UI component for displaying agent execution status with animation
and step progress.
"""

from typing import Optional

import flet as ft

from src.agent.events.emitter import AgentEventEmitter, EventSubscription
from src.agent.models.event import AgentEvent
from src.ui.theme import Theme


class AgentStatusIndicator(ft.Row):
    """
    Visual indicator for agent execution status.

    Shows animated spinner for active states, static icons for idle/complete,
    and step progress during execution.
    """

    STATUS_CONFIG: dict = {
        "idle": {
            "icon": ft.Icons.PENDING_OUTLINED,
            "color": Theme.TEXT_MUTED,
            "animate": False,
            "text": "Ready",
        },
        "planning": {
            "icon": ft.Icons.AUTO_AWESOME,
            "color": Theme.PRIMARY,
            "animate": True,
            "text": "Planning...",
        },
        "executing": {
            "icon": ft.Icons.PLAY_ARROW,
            "color": Theme.SECONDARY,
            "animate": True,
            "text": "Executing...",
        },
        "awaiting_tool": {
            "icon": ft.Icons.BUILD,
            "color": Theme.INFO,
            "animate": True,
            "text": "Running tool...",
        },
        "awaiting_approval": {
            "icon": ft.Icons.PAUSE,
            "color": Theme.WARNING,
            "animate": False,
            "text": "Waiting for approval",
        },
        "completed": {
            "icon": ft.Icons.CHECK_CIRCLE,
            "color": Theme.SUCCESS,
            "animate": False,
            "text": "Completed",
        },
        "failed": {
            "icon": ft.Icons.ERROR,
            "color": Theme.ERROR,
            "animate": False,
            "text": "Failed",
        },
        "cancelled": {
            "icon": ft.Icons.CANCEL,
            "color": Theme.WARNING,
            "animate": False,
            "text": "Cancelled",
        },
    }

    def __init__(self, initial_status: str = "idle"):
        self.current_status = initial_status
        self.current_step: int = 0
        self.total_steps: int = 0
        self._detail: Optional[str] = None
        self._subscription: Optional[EventSubscription] = None

        config = self.STATUS_CONFIG.get(initial_status, self.STATUS_CONFIG["idle"])

        # UI components
        self._progress_ring = ft.ProgressRing(
            width=16,
            height=16,
            stroke_width=2,
            color=config["color"],
            visible=config["animate"],
        )

        self._icon = ft.Icon(
            config["icon"],
            size=16,
            color=config["color"],
            visible=not config["animate"],
        )

        self._status_text = ft.Text(
            value=self._format_status_text(),
            size=Theme.FONT_SM,
            color=config["color"],
        )

        super().__init__(
            controls=[
                ft.Stack(
                    controls=[self._progress_ring, self._icon],
                    width=16,
                    height=16,
                ),
                self._status_text,
            ],
            spacing=Theme.SPACING_SM,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def update_status(self, status: str, detail: Optional[str] = None):
        """
        Update the displayed status.

        Args:
            status: New status key (must be in STATUS_CONFIG)
            detail: Optional detail text to show instead of default
        """
        if status not in self.STATUS_CONFIG:
            status = "idle"

        self.current_status = status
        self._detail = detail
        config = self.STATUS_CONFIG[status]

        if self._progress_ring:
            self._progress_ring.visible = config["animate"]
            self._progress_ring.color = config["color"]

        if self._icon:
            self._icon.visible = not config["animate"]
            self._icon.icon = config["icon"]
            self._icon.color = config["color"]

        if self._status_text:
            self._status_text.value = self._format_status_text()
            self._status_text.color = config["color"]

    def set_step_progress(self, current: int, total: int):
        """
        Set the step progress display.

        Args:
            current: Current step number (1-indexed)
            total: Total number of steps
        """
        self.current_step = current
        self.total_steps = total

        if self._status_text:
            self._status_text.value = self._format_status_text()

    def update_from_event(self, event: AgentEvent):
        """
        Update status based on an agent event.

        Args:
            event: AgentEvent to process
        """
        event_type = event.type
        data = event.data

        if event_type == "state_change":
            state = data.get("state", "idle")
            self.update_status(state)

        elif event_type == "plan_created":
            plan = data.get("plan", {})
            steps = plan.get("steps", [])
            self.total_steps = len(steps)
            self.current_step = 0

        elif event_type == "step_started":
            self.current_step += 1
            description = data.get("description", "")
            self.update_status("executing", description)

        elif event_type == "tool_called":
            tool_name = data.get("tool_name", "tool")
            self.update_status("awaiting_tool", f"Running {tool_name}...")

        elif event_type == "completed":
            self.update_status("completed")

        elif event_type == "error":
            self.update_status("failed", data.get("message", "Error"))

        elif event_type == "cancelled":
            self.update_status("cancelled")

    def subscribe_to_emitter(self, emitter: AgentEventEmitter) -> EventSubscription:
        """
        Subscribe to an event emitter for automatic updates.

        Args:
            emitter: AgentEventEmitter to subscribe to

        Returns:
            EventSubscription for lifecycle management
        """
        self._subscription = emitter.subscribe()

        # Note: The caller should iterate over the subscription in an async context
        # and call update_from_event for each event
        return self._subscription

    def unsubscribe(self):
        """Close the current subscription if any."""
        if self._subscription:
            self._subscription.close()
            self._subscription = None

    def _format_status_text(self) -> str:
        """
        Format the status text based on current state.

        Returns:
            Formatted status string with step progress if applicable
        """
        if self._detail:
            base_text = self._detail
        else:
            config = self.STATUS_CONFIG.get(self.current_status, self.STATUS_CONFIG["idle"])
            base_text = config["text"]

        # Add step progress for executing state
        if self.current_status == "executing" and self.total_steps > 0:
            return f"{base_text} (Step {self.current_step} of {self.total_steps})"

        return base_text
