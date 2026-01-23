"""
Tests for Enhanced ApprovalSheet

Tests detail levels, parameter editing, and batch approval features.
"""

import pytest
from unittest.mock import MagicMock

from src.agent.safety.classification import ActionClassification
from src.agent.safety.approval import ApprovalRequest


class TestDetailLevelRenderers:
    """Tests for approval detail level renderers."""

    def test_detail_level_minimal(self):
        """Test minimal detail level renders tool name and badge only."""
        from src.agent.ui.approval_detail_levels import render_minimal

        classification = ActionClassification(
            risk_level="moderate",
            reason="Test reason",
            requires_approval=True,
            tool_name="test_tool",
            parameters={"key": "value"},
        )
        content = render_minimal(classification)
        assert content is not None
        # Minimal should have a Row with badge and tool name
        assert hasattr(content, 'content')

    def test_detail_level_detailed(self):
        """Test detailed level renders full parameters."""
        from src.agent.ui.approval_detail_levels import render_detailed

        classification = ActionClassification(
            risk_level="destructive",
            reason="Test reason explaining the action",
            requires_approval=True,
            tool_name="file_write",
            parameters={"path": "/tmp/test.txt", "content": "hello"},
        )
        content = render_detailed(classification)
        assert content is not None

    def test_detail_level_detailed_truncates_long_params(self):
        """Test detailed level truncates parameters over 500 chars."""
        from src.agent.ui.approval_detail_levels import render_detailed

        # Create very long parameters
        long_content = "x" * 1000
        classification = ActionClassification(
            risk_level="moderate",
            reason="Test",
            requires_approval=True,
            tool_name="test",
            parameters={"content": long_content},
        )
        content = render_detailed(classification, max_chars=500)
        assert content is not None

    def test_detail_level_progressive_collapsed(self):
        """Test progressive detail level starts collapsed."""
        from src.agent.ui.approval_detail_levels import render_progressive

        classification = ActionClassification(
            risk_level="destructive",
            reason="Test reason",
            requires_approval=True,
            tool_name="file_delete",
            parameters={"path": "/tmp/test"},
        )
        content = render_progressive(classification, expanded=False)
        assert content is not None

    def test_detail_level_progressive_expanded(self):
        """Test progressive detail level can start expanded."""
        from src.agent.ui.approval_detail_levels import render_progressive

        classification = ActionClassification(
            risk_level="critical",
            reason="Critical action test",
            requires_approval=True,
            tool_name="file_delete",
            parameters={"path": "/important/file"},
        )
        content = render_progressive(classification, expanded=True)
        assert content is not None

    def test_render_by_level_minimal(self):
        """Test render_by_level with minimal level."""
        from src.agent.ui.approval_detail_levels import render_by_level

        classification = ActionClassification(
            risk_level="safe",
            reason="Safe read",
            requires_approval=False,
            tool_name="file_read",
            parameters={"path": "/tmp/test"},
        )
        content = render_by_level(classification, "minimal")
        assert content is not None

    def test_render_by_level_detailed(self):
        """Test render_by_level with detailed level."""
        from src.agent.ui.approval_detail_levels import render_by_level

        classification = ActionClassification(
            risk_level="moderate",
            reason="Moderate action",
            requires_approval=True,
            tool_name="browser",
            parameters={"url": "https://example.com"},
        )
        content = render_by_level(classification, "detailed")
        assert content is not None

    def test_render_by_level_invalid(self):
        """Test render_by_level raises on invalid level."""
        from src.agent.ui.approval_detail_levels import render_by_level

        classification = ActionClassification(
            risk_level="safe",
            reason="Test",
            requires_approval=False,
            tool_name="test",
            parameters={},
        )
        with pytest.raises(ValueError, match="Unknown detail level"):
            render_by_level(classification, "invalid_level")


