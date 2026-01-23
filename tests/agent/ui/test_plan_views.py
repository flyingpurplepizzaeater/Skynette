"""Tests for plan view components."""

import pytest

from src.agent.models.plan import AgentPlan, PlanStep, StepStatus


class TestPlanListView:
    """Tests for PlanListView component."""

    def test_plan_list_view_creation(self):
        """Test PlanListView renders plan."""
        from src.agent.ui.plan_views import PlanListView

        plan = AgentPlan(
            task="Test task",
            overview="Test overview",
            steps=[
                PlanStep(id="1", description="Step 1"),
                PlanStep(id="2", description="Step 2", dependencies=["1"]),
            ]
        )
        view = PlanListView(plan)
        assert view.controls is not None
        assert len(view.controls) >= 2  # Header + list

    def test_plan_list_view_empty_plan(self):
        """Test PlanListView handles empty plan."""
        from src.agent.ui.plan_views import PlanListView

        plan = AgentPlan(task="Empty", overview="No steps", steps=[])
        view = PlanListView(plan)
        assert view.controls is not None

    def test_plan_list_view_no_plan(self):
        """Test PlanListView handles None plan."""
        from src.agent.ui.plan_views import PlanListView

        view = PlanListView(None)
        assert view.controls is not None

    def test_plan_list_view_with_tools(self):
        """Test PlanListView shows tool icons."""
        from src.agent.ui.plan_views import PlanListView

        plan = AgentPlan(
            task="Tool task",
            overview="With tools",
            steps=[
                PlanStep(id="1", description="Read file", tool_name="file_read"),
                PlanStep(id="2", description="Run code", tool_name="python_execute"),
            ]
        )
        view = PlanListView(plan)
        # View should be built with step rows
        assert "1" in view._step_rows
        assert "2" in view._step_rows

    def test_plan_list_view_set_plan(self):
        """Test PlanListView.set_plan replaces plan."""
        from src.agent.ui.plan_views import PlanListView

        view = PlanListView(None)
        initial_controls = len(view.controls)

        plan = AgentPlan(
            task="New task",
            overview="New overview",
            steps=[PlanStep(id="1", description="Step 1")]
        )
        view.set_plan(plan)

        # Should have rebuilt with new content
        assert view._plan == plan
        assert "1" in view._step_rows


class TestPlanTreeView:
    """Tests for PlanTreeView component."""

    def test_plan_tree_view_dependencies(self):
        """Test PlanTreeView builds tree from dependencies."""
        from src.agent.ui.plan_views import PlanTreeView

        plan = AgentPlan(
            task="Test task",
            overview="Test overview",
            steps=[
                PlanStep(id="1", description="Root step"),
                PlanStep(id="2", description="Child step", dependencies=["1"]),
                PlanStep(id="3", description="Grandchild", dependencies=["2"]),
            ]
        )
        view = PlanTreeView(plan)
        # Tree should have single root
        assert len(view._roots) == 1
        assert view._roots[0].id == "1"

    def test_plan_tree_view_multiple_roots(self):
        """Test PlanTreeView handles multiple root steps."""
        from src.agent.ui.plan_views import PlanTreeView

        plan = AgentPlan(
            task="Parallel task",
            overview="Multiple roots",
            steps=[
                PlanStep(id="1", description="Root A"),
                PlanStep(id="2", description="Root B"),
                PlanStep(id="3", description="Child of A", dependencies=["1"]),
            ]
        )
        view = PlanTreeView(plan)
        assert len(view._roots) == 2

    def test_plan_tree_view_empty_plan(self):
        """Test PlanTreeView handles empty plan."""
        from src.agent.ui.plan_views import PlanTreeView

        plan = AgentPlan(task="Empty", overview="No steps", steps=[])
        view = PlanTreeView(plan)
        assert view.controls is not None
        assert len(view._roots) == 0

    def test_plan_tree_view_no_plan(self):
        """Test PlanTreeView handles None plan."""
        from src.agent.ui.plan_views import PlanTreeView

        view = PlanTreeView(None)
        assert view.controls is not None

    def test_plan_tree_view_set_plan(self):
        """Test PlanTreeView.set_plan replaces plan."""
        from src.agent.ui.plan_views import PlanTreeView

        view = PlanTreeView(None)

        plan = AgentPlan(
            task="New task",
            overview="New overview",
            steps=[
                PlanStep(id="1", description="Root"),
                PlanStep(id="2", description="Child", dependencies=["1"]),
            ]
        )
        view.set_plan(plan)

        assert view._plan == plan
        assert len(view._roots) == 1


