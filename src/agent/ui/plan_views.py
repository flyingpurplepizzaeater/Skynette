"""
Plan View Components

Visualizations for agent execution plans.
Supports list and tree views with dependency visualization.
"""

from typing import Optional

import flet as ft

from src.agent.models.plan import AgentPlan, PlanStep, StepStatus
from src.ui.theme import Theme


# Tool icons based on tool name patterns
TOOL_ICONS = {
    "code": ft.Icons.CODE,
    "python": ft.Icons.CODE,
    "execute": ft.Icons.PLAY_ARROW,
    "file": ft.Icons.FOLDER,
    "read": ft.Icons.DESCRIPTION,
    "write": ft.Icons.EDIT,
    "search": ft.Icons.SEARCH,
    "browser": ft.Icons.WEB,
    "shell": ft.Icons.TERMINAL,
    "bash": ft.Icons.TERMINAL,
    "git": ft.Icons.SOURCE,
    "github": ft.Icons.SOURCE,
    "rag": ft.Icons.STORAGE,
    "mcp": ft.Icons.EXTENSION,
}


def _get_tool_icon(tool_name: Optional[str]) -> Optional[str]:
    """Get icon for tool based on name."""
    if not tool_name:
        return None

    tool_lower = tool_name.lower()
    for key, icon in TOOL_ICONS.items():
        if key in tool_lower:
            return icon

    return ft.Icons.BUILD  # Default tool icon


def _get_status_color(status: StepStatus) -> str:
    """Get color for step status."""
    status_colors = {
        StepStatus.PENDING: Theme.TEXT_MUTED,
        StepStatus.RUNNING: Theme.PRIMARY,
        StepStatus.COMPLETED: Theme.SUCCESS,
        StepStatus.FAILED: Theme.ERROR,
        StepStatus.SKIPPED: Theme.WARNING,
    }
    return status_colors.get(status, Theme.TEXT_MUTED)


def _safe_update(control: ft.Control) -> None:
    """Safely call update on a control, handling unattached controls."""
    try:
        control.update()
    except RuntimeError:
        # Control not attached to a page yet
        pass


