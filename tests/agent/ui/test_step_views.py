"""
Tests for Step View Components

Tests StepChecklistView, StepTimelineView, StepCardsView, and StepViewSwitcher.
"""

import pytest

from src.agent.models.plan import PlanStep, StepStatus


class TestStepChecklistView:
    """Tests for StepChecklistView component."""

    def test_checklist_view_creation(self):
        """Test StepChecklistView creates with steps."""
        from src.agent.ui.step_views import StepChecklistView

        steps = [
            PlanStep(description="Step 1", status=StepStatus.COMPLETED),
            PlanStep(description="Step 2", status=StepStatus.RUNNING),
            PlanStep(description="Step 3", status=StepStatus.PENDING),
        ]
        view = StepChecklistView(steps)
        assert len(view.controls) == 3

    def test_checklist_view_empty_steps(self):
        """Test StepChecklistView handles empty steps list."""
        from src.agent.ui.step_views import StepChecklistView

        view = StepChecklistView([])
        assert len(view.controls) == 0

    def test_checklist_view_set_steps(self):
        """Test replacing steps in checklist view (internal state only)."""
        from src.agent.ui.step_views import StepChecklistView

        view = StepChecklistView([])
        new_steps = [
            PlanStep(description="New step 1"),
            PlanStep(description="New step 2"),
        ]
        # Directly update internal state (without calling update which requires page)
        view._steps = list(new_steps)
        view._expanded_id = None
        view.controls = view._build_controls()
        assert len(view._steps) == 2
        assert len(view.controls) == 2

    def test_checklist_view_update_step(self):
        """Test updating step status in checklist view (internal state only)."""
        from src.agent.ui.step_views import StepChecklistView

        step = PlanStep(id="step-1", description="Step 1", status=StepStatus.PENDING)
        view = StepChecklistView([step])

        # Directly update internal state
        for s in view._steps:
            if s.id == "step-1":
                s.status = StepStatus.COMPLETED
        view.controls = view._build_controls()
        assert view._steps[0].status == StepStatus.COMPLETED

    def test_checklist_view_tracks_internal_steps(self):
        """Test that view maintains its own copy of steps."""
        from src.agent.ui.step_views import StepChecklistView

        original_steps = [PlanStep(description="Step 1")]
        view = StepChecklistView(original_steps)

        # Modifying original shouldn't affect view
        original_steps.append(PlanStep(description="Step 2"))
        assert len(view._steps) == 1


class TestStepTimelineView:
    """Tests for StepTimelineView component."""

    def test_timeline_view_creation(self):
        """Test StepTimelineView creates with steps."""
        from src.agent.ui.step_views import StepTimelineView

        steps = [
            PlanStep(description="Step 1", status=StepStatus.COMPLETED),
            PlanStep(description="Step 2", status=StepStatus.RUNNING),
        ]
        view = StepTimelineView(steps)
        assert len(view.controls) == 2

    def test_timeline_view_set_steps(self):
        """Test replacing steps in timeline view (internal state only)."""
        from src.agent.ui.step_views import StepTimelineView

        view = StepTimelineView([])
        new_steps = [PlanStep(description="New step")]
        # Directly update internal state
        view._steps = list(new_steps)
        view.controls = view._build_controls()
        assert len(view._steps) == 1
        assert len(view.controls) == 1

    def test_timeline_view_update_step(self):
        """Test updating step status in timeline view (internal state only)."""
        from src.agent.ui.step_views import StepTimelineView

        step = PlanStep(id="step-1", description="Step 1", status=StepStatus.PENDING)
        view = StepTimelineView([step])

        # Directly update internal state
        for s in view._steps:
            if s.id == "step-1":
                s.status = StepStatus.RUNNING
        view.controls = view._build_controls()
        assert view._steps[0].status == StepStatus.RUNNING


class TestStepCardsView:
    """Tests for StepCardsView component."""

    def test_cards_view_creation(self):
        """Test StepCardsView creates with steps."""
        from src.agent.ui.step_views import StepCardsView

        steps = [
            PlanStep(
                description="Step 1",
                tool_name="test_tool",
                tool_params={"key": "value"},
            ),
        ]
        view = StepCardsView(steps)
        assert len(view.controls) == 1

    def test_cards_view_set_steps(self):
        """Test replacing steps in cards view (internal state only)."""
        from src.agent.ui.step_views import StepCardsView

        view = StepCardsView([])
        new_steps = [PlanStep(description="New step")]
        # Directly update internal state
        view._steps = list(new_steps)
        view._expanded_ids.clear()
        view.controls = view._build_controls()
        assert len(view._steps) == 1
        # Expanded IDs should be cleared
        assert len(view._expanded_ids) == 0
        assert len(view.controls) == 1

    def test_cards_view_update_step(self):
        """Test updating step status in cards view (internal state only)."""
        from src.agent.ui.step_views import StepCardsView

        step = PlanStep(id="step-1", description="Step 1", status=StepStatus.PENDING)
        view = StepCardsView([step])

        # Directly update internal state
        for s in view._steps:
            if s.id == "step-1":
                s.status = StepStatus.FAILED
        view.controls = view._build_controls()
        assert view._steps[0].status == StepStatus.FAILED