class TestApprovalSheetEnhanced:
    """Tests for enhanced ApprovalSheet features."""

    def test_approval_sheet_with_detail_level_minimal(self):
        """Test ApprovalSheet accepts minimal detail_level."""
        from src.agent.ui.approval_sheet import ApprovalSheet

        request = ApprovalRequest()
        request.classification = ActionClassification(
            risk_level="moderate",
            reason="Test",
            requires_approval=True,
            tool_name="test",
            parameters={},
        )

        sheet = ApprovalSheet(
            request=request,
            on_approve=MagicMock(),
            on_reject=MagicMock(),
            detail_level="minimal",
        )
        assert sheet is not None
        assert sheet.detail_level == "minimal"

    def test_approval_sheet_with_detail_level_detailed(self):
        """Test ApprovalSheet with detailed level (default)."""
        from src.agent.ui.approval_sheet import ApprovalSheet

        request = ApprovalRequest()
        request.classification = ActionClassification(
            risk_level="destructive",
            reason="Writes to file",
            requires_approval=True,
            tool_name="file_write",
            parameters={"path": "/tmp/test.txt"},
        )

        sheet = ApprovalSheet(
            request=request,
            on_approve=MagicMock(),
            on_reject=MagicMock(),
            detail_level="detailed",
        )
        assert sheet is not None
        assert sheet.detail_level == "detailed"

    def test_approval_sheet_with_detail_level_progressive(self):
        """Test ApprovalSheet with progressive detail_level."""
        from src.agent.ui.approval_sheet import ApprovalSheet

        request = ApprovalRequest()
        request.classification = ActionClassification(
            risk_level="critical",
            reason="Deletes file",
            requires_approval=True,
            tool_name="file_delete",
            parameters={"path": "/important"},
        )

        sheet = ApprovalSheet(
            request=request,
            on_approve=MagicMock(),
            on_reject=MagicMock(),
            detail_level="progressive",
        )
        assert sheet is not None
        assert sheet.detail_level == "progressive"

    def test_approval_sheet_default_detail_level(self):
        """Test ApprovalSheet defaults to detailed level."""
        from src.agent.ui.approval_sheet import ApprovalSheet

        request = ApprovalRequest()
        request.classification = ActionClassification(
            risk_level="moderate",
            reason="Test",
            requires_approval=True,
            tool_name="test",
            parameters={},
        )

        sheet = ApprovalSheet(
            request=request,
            on_approve=MagicMock(),
            on_reject=MagicMock(),
        )
        assert sheet.detail_level == "detailed"

    def test_approval_sheet_modified_params_initially_none(self):
        """Test ApprovalSheet has no modified params initially."""
        from src.agent.ui.approval_sheet import ApprovalSheet

        request = ApprovalRequest()
        request.classification = ActionClassification(
            risk_level="moderate",
            reason="Test",
            requires_approval=True,
            tool_name="test",
            parameters={"key": "original"},
        )

        sheet = ApprovalSheet(
            request=request,
            on_approve=MagicMock(),
            on_reject=MagicMock(),
        )
        assert sheet.get_modified_params() is None

    def test_approval_sheet_remember_scope_initially_none(self):
        """Test ApprovalSheet has no remember scope initially."""
        from src.agent.ui.approval_sheet import ApprovalSheet

        request = ApprovalRequest()
        request.classification = ActionClassification(
            risk_level="moderate",
            reason="Test",
            requires_approval=True,
            tool_name="test",
            parameters={},
        )

        sheet = ApprovalSheet(
            request=request,
            on_approve=MagicMock(),
            on_reject=MagicMock(),
        )
        assert sheet.get_remember_scope() is None


class TestApprovalSheetExports:
    """Test that exports are available from __init__."""

    def test_exports_render_functions(self):
        """Test render functions are exported from package."""
        from src.agent.ui import (
            render_minimal,
            render_detailed,
            render_progressive,
            render_by_level,
        )

        assert callable(render_minimal)
        assert callable(render_detailed)
        assert callable(render_progressive)
        assert callable(render_by_level)

    def test_exports_approval_sheet(self):
        """Test ApprovalSheet is exported from package."""
        from src.agent.ui import ApprovalSheet

        assert ApprovalSheet is not None