class PlanHeader(ft.Container):
    """
    Header component showing plan overview.

    Displays plan overview text, task name, and step count.
    """

    def __init__(self, plan: Optional[AgentPlan] = None):
        """
        Initialize plan header.

        Args:
            plan: The agent plan to display
        """
        self._plan = plan
        content = self._build_content()

        super().__init__(
            content=content,
            bgcolor=Theme.BG_TERTIARY,
            border_radius=Theme.RADIUS_MD,
            padding=Theme.SPACING_SM,
        )

    def _build_content(self) -> ft.Control:
        """Build header content."""
        if not self._plan:
            return ft.Text(
                "No plan loaded",
                color=Theme.TEXT_MUTED,
                size=Theme.FONT_SM,
            )

        step_count = len(self._plan.steps)

        return ft.Column(
            controls=[
                ft.Text(
                    self._plan.task,
                    color=Theme.TEXT_PRIMARY,
                    size=Theme.FONT_MD,
                    weight=ft.FontWeight.W_600,
                    max_lines=2,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
                ft.Container(height=Theme.SPACING_XS),
                ft.Text(
                    self._plan.overview,
                    color=Theme.TEXT_SECONDARY,
                    size=Theme.FONT_SM,
                    max_lines=3,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
                ft.Container(height=Theme.SPACING_XS),
                ft.Row(
                    controls=[
                        ft.Icon(
                            ft.Icons.LIST_ALT,
                            size=14,
                            color=Theme.TEXT_MUTED,
                        ),
                        ft.Text(
                            f"{step_count} step{'s' if step_count != 1 else ''}",
                            color=Theme.TEXT_MUTED,
                            size=Theme.FONT_XS,
                        ),
                    ],
                    spacing=Theme.SPACING_XS,
                ),
            ],
            spacing=0,
        )

    def set_plan(self, plan: AgentPlan) -> None:
        """Update the displayed plan."""
        self._plan = plan
        self.content = self._build_content()
        _safe_update(self)


class PlanListView(ft.Column):
    """
    List view of plan steps.

    Shows numbered list with step descriptions, tool icons,
    and dependency indicators.
    """

    def __init__(self, plan: Optional[AgentPlan] = None):
        """
        Initialize list view.

        Args:
            plan: The agent plan to display
        """
        self._plan = plan
        self._step_rows: dict[str, ft.Container] = {}

        super().__init__(
            spacing=Theme.SPACING_SM,
            expand=True,
        )

        self._build()

    def _build(self) -> None:
        """Build the list view."""
        self.controls = []
        self._step_rows = {}

        # Header
        header = PlanHeader(self._plan)
        self.controls.append(header)

        if not self._plan or not self._plan.steps:
            self.controls.append(
                ft.Container(
                    content=ft.Text(
                        "No steps in plan",
                        color=Theme.TEXT_MUTED,
                        size=Theme.FONT_SM,
                    ),
                    padding=Theme.SPACING_MD,
                )
            )
            return

        # Step list
        list_view = ft.ListView(
            spacing=Theme.SPACING_XS,
            expand=True,
            padding=ft.Padding.only(top=Theme.SPACING_SM),
        )

        for i, step in enumerate(self._plan.steps, 1):
            row = self._create_step_row(step, i)
            self._step_rows[step.id] = row
            list_view.controls.append(row)

        self.controls.append(list_view)

    def _create_step_row(self, step: PlanStep, number: int) -> ft.Container:
        """Create a row for a step."""
        status_color = _get_status_color(step.status)
        tool_icon = _get_tool_icon(step.tool_name)
        has_deps = bool(step.dependencies)

        # Number badge
        number_badge = ft.Container(
            content=ft.Text(
                str(number),
                size=Theme.FONT_XS,
                color=Theme.TEXT_PRIMARY,
                text_align=ft.TextAlign.CENTER,
            ),
            width=20,
            height=20,
            border_radius=10,
            bgcolor=status_color,
            alignment=ft.Alignment(0, 0),
        )

        # Description
        description = ft.Text(
            step.description,
            color=Theme.TEXT_PRIMARY,
            size=Theme.FONT_SM,
            expand=True,
            max_lines=2,
            overflow=ft.TextOverflow.ELLIPSIS,
        )

        # Icons row
        icons = []
        if tool_icon:
            icons.append(
                ft.Icon(
                    tool_icon,
                    size=14,
                    color=Theme.TEXT_MUTED,
                    tooltip=step.tool_name,
                )
            )
        if has_deps:
            icons.append(
                ft.Icon(
                    ft.Icons.LINK,
                    size=12,
                    color=Theme.TEXT_MUTED,
                    tooltip=f"Depends on: {', '.join(step.dependencies[:3])}{'...' if len(step.dependencies) > 3 else ''}",
                )
            )

        row_content = ft.Row(
            controls=[
                number_badge,
                description,
                *icons,
            ],
            spacing=Theme.SPACING_SM,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        return ft.Container(
            content=row_content,
            padding=ft.Padding.symmetric(
                horizontal=Theme.SPACING_SM,
                vertical=Theme.SPACING_XS,
            ),
            border_radius=Theme.RADIUS_SM,
            bgcolor=Theme.BG_SECONDARY,
            data=step.id,  # Store step ID for updates
        )

    def set_plan(self, plan: AgentPlan) -> None:
        """Replace the displayed plan."""
        self._plan = plan
        self._build()
        _safe_update(self)

    def update_step_status(self, step_id: str, status: StepStatus) -> None:
        """
        Update visual for a specific step.

        Args:
            step_id: ID of step to update
            status: New status
        """
        if step_id not in self._step_rows:
            return

        row = self._step_rows[step_id]
        status_color = _get_status_color(status)

        # Find and update the number badge
        if isinstance(row.content, ft.Row) and row.content.controls:
            badge = row.content.controls[0]
            if isinstance(badge, ft.Container):
                badge.bgcolor = status_color
                _safe_update(badge)


class PlanTreeView(ft.Column):
    """
    Tree view of plan steps showing dependencies.

    Root nodes are steps without dependencies.
    Child nodes are steps that depend on parent.
    """

    def __init__(self, plan: Optional[AgentPlan] = None):
        """
        Initialize tree view.

        Args:
            plan: The agent plan to display
        """
        self._plan = plan
        self._step_rows: dict[str, ft.Container] = {}
        self._roots: list[PlanStep] = []

        super().__init__(
            spacing=Theme.SPACING_SM,
            expand=True,
        )

        self._build()

    def _build(self) -> None:
        """Build the tree view."""
        self.controls = []
        self._step_rows = {}
        self._roots = []

        # Header
        header = PlanHeader(self._plan)
        self.controls.append(header)

        if not self._plan or not self._plan.steps:
            self.controls.append(
                ft.Container(
                    content=ft.Text(
                        "No steps in plan",
                        color=Theme.TEXT_MUTED,
                        size=Theme.FONT_SM,
                    ),
                    padding=Theme.SPACING_MD,
                )
            )
            return

        # Build tree structure
        tree_controls = self._build_tree(self._plan.steps)

        # Tree scroll view
        list_view = ft.ListView(
            controls=tree_controls,
            spacing=Theme.SPACING_XS,
            expand=True,
            padding=ft.Padding.only(top=Theme.SPACING_SM),
        )

        self.controls.append(list_view)

    def _build_tree(self, steps: list[PlanStep]) -> list[ft.Control]:
        """
        Build tree structure from step dependencies.

        Args:
            steps: List of plan steps

        Returns:
            List of tree node controls
        """
        # Create lookup for steps by ID
        step_by_id = {s.id: s for s in steps}

        # Find roots (no dependencies or dependencies not in this plan)
        valid_ids = set(step_by_id.keys())
        self._roots = [
            s for s in steps
            if not s.dependencies or not any(d in valid_ids for d in s.dependencies)
        ]

        # Track which steps have been placed as children
        placed_as_child: set[str] = set()

        # Build children lookup (step -> steps that depend on it)
        children_of: dict[str, list[PlanStep]] = {s.id: [] for s in steps}
        for step in steps:
            for dep_id in step.dependencies:
                if dep_id in children_of:
                    children_of[dep_id].append(step)
                    placed_as_child.add(step.id)

        # Build tree recursively
        def build_node(step: PlanStep, depth: int = 0) -> ft.Control:
            row = self._create_tree_row(step, depth)
            self._step_rows[step.id] = row

            children = children_of.get(step.id, [])
            if not children:
                return row

            return ft.Column(
                controls=[
                    row,
                    *[build_node(c, depth + 1) for c in children]
                ],
                spacing=Theme.SPACING_XS,
            )

        # Build from roots, but also include orphaned non-root steps
        nodes = []
        for root in self._roots:
            nodes.append(build_node(root))

        # Add any steps not reached from roots
        for step in steps:
            if step.id not in self._step_rows:
                nodes.append(build_node(step))

        return nodes

    def _create_tree_row(self, step: PlanStep, depth: int) -> ft.Container:
        """Create a tree row with indentation."""
        status_color = _get_status_color(step.status)
        tool_icon = _get_tool_icon(step.tool_name)

        # Indentation based on depth
        indent = depth * 24

        # Connection indicator for non-root nodes
        if depth > 0:
            connector = ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Icon(
                            ft.Icons.SUBDIRECTORY_ARROW_RIGHT,
                            size=14,
                            color=Theme.TEXT_MUTED,
                        ),
                    ),
                ],
                spacing=0,
            )
        else:
            connector = ft.Container(width=0)

        # Status dot
        status_dot = ft.Container(
            width=8,
            height=8,
            border_radius=4,
            bgcolor=status_color,
        )

        # Description
        description = ft.Text(
            step.description,
            color=Theme.TEXT_PRIMARY,
            size=Theme.FONT_SM,
            expand=True,
            max_lines=2,
            overflow=ft.TextOverflow.ELLIPSIS,
        )

        # Tool icon
        icons = []
        if tool_icon:
            icons.append(
                ft.Icon(
                    tool_icon,
                    size=14,
                    color=Theme.TEXT_MUTED,
                    tooltip=step.tool_name,
                )
            )

        row_content = ft.Row(
            controls=[
                ft.Container(width=indent),  # Indentation
                connector,
                status_dot,
                description,
                *icons,
            ],
            spacing=Theme.SPACING_SM,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        return ft.Container(
            content=row_content,
            padding=ft.Padding.symmetric(
                horizontal=Theme.SPACING_SM,
                vertical=Theme.SPACING_XS,
            ),
            border_radius=Theme.RADIUS_SM,
            bgcolor=Theme.BG_SECONDARY,
            data=step.id,
        )

    def set_plan(self, plan: AgentPlan) -> None:
        """Replace the displayed plan."""
        self._plan = plan
        self._build()
        _safe_update(self)

    def update_step_status(self, step_id: str, status: StepStatus) -> None:
        """
        Update visual for a specific step.

        Args:
            step_id: ID of step to update
            status: New status
        """
        if step_id not in self._step_rows:
            return

        row = self._step_rows[step_id]
        status_color = _get_status_color(status)

        # Find and update the status dot (after indentation and connector)
        if isinstance(row.content, ft.Row):
            for control in row.content.controls:
                if (isinstance(control, ft.Container) and
                    control.width == 8 and control.height == 8):
                    control.bgcolor = status_color
                    _safe_update(control)
                    break


class PlanViewSwitcher(ft.AnimatedSwitcher):
    """
    Animated switcher between list and tree plan views.

    Persists current mode and animates transitions.
    """

    def __init__(self, mode: str = "list", plan: Optional[AgentPlan] = None):
        """
        Initialize view switcher.

        Args:
            mode: Initial view mode ("list" or "tree")
            plan: The agent plan to display
        """
        self._current_mode = mode
        self._plan = plan

        # Create both views
        self._list_view = PlanListView(plan)
        self._tree_view = PlanTreeView(plan)

        # Select initial content
        content = self._list_view if mode == "list" else self._tree_view

        super().__init__(
            content=content,
            duration=200,
            transition=ft.AnimatedSwitcherTransition.FADE,
            expand=True,
        )

    def set_view_mode(self, mode: str) -> None:
        """
        Switch between list and tree views.

        Args:
            mode: View mode ("list" or "tree")
        """
        if mode == self._current_mode:
            return

        self._current_mode = mode

        if mode == "list":
            self.content = self._list_view
        else:
            self.content = self._tree_view

        _safe_update(self)

    def set_plan(self, plan: AgentPlan) -> None:
        """
        Update plan in both views.

        Args:
            plan: The agent plan to display
        """
        self._plan = plan
        self._list_view.set_plan(plan)
        self._tree_view.set_plan(plan)
        _safe_update(self)

    def update_step_status(self, step_id: str, status: StepStatus) -> None:
        """
        Update step status in both views.

        Args:
            step_id: ID of step to update
            status: New status
        """
        self._list_view.update_step_status(step_id, status)
        self._tree_view.update_step_status(step_id, status)

    @property
    def current_mode(self) -> str:
        """Get current view mode."""
        return self._current_mode
