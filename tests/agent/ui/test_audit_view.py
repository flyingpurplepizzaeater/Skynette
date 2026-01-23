"""
Tests for AuditTrailView component.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch


def test_audit_view_creation():
    """Test AuditTrailView creates without errors."""
    with patch('src.agent.ui.audit_view.get_audit_store') as mock_get:
        mock_store = MagicMock()
        mock_store.query.return_value = []
        mock_store.get_session_summary.return_value = {
            "total_actions": 0,
            "by_risk": {"safe": 0, "moderate": 0, "destructive": 0, "critical": 0},
            "approved": 0,
            "rejected": 0,
            "successful": 0,
            "total_duration_ms": 0,
        }
        mock_get.return_value = mock_store

        from src.agent.ui.audit_view import AuditTrailView
        view = AuditTrailView(session_id="test-session")
        assert view is not None
        assert view._session_id == "test-session"


def test_audit_entry_row_display():
    """Test AuditEntryRow renders entry."""
    from src.agent.ui.audit_view import AuditEntryRow
    from src.agent.safety.audit import AuditEntry

    entry = AuditEntry(
        session_id="test",
        step_id="step-1",
        tool_name="file_read",
        risk_level="safe",
        approval_decision="not_required",
        duration_ms=150.5,
    )
    row = AuditEntryRow(entry)
    assert row is not None
    assert row._entry == entry
    assert row._expanded is False


def test_audit_entry_row_expansion():
    """Test AuditEntryRow toggle expand."""
    from src.agent.ui.audit_view import AuditEntryRow
    from src.agent.safety.audit import AuditEntry

    entry = AuditEntry(
        session_id="test",
        step_id="step-1",
        tool_name="file_write",
        risk_level="destructive",
        approval_required=True,
        approval_decision="approved",
        approved_by="user",
        parameters={"path": "/test/file.txt", "content": "test content"},
        result={"success": True},
        duration_ms=250.0,
    )
    row = AuditEntryRow(entry)

    # Initial state is collapsed
    assert row._expanded is False

    # Toggle should expand
    row._toggle_expand(None)
    assert row._expanded is True

    # Toggle again should collapse
    row._toggle_expand(None)
    assert row._expanded is False


def test_audit_view_filter():
    """Test filtering by risk level."""
    with patch('src.agent.ui.audit_view.get_audit_store') as mock_get:
        mock_store = MagicMock()
        mock_store.query.return_value = []
        mock_store.get_session_summary.return_value = {
            "total_actions": 0,
            "by_risk": {"safe": 0, "moderate": 0, "destructive": 0, "critical": 0},
            "approved": 0,
            "rejected": 0,
            "successful": 0,
            "total_duration_ms": 0,
        }
        mock_get.return_value = mock_store

        from src.agent.ui.audit_view import AuditTrailView
        view = AuditTrailView(session_id="test")
        view.build()

        view.set_filter("destructive")
        mock_store.query.assert_called_with(
            session_id="test",
            risk_level="destructive",
            limit=100,
        )


def test_audit_view_set_session():
    """Test changing session refreshes entries."""
    with patch('src.agent.ui.audit_view.get_audit_store') as mock_get:
        mock_store = MagicMock()
        mock_store.query.return_value = []
        mock_store.get_session_summary.return_value = {
            "total_actions": 0,
            "by_risk": {"safe": 0, "moderate": 0, "destructive": 0, "critical": 0},
            "approved": 0,
            "rejected": 0,
            "successful": 0,
            "total_duration_ms": 0,
        }
        mock_get.return_value = mock_store

        from src.agent.ui.audit_view import AuditTrailView
        view = AuditTrailView(session_id=None)
        view.build()

        # Set session
        view.set_session("new-session")
        assert view._session_id == "new-session"
        mock_store.query.assert_called_with(
            session_id="new-session",
            risk_level=None,
            limit=100,
        )


def test_audit_view_add_entry():
    """Test adding entry to list."""
    with patch('src.agent.ui.audit_view.get_audit_store') as mock_get:
        mock_store = MagicMock()
        mock_store.query.return_value = []
        mock_store.get_session_summary.return_value = {
            "total_actions": 1,
            "by_risk": {"safe": 1, "moderate": 0, "destructive": 0, "critical": 0},
            "approved": 0,
            "rejected": 0,
            "successful": 1,
            "total_duration_ms": 100,
        }
        mock_get.return_value = mock_store

        from src.agent.ui.audit_view import AuditTrailView
        from src.agent.safety.audit import AuditEntry

        view = AuditTrailView(session_id="test-session")
        view.build()

        entry = AuditEntry(
            session_id="test-session",
            step_id="step-1",
            tool_name="file_read",
            risk_level="safe",
            duration_ms=100.0,
        )

        view.add_entry(entry)

        # Entry should be added to internal list
        assert len(view._entries) == 1
        assert view._entries[0] == entry


def test_audit_view_add_entry_filtered():
    """Test adding entry respects filter."""
    with patch('src.agent.ui.audit_view.get_audit_store') as mock_get:
        mock_store = MagicMock()
        mock_store.query.return_value = []
        mock_store.get_session_summary.return_value = {
            "total_actions": 0,
            "by_risk": {"safe": 0, "moderate": 0, "destructive": 0, "critical": 0},
            "approved": 0,
            "rejected": 0,
            "successful": 0,
            "total_duration_ms": 0,
        }
        mock_get.return_value = mock_store

        from src.agent.ui.audit_view import AuditTrailView
        from src.agent.safety.audit import AuditEntry

        view = AuditTrailView(session_id="test-session")
        view.build()

        # Set filter to destructive only
        view._filter_risk = "destructive"

        # Add a safe entry - should be ignored
        entry = AuditEntry(
            session_id="test-session",
            step_id="step-1",
            tool_name="file_read",
            risk_level="safe",
            duration_ms=100.0,
        )

        view.add_entry(entry)

        # Entry should NOT be added due to filter
        assert len(view._entries) == 0


def test_audit_view_add_entry_wrong_session():
    """Test adding entry ignores wrong session."""
    with patch('src.agent.ui.audit_view.get_audit_store') as mock_get:
        mock_store = MagicMock()
        mock_store.query.return_value = []
        mock_store.get_session_summary.return_value = {
            "total_actions": 0,
            "by_risk": {"safe": 0, "moderate": 0, "destructive": 0, "critical": 0},
            "approved": 0,
            "rejected": 0,
            "successful": 0,
            "total_duration_ms": 0,
        }
        mock_get.return_value = mock_store

        from src.agent.ui.audit_view import AuditTrailView
        from src.agent.safety.audit import AuditEntry

        view = AuditTrailView(session_id="test-session")
        view.build()

        # Add entry from different session
        entry = AuditEntry(
            session_id="other-session",
            step_id="step-1",
            tool_name="file_read",
            risk_level="safe",
            duration_ms=100.0,
        )

        view.add_entry(entry)

        # Entry should NOT be added due to wrong session
        assert len(view._entries) == 0


def test_audit_entry_row_with_error():
    """Test AuditEntryRow displays error."""
    from src.agent.ui.audit_view import AuditEntryRow
    from src.agent.safety.audit import AuditEntry

    entry = AuditEntry(
        session_id="test",
        step_id="step-1",
        tool_name="file_delete",
        risk_level="critical",
        approval_required=True,
        approval_decision="approved",
        error="File not found: /test/missing.txt",
        success=False,
        duration_ms=50.0,
    )
    row = AuditEntryRow(entry)
    assert row is not None
    assert row._entry.error is not None
    assert row._entry.success is False


def test_audit_entry_row_approval_badges():
    """Test AuditEntryRow shows approval badges."""
    from src.agent.ui.audit_view import AuditEntryRow, APPROVAL_BADGES
    from src.agent.safety.audit import AuditEntry

    # Test approved
    entry_approved = AuditEntry(
        session_id="test",
        step_id="step-1",
        tool_name="file_write",
        risk_level="destructive",
        approval_required=True,
        approval_decision="approved",
        approved_by="user",
        duration_ms=100.0,
    )
    row_approved = AuditEntryRow(entry_approved)
    assert row_approved is not None

    # Test rejected
    entry_rejected = AuditEntry(
        session_id="test",
        step_id="step-2",
        tool_name="file_delete",
        risk_level="critical",
        approval_required=True,
        approval_decision="rejected",
        duration_ms=50.0,
    )
    row_rejected = AuditEntryRow(entry_rejected)
    assert row_rejected is not None

    # Test auto
    entry_auto = AuditEntry(
        session_id="test",
        step_id="step-3",
        tool_name="file_write",
        risk_level="destructive",
        approval_required=True,
        approval_decision="auto",
        approved_by="similar_match",
        duration_ms=75.0,
    )
    row_auto = AuditEntryRow(entry_auto)
    assert row_auto is not None