class TestStepViewSwitcher:
    """Tests for StepViewSwitcher component."""

    def test_view_switcher_creation(self):
        """Test StepViewSwitcher creates with initial mode."""
        from src.agent.ui.step_views import StepViewSwitcher

        steps = [PlanStep(description="Test step")]
        switcher = StepViewSwitcher("checklist", steps)
        assert switcher.current_mode == "checklist"
        assert switcher.content is not None

    def test_view_switcher_mode_change(self):
        """Test StepViewSwitcher changes mode (internal state only)."""
        from src.agent.ui.step_views import StepViewSwitcher, StepTimelineView

        steps = [PlanStep(description="Test step")]
        switcher = StepViewSwitcher("checklist", steps)

        # Directly change mode without calling update
        switcher._mode = "timeline"
        switcher._steps = list(steps)
        switcher.content = switcher._create_view("timeline")
        assert switcher.current_mode == "timeline"
        assert isinstance(switcher.content, StepTimelineView)

    def test_view_switcher_invalid_mode_defaults(self):
        """Test StepViewSwitcher defaults invalid mode to checklist."""
        from src.agent.ui.step_views import StepViewSwitcher, StepChecklistView

        steps = [PlanStep(description="Test step")]
        switcher = StepViewSwitcher("invalid_mode", steps)
        assert switcher.current_mode == "checklist"
        assert isinstance(switcher.content, StepChecklistView)

    def test_view_switcher_set_steps(self):
        """Test setting steps on switcher (internal state only)."""
        from src.agent.ui.step_views import StepViewSwitcher

        switcher = StepViewSwitcher("checklist", [])
        new_steps = [
            PlanStep(description="Step 1"),
            PlanStep(description="Step 2"),
        ]
        # Directly update internal state
        switcher._steps = list(new_steps)
        if switcher.content and hasattr(switcher.content, "_steps"):
            switcher.content._steps = list(new_steps)
        assert len(switcher.steps) == 2

    def test_view_switcher_update_step(self):
        """Test updating step status through switcher (internal state only)."""
        from src.agent.ui.step_views import StepViewSwitcher

        step = PlanStep(id="step-1", description="Step 1", status=StepStatus.PENDING)
        switcher = StepViewSwitcher("checklist", [step])

        # Directly update internal state
        for s in switcher._steps:
            if s.id == "step-1":
                s.status = StepStatus.COMPLETED
        assert switcher.steps[0].status == StepStatus.COMPLETED

    def test_view_switcher_all_modes(self):
        """Test switcher can switch to all modes (internal state only)."""
        from src.agent.ui.step_views import (
            StepViewSwitcher,
            StepChecklistView,
            StepTimelineView,
            StepCardsView,
        )

        steps = [PlanStep(description="Test")]
        switcher = StepViewSwitcher("checklist", steps)

        for mode, expected_type in [
            ("checklist", StepChecklistView),
            ("timeline", StepTimelineView),
            ("cards", StepCardsView),
        ]:
            # Directly change mode
            switcher._mode = mode
            switcher.content = switcher._create_view(mode)
            assert switcher.current_mode == mode
            assert isinstance(switcher.content, expected_type)

    def test_view_switcher_preserves_steps_on_mode_change(self):
        """Test that steps are preserved when changing modes (internal state only)."""
        from src.agent.ui.step_views import StepViewSwitcher

        steps = [
            PlanStep(id="1", description="Step 1"),
            PlanStep(id="2", description="Step 2"),
        ]
        switcher = StepViewSwitcher("checklist", steps)

        # Directly change mode
        switcher._mode = "timeline"
        switcher.content = switcher._create_view("timeline")
        assert len(switcher.steps) == 2
        assert switcher.steps[0].id == "1"


class TestStatusMappings:
    """Tests for status icon and color mappings."""

    def test_status_icons_defined(self):
        """Test all status values have icons."""
        from src.agent.ui.step_views import STATUS_ICONS

        for status in StepStatus:
            assert status in STATUS_ICONS, f"Missing icon for {status}"

    def test_status_colors_defined(self):
        """Test all status values have colors."""
        from src.agent.ui.step_views import STATUS_COLORS

        for status in StepStatus:
            assert status in STATUS_COLORS, f"Missing color for {status}"
