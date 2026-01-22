"""
Step View Components

Flet UI components for displaying agent plan steps with multiple view modes:
- Checklist: Vertical list with status icons
- Timeline: Stepper with connecting lines
- Cards: Expandable cards with full details
"""

from typing import Optional

import flet as ft

from src.agent.models.plan import PlanStep, StepStatus
from src.ui.theme import Theme


# Status icon mapping for all views
STATUS_ICONS = {
    StepStatus.PENDING: ft.Icons.RADIO_BUTTON_UNCHECKED,
    StepStatus.RUNNING: ft.Icons.PLAY_CIRCLE,
    StepStatus.COMPLETED: ft.Icons.CHECK_CIRCLE,
    StepStatus.FAILED: ft.Icons.ERROR,
    StepStatus.SKIPPED: ft.Icons.SKIP_NEXT,
}

STATUS_COLORS = {
    StepStatus.PENDING: Theme.TEXT_MUTED,
    StepStatus.RUNNING: Theme.PRIMARY,
    StepStatus.COMPLETED: Theme.SUCCESS,
    StepStatus.FAILED: Theme.ERROR,
    StepStatus.SKIPPED: Theme.TEXT_SECONDARY,
}


class StepChecklistView(ft.ListView):
    """
    Vertical scrollable list with status icons for each step.

    Shows step number, description, and status icon.
    Click to expand and show result/error details.
    """

    def __init__(self, steps: list[PlanStep]):
        """
        Initialize checklist view.

        Args:
            steps: List of plan steps to display
        """
        self._steps = list(steps)  # Copy to track updates
        self._expanded_id: Optional[str] = None

        super().__init__(
            controls=self._build_controls(),
            spacing=Theme.SPACING_XS,
            padding=Theme.SPACING_SM,
            auto_scroll=True,
            expand=True,
        )

    def _build_controls(self) -> list[ft.Control]:
        """Build list controls from steps."""
        controls = []
        for i, step in enumerate(self._steps, start=1):
            controls.append(self._build_step_row(i, step))
        return controls

    def _build_step_row(self, number: int, step: PlanStep) -> ft.Container:
        """Build a single step row."""
        is_expanded = self._expanded_id == step.id
        icon = STATUS_ICONS.get(step.status, ft.Icons.RADIO_BUTTON_UNCHECKED)
        color = STATUS_COLORS.get(step.status, Theme.TEXT_MUTED)

        # Main row content
        row_content = ft.Row(
            controls=[
                ft.Icon(icon, size=16, color=color),
                ft.Text(
                    f"{number}.",
                    size=Theme.FONT_SM,
                    color=Theme.TEXT_SECONDARY,
                    weight=ft.FontWeight.W_500,
                ),
                ft.Text(
                    step.description,
                    size=Theme.FONT_SM,
                    color=Theme.TEXT_PRIMARY,
                    expand=True,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
                ft.Icon(
                    ft.Icons.EXPAND_MORE if not is_expanded else ft.Icons.EXPAND_LESS,
                    size=14,
                    color=Theme.TEXT_MUTED,
                ),
            ],
            spacing=Theme.SPACING_SM,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # Build expanded content if applicable
        expanded_content = None
        if is_expanded and (step.result or step.error):
            detail_text = step.error if step.error else str(step.result)
            expanded_content = ft.Container(
                content=ft.Text(
                    detail_text,
                    size=Theme.FONT_XS,
                    color=Theme.ERROR if step.error else Theme.TEXT_SECONDARY,
                    selectable=True,
                ),
                padding=ft.padding.only(left=32, top=Theme.SPACING_XS),
            )

        # Column for row + expansion
        column_controls = [row_content]
        if expanded_content:
            column_controls.append(expanded_content)

        return ft.Container(
            content=ft.Column(
                controls=column_controls,
                spacing=0,
            ),
            padding=ft.padding.symmetric(
                horizontal=Theme.SPACING_XS,
                vertical=Theme.SPACING_XS,
            ),
            border_radius=Theme.RADIUS_SM,
            ink=True,
            on_click=lambda e, sid=step.id: self._toggle_expand(sid),
            bgcolor=Theme.BG_TERTIARY if is_expanded else None,
        )

    def _toggle_expand(self, step_id: str) -> None:
        """Toggle expansion of a step."""
        if self._expanded_id == step_id:
            self._expanded_id = None
        else:
            self._expanded_id = step_id
        self.controls = self._build_controls()
        self.update()

    def update_step(self, step_id: str, status: StepStatus) -> None:
        """
        Update a specific step's status.

        Args:
            step_id: ID of step to update
            status: New status value
        """
        for step in self._steps:
            if step.id == step_id:
                step.status = status
                break
        self.controls = self._build_controls()
        self.update()

    def set_steps(self, steps: list[PlanStep]) -> None:
        """
        Replace all steps.

        Args:
            steps: New list of steps
        """
        self._steps = list(steps)
        self._expanded_id = None
        self.controls = self._build_controls()
        self.update()


class StepTimelineView(ft.Column):
    """
    Stepper-style view with connecting lines between steps.

    Each step has a circular badge with number, status indicator,
    and description below.
    """

    def __init__(self, steps: list[PlanStep]):
        """
        Initialize timeline view.

        Args:
            steps: List of plan steps to display
        """
        self._steps = list(steps)

        super().__init__(
            controls=self._build_controls(),
            spacing=0,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    def _build_controls(self) -> list[ft.Control]:
        """Build timeline controls."""
        controls = []
        for i, step in enumerate(self._steps):
            is_last = i == len(self._steps) - 1
            controls.append(self._build_step_item(i + 1, step, is_last))
        return controls

    def _build_step_item(
        self, number: int, step: PlanStep, is_last: bool
    ) -> ft.Container:
        """Build a single timeline step."""
        color = STATUS_COLORS.get(step.status, Theme.TEXT_MUTED)
        is_running = step.status == StepStatus.RUNNING
        is_completed = step.status == StepStatus.COMPLETED

        # Step badge (circle with number or checkmark)
        if is_completed:
            badge_content = ft.Icon(
                ft.Icons.CHECK,
                size=12,
                color=Theme.TEXT_PRIMARY,
            )
        else:
            badge_content = ft.Text(
                str(number),
                size=Theme.FONT_XS,
                color=Theme.TEXT_PRIMARY if is_running else color,
                weight=ft.FontWeight.W_600,
            )

        badge = ft.Container(
            content=badge_content,
            width=24,
            height=24,
            border_radius=12,
            bgcolor=color if (is_running or is_completed) else None,
            border=ft.border.all(2, color),
            alignment=ft.alignment.center,
        )

        # Pulsing animation container for running step
        if is_running:
            badge = ft.Container(
                content=badge,
                animate=ft.animation.Animation(500, ft.AnimationCurve.EASE_IN_OUT),
            )

        # Connecting line (not for last step)
        line = ft.Container(
            width=2,
            height=24,
            bgcolor=color if is_completed else Theme.BORDER,
            margin=ft.margin.only(left=11),  # Center under badge
        ) if not is_last else ft.Container(height=4)

        # Step description
        description = ft.Text(
            step.description,
            size=Theme.FONT_SM,
            color=Theme.TEXT_PRIMARY if is_running else Theme.TEXT_SECONDARY,
            overflow=ft.TextOverflow.ELLIPSIS,
            max_lines=2,
        )

        # Layout: badge + description side by side
        row = ft.Row(
            controls=[
                badge,
                ft.Container(
                    content=description,
                    expand=True,
                    padding=ft.padding.only(left=Theme.SPACING_SM),
                ),
            ],
            vertical_alignment=ft.CrossAxisAlignment.START,
        )

        return ft.Column(
            controls=[
                ft.Container(content=row, padding=Theme.SPACING_XS),
                line,
            ],
            spacing=0,
        )

    def update_step(self, step_id: str, status: StepStatus) -> None:
        """
        Update a specific step's status.

        Args:
            step_id: ID of step to update
            status: New status value
        """
        for step in self._steps:
            if step.id == step_id:
                step.status = status
                break
        self.controls = self._build_controls()
        self.update()

    def set_steps(self, steps: list[PlanStep]) -> None:
        """
        Replace all steps.

        Args:
            steps: New list of steps
        """
        self._steps = list(steps)
        self.controls = self._build_controls()
        self.update()


class StepCardsView(ft.ListView):
    """
    Expandable cards view for detailed step information.

    Collapsed shows icon, description, and status badge.
    Expanded shows tool name, parameters, and result.
    """

    def __init__(self, steps: list[PlanStep]):
        """
        Initialize cards view.

        Args:
            steps: List of plan steps to display
        """
        self._steps = list(steps)
        self._expanded_ids: set[str] = set()

        super().__init__(
            controls=self._build_controls(),
            spacing=Theme.SPACING_SM,
            padding=Theme.SPACING_SM,
            expand=True,
        )

    def _build_controls(self) -> list[ft.Control]:
        """Build card controls."""
        controls = []
        for i, step in enumerate(self._steps, start=1):
            controls.append(self._build_card(i, step))
        return controls

    def _build_card(self, number: int, step: PlanStep) -> ft.Container:
        """Build a single step card."""
        is_expanded = step.id in self._expanded_ids
        icon = STATUS_ICONS.get(step.status, ft.Icons.RADIO_BUTTON_UNCHECKED)
        color = STATUS_COLORS.get(step.status, Theme.TEXT_MUTED)

        # Status badge
        status_badge = ft.Container(
            content=ft.Text(
                step.status.value.upper(),
                size=10,
                color=Theme.TEXT_PRIMARY,
                weight=ft.FontWeight.W_500,
            ),
            bgcolor=color,
            border_radius=Theme.RADIUS_SM,
            padding=ft.padding.symmetric(horizontal=6, vertical=2),
        )

        # Header row
        header = ft.Row(
            controls=[
                ft.Icon(icon, size=18, color=color),
                ft.Text(
                    f"Step {number}",
                    size=Theme.FONT_SM,
                    color=Theme.TEXT_SECONDARY,
                    weight=ft.FontWeight.W_500,
                ),
                ft.Container(expand=True),
                status_badge,
                ft.Icon(
                    ft.Icons.EXPAND_MORE if not is_expanded else ft.Icons.EXPAND_LESS,
                    size=16,
                    color=Theme.TEXT_MUTED,
                ),
            ],
            spacing=Theme.SPACING_SM,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # Description
        description = ft.Text(
            step.description,
            size=Theme.FONT_SM,
            color=Theme.TEXT_PRIMARY,
        )

        card_content = [header, description]

        # Expanded details
        if is_expanded:
            details = []

            # Tool name
            if step.tool_name:
                details.append(
                    ft.Row(
                        controls=[
                            ft.Text("Tool:", size=Theme.FONT_XS, color=Theme.TEXT_MUTED),
                            ft.Text(
                                step.tool_name,
                                size=Theme.FONT_XS,
                                color=Theme.PRIMARY,
                                weight=ft.FontWeight.W_500,
                            ),
                        ],
                        spacing=Theme.SPACING_XS,
                    )
                )

            # Tool params (if any)
            if step.tool_params:
                params_text = ", ".join(
                    f"{k}={v}" for k, v in list(step.tool_params.items())[:3]
                )
                if len(step.tool_params) > 3:
                    params_text += "..."
                details.append(
                    ft.Text(
                        f"Params: {params_text}",
                        size=Theme.FONT_XS,
                        color=Theme.TEXT_MUTED,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    )
                )

            # Result or error
            if step.error:
                details.append(
                    ft.Container(
                        content=ft.Text(
                            f"Error: {step.error}",
                            size=Theme.FONT_XS,
                            color=Theme.ERROR,
                            selectable=True,
                        ),
                        padding=ft.padding.only(top=Theme.SPACING_XS),
                    )
                )
            elif step.result:
                result_str = str(step.result)[:200]
                if len(str(step.result)) > 200:
                    result_str += "..."
                details.append(
                    ft.Container(
                        content=ft.Text(
                            f"Result: {result_str}",
                            size=Theme.FONT_XS,
                            color=Theme.TEXT_SECONDARY,
                            selectable=True,
                        ),
                        padding=ft.padding.only(top=Theme.SPACING_XS),
                    )
                )

            if details:
                card_content.append(
                    ft.Container(
                        content=ft.Column(
                            controls=details,
                            spacing=Theme.SPACING_XS,
                        ),
                        padding=ft.padding.only(top=Theme.SPACING_SM),
                        border=ft.border.only(top=ft.BorderSide(1, Theme.BORDER)),
                    )
                )

        return ft.Container(
            content=ft.Column(
                controls=card_content,
                spacing=Theme.SPACING_XS,
            ),
            bgcolor=Theme.BG_TERTIARY,
            border_radius=Theme.RADIUS_MD,
            padding=Theme.SPACING_SM,
            ink=True,
            on_click=lambda e, sid=step.id: self._toggle_expand(sid),
        )

    def _toggle_expand(self, step_id: str) -> None:
        """Toggle expansion of a card."""
        if step_id in self._expanded_ids:
            self._expanded_ids.discard(step_id)
        else:
            self._expanded_ids.add(step_id)
        self.controls = self._build_controls()
        self.update()

    def update_step(self, step_id: str, status: StepStatus) -> None:
        """
        Update a specific step's status.

        Args:
            step_id: ID of step to update
            status: New status value
        """
        for step in self._steps:
            if step.id == step_id:
                step.status = status
                break
        self.controls = self._build_controls()
        self.update()

    def set_steps(self, steps: list[PlanStep]) -> None:
        """
        Replace all steps.

        Args:
            steps: New list of steps
        """
        self._steps = list(steps)
        self._expanded_ids.clear()
        self.controls = self._build_controls()
        self.update()


class StepViewSwitcher(ft.AnimatedSwitcher):
    """
    Animated switcher between step view modes.

    Provides fade transition when switching between checklist,
    timeline, and cards views.
    """

    VIEW_MODES = ("checklist", "timeline", "cards")

    def __init__(self, mode: str, steps: list[PlanStep]):
        """
        Initialize view switcher.

        Args:
            mode: Initial view mode (checklist, timeline, or cards)
            steps: List of plan steps to display
        """
        self._mode = mode if mode in self.VIEW_MODES else "checklist"
        self._steps = list(steps)

        super().__init__(
            content=self._create_view(self._mode),
            duration=200,
            transition=ft.AnimatedSwitcherTransition.FADE,
            switch_in_curve=ft.AnimationCurve.EASE_OUT,
            switch_out_curve=ft.AnimationCurve.EASE_IN,
            expand=True,
        )

    def _create_view(self, mode: str) -> ft.Control:
        """Create view for the specified mode."""
        if mode == "timeline":
            return StepTimelineView(self._steps)
        elif mode == "cards":
            return StepCardsView(self._steps)
        else:  # default to checklist
            return StepChecklistView(self._steps)

    def set_view_mode(self, mode: str, steps: Optional[list[PlanStep]] = None) -> None:
        """
        Switch to a different view mode with animation.

        Args:
            mode: View mode (checklist, timeline, or cards)
            steps: Optional new steps list (uses existing if not provided)
        """
        if mode not in self.VIEW_MODES:
            mode = "checklist"

        self._mode = mode
        if steps is not None:
            self._steps = list(steps)

        self.content = self._create_view(self._mode)
        self.update()

    def update_step(self, step_id: str, status: StepStatus) -> None:
        """
        Update a specific step's status in the current view.

        Args:
            step_id: ID of step to update
            status: New status value
        """
        # Update internal steps list
        for step in self._steps:
            if step.id == step_id:
                step.status = status
                break

        # Update the current view
        if self.content and hasattr(self.content, "update_step"):
            self.content.update_step(step_id, status)

    def set_steps(self, steps: list[PlanStep]) -> None:
        """
        Replace all steps in the current view.

        Args:
            steps: New list of steps
        """
        self._steps = list(steps)
        if self.content and hasattr(self.content, "set_steps"):
            self.content.set_steps(steps)

    @property
    def current_mode(self) -> str:
        """Get current view mode."""
        return self._mode

    @property
    def steps(self) -> list[PlanStep]:
        """Get current steps list."""
        return self._steps
