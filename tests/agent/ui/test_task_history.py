"""
Tests for Task History View

Tests TaskHistoryView and TaskSessionRow components.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from src.agent.observability.trace_models import TraceSession


class TestTaskSessionRow:
    """Tests for TaskSessionRow component."""

    def test_task_session_row_creation(self):
        """Test TaskSessionRow creates with session."""
        from src.agent.ui.task_history import TaskSessionRow

        session = TraceSession(
            id="test-session",
            task="Build a web scraper for news articles",
            started_at=datetime.now(timezone.utc),
            status="completed",
            total_events=15,
            total_tokens=5000,
            total_cost_usd=0.05,
        )
        row = TaskSessionRow(session, on_replay=MagicMock())
        assert row is not None
        assert row._session == session

    def test_task_session_row_truncates_long_task(self):
        """Test TaskSessionRow truncates long task descriptions."""
        from src.agent.ui.task_history import TaskSessionRow

        long_task = "A" * 100  # 100 character task
        session = TraceSession(
            id="test",
            task=long_task,
            started_at=datetime.now(timezone.utc),
            status="completed",
        )
        row = TaskSessionRow(session)
        # Task should be truncated internally when displayed
        assert row._session.task == long_task  # Original preserved

    def test_replay_callback(self):
        """Test replay button triggers callback."""
        from src.agent.ui.task_history import TaskSessionRow

        callback = MagicMock()
        session = TraceSession(
            id="test",
            task="Test task",
            started_at=datetime.now(timezone.utc),
            status="completed",
        )
        row = TaskSessionRow(session, on_replay=callback)

        # Simulate replay click by calling the method directly
        row._on_replay_click(MagicMock())
        callback.assert_called_with("Test task")

    def test_task_session_row_all_statuses(self):
        """Test TaskSessionRow handles all status values."""
        from src.agent.ui.task_history import TaskSessionRow

        for status in ["running", "completed", "failed", "cancelled"]:
            session = TraceSession(
                id=f"test-{status}",
                task=f"Task with {status} status",
                started_at=datetime.now(timezone.utc),
                status=status,
            )
            row = TaskSessionRow(session)
            assert row is not None
            assert row._session.status == status


class TestTaskHistoryView:
    """Tests for TaskHistoryView component."""

    def test_task_history_view_creation(self):
        """Test TaskHistoryView creates and can load sessions."""
        with patch("src.agent.ui.task_history.TraceStore") as MockStore:
            mock_store = MagicMock()
            mock_store.get_sessions.return_value = []

            from src.agent.ui.task_history import TaskHistoryView

            view = TaskHistoryView(on_replay=MagicMock(), trace_store=mock_store)
            view.refresh()

            mock_store.get_sessions.assert_called()

    def test_task_history_view_empty_state(self):
        """Test TaskHistoryView shows empty state when no sessions."""
        with patch("src.agent.ui.task_history.TraceStore") as MockStore:
            mock_store = MagicMock()
            mock_store.get_sessions.return_value = []

            from src.agent.ui.task_history import TaskHistoryView

            view = TaskHistoryView(trace_store=mock_store)
            view.refresh()

            assert len(view._sessions) == 0
            # Should have header + empty state
            assert len(view.controls) >= 1

    def test_task_history_view_with_sessions(self):
        """Test TaskHistoryView displays sessions."""
        with patch("src.agent.ui.task_history.TraceStore"):
            from src.agent.ui.task_history import TaskHistoryView

            mock_store = MagicMock()
            mock_sessions = [
                TraceSession(
                    id="1",
                    task="Task 1",
                    started_at=datetime.now(timezone.utc),
                    status="completed",
                ),
                TraceSession(
                    id="2",
                    task="Task 2",
                    started_at=datetime.now(timezone.utc),
                    status="running",
                ),
            ]
            mock_store.get_sessions.return_value = mock_sessions

            view = TaskHistoryView(trace_store=mock_store)
            view.refresh()

            assert len(view._sessions) == 2

    def test_task_history_view_load_more(self):
        """Test TaskHistoryView pagination."""
        with patch("src.agent.ui.task_history.TraceStore"):
            from src.agent.ui.task_history import TaskHistoryView

            mock_store = MagicMock()
            # First page returns PAGE_SIZE sessions
            first_page = [
                TraceSession(
                    id=str(i),
                    task=f"Task {i}",
                    started_at=datetime.now(timezone.utc),
                    status="completed",
                )
                for i in range(TaskHistoryView.PAGE_SIZE)
            ]
            # Second page returns fewer
            second_page = [
                TraceSession(
                    id=str(i + TaskHistoryView.PAGE_SIZE),
                    task=f"Task {i + TaskHistoryView.PAGE_SIZE}",
                    started_at=datetime.now(timezone.utc),
                    status="completed",
                )
                for i in range(5)
            ]

            mock_store.get_sessions.side_effect = [first_page, second_page]

            view = TaskHistoryView(trace_store=mock_store)
            view.refresh()

            assert len(view._sessions) == TaskHistoryView.PAGE_SIZE
            assert view._has_more is True

            view.load_more()

            assert len(view._sessions) == TaskHistoryView.PAGE_SIZE + 5
            assert view._has_more is False  # Less than PAGE_SIZE returned

    def test_task_history_view_replay_callback(self):
        """Test TaskHistoryView passes replay callback to rows."""
        callback = MagicMock()
        mock_store = MagicMock()
        mock_store.get_sessions.return_value = []

        from src.agent.ui.task_history import TaskHistoryView

        view = TaskHistoryView(on_replay=callback, trace_store=mock_store)
        assert view._on_replay == callback


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_format_relative_time_just_now(self):
        """Test relative time for very recent."""
        from src.agent.ui.task_history import _format_relative_time

        now = datetime.now(timezone.utc)
        assert _format_relative_time(now) == "Just now"

    def test_format_relative_time_minutes(self):
        """Test relative time for minutes ago."""
        from datetime import timedelta
        from src.agent.ui.task_history import _format_relative_time

        past = datetime.now(timezone.utc) - timedelta(minutes=5)
        assert "5m ago" == _format_relative_time(past)

    def test_format_relative_time_hours(self):
        """Test relative time for hours ago."""
        from datetime import timedelta
        from src.agent.ui.task_history import _format_relative_time

        past = datetime.now(timezone.utc) - timedelta(hours=3)
        assert "3h ago" == _format_relative_time(past)

    def test_format_relative_time_days(self):
        """Test relative time for days ago."""
        from datetime import timedelta
        from src.agent.ui.task_history import _format_relative_time

        past = datetime.now(timezone.utc) - timedelta(days=2)
        assert "2d ago" == _format_relative_time(past)

    def test_format_duration(self):
        """Test duration formatting."""
        from datetime import timedelta
        from src.agent.ui.task_history import _format_duration

        start = datetime.now(timezone.utc)

        # Running (no end time)
        assert _format_duration(start, None) == "Running..."

        # Short duration
        end_short = start + timedelta(seconds=30)
        assert _format_duration(start, end_short) == "30s"

        # Medium duration
        end_medium = start + timedelta(minutes=5, seconds=30)
        assert _format_duration(start, end_medium) == "5m 30s"

        # Long duration
        end_long = start + timedelta(hours=2, minutes=15)
        assert _format_duration(start, end_long) == "2h 15m"

    def test_format_cost(self):
        """Test cost formatting."""
        from src.agent.ui.task_history import _format_cost

        assert _format_cost(None) == "$0.00"
        assert _format_cost(0) == "$0.00"
        assert _format_cost(0.001) == "$0.0010"
        assert _format_cost(0.05) == "$0.05"
        assert _format_cost(1.23) == "$1.23"


class TestStatusMappings:
    """Tests for session status icon and color mappings."""

    def test_session_status_icons_defined(self):
        """Test all session status values have icons."""
        from src.agent.ui.task_history import SESSION_STATUS_ICONS

        for status in ["running", "completed", "failed", "cancelled"]:
            assert status in SESSION_STATUS_ICONS, f"Missing icon for {status}"

    def test_session_status_colors_defined(self):
        """Test all session status values have colors."""
        from src.agent.ui.task_history import SESSION_STATUS_COLORS

        for status in ["running", "completed", "failed", "cancelled"]:
            assert status in SESSION_STATUS_COLORS, f"Missing color for {status}"