class TestPlanViewSwitcher:
    """Tests for PlanViewSwitcher component."""

    def test_plan_view_switcher(self):
        """Test PlanViewSwitcher changes mode."""
        from src.agent.ui.plan_views import PlanViewSwitcher

        plan = AgentPlan(task="Test", overview="Overview", steps=[])
        switcher = PlanViewSwitcher("list", plan)

        assert switcher._current_mode == "list"

        switcher.set_view_mode("tree")
        assert switcher._current_mode == "tree"

    def test_plan_view_switcher_default_list(self):
        """Test PlanViewSwitcher defaults to list mode."""
        from src.agent.ui.plan_views import PlanViewSwitcher

        switcher = PlanViewSwitcher(plan=None)
        assert switcher._current_mode == "list"

    def test_plan_view_switcher_tree_initial(self):
        """Test PlanViewSwitcher can start in tree mode."""
        from src.agent.ui.plan_views import PlanViewSwitcher

        plan = AgentPlan(task="Test", overview="Overview", steps=[])
        switcher = PlanViewSwitcher("tree", plan)
        assert switcher._current_mode == "tree"

    def test_plan_view_switcher_set_plan(self):
        """Test PlanViewSwitcher.set_plan updates both views."""
        from src.agent.ui.plan_views import PlanViewSwitcher

        switcher = PlanViewSwitcher("list", None)

        plan = AgentPlan(
            task="New task",
            overview="New overview",
            steps=[PlanStep(id="1", description="Step")]
        )
        switcher.set_plan(plan)

        assert switcher._plan == plan
        assert switcher._list_view._plan == plan
        assert switcher._tree_view._plan == plan

    def test_plan_view_switcher_same_mode_noop(self):
        """Test switching to same mode does nothing."""
        from src.agent.ui.plan_views import PlanViewSwitcher

        switcher = PlanViewSwitcher("list", None)
        initial_content = switcher.content

        switcher.set_view_mode("list")
        assert switcher.content is initial_content

    def test_plan_view_switcher_current_mode_property(self):
        """Test current_mode property."""
        from src.agent.ui.plan_views import PlanViewSwitcher

        switcher = PlanViewSwitcher("list", None)
        assert switcher.current_mode == "list"

        switcher.set_view_mode("tree")
        assert switcher.current_mode == "tree"


class TestPlanViewHelpers:
    """Tests for helper functions and utilities."""

    def test_get_tool_icon_code(self):
        """Test tool icon for code tools."""
        from src.agent.ui.plan_views import _get_tool_icon
        import flet as ft

        icon = _get_tool_icon("code_execute")
        assert icon == ft.Icons.CODE

    def test_get_tool_icon_file(self):
        """Test tool icon for file tools."""
        from src.agent.ui.plan_views import _get_tool_icon
        import flet as ft

        icon = _get_tool_icon("file_read")
        assert icon == ft.Icons.FOLDER

    def test_get_tool_icon_none(self):
        """Test tool icon for None tool name."""
        from src.agent.ui.plan_views import _get_tool_icon

        icon = _get_tool_icon(None)
        assert icon is None

    def test_get_tool_icon_unknown(self):
        """Test tool icon for unknown tool."""
        from src.agent.ui.plan_views import _get_tool_icon
        import flet as ft

        icon = _get_tool_icon("some_unknown_tool")
        assert icon == ft.Icons.BUILD  # Default

    def test_get_status_color(self):
        """Test status colors."""
        from src.agent.ui.plan_views import _get_status_color
        from src.ui.theme import Theme

        assert _get_status_color(StepStatus.PENDING) == Theme.TEXT_MUTED
        assert _get_status_color(StepStatus.RUNNING) == Theme.PRIMARY
        assert _get_status_color(StepStatus.COMPLETED) == Theme.SUCCESS
        assert _get_status_color(StepStatus.FAILED) == Theme.ERROR
        assert _get_status_color(StepStatus.SKIPPED) == Theme.WARNING


class TestPlanViewExports:
    """Tests for module exports."""

    def test_exports_from_init(self):
        """Test plan views are exported from __init__."""
        from src.agent.ui import PlanListView, PlanTreeView, PlanViewSwitcher

        assert PlanListView is not None
        assert PlanTreeView is not None
        assert PlanViewSwitcher is not None

    def test_exports_in_all(self):
        """Test exports are in __all__."""
        from src.agent.ui import __all__

        assert "PlanListView" in __all__
        assert "PlanTreeView" in __all__
        assert "PlanViewSwitcher" in __all__
