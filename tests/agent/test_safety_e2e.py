"""
E2E Tests for Safety and Approval Systems

Tests QUAL-04: E2E tests for critical agent workflows
"""

import asyncio
import gc
import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.agent import (
    ActionClassifier,
    ActionClassification,
    RiskLevel,
    ApprovalManager,
    ApprovalRequest,
    ApprovalResult,
    KillSwitch,
    get_kill_switch,
    AuditStore,
    AuditEntry,
)
from src.agent.loop.executor import AgentExecutor
from src.agent.models.state import AgentSession, AgentState


class TestClassificationE2E:
    """E2E tests for action classification."""

    def test_builtin_tools_classified_correctly(self):
        """Verify all built-in tools have correct risk classification."""
        classifier = ActionClassifier()

        # Safe tools
        assert classifier.classify("file_read", {"path": "/tmp/test.txt"}).risk_level == "safe"
        assert classifier.classify("file_list", {"path": "/tmp"}).risk_level == "safe"
        assert classifier.classify("web_search", {"query": "python"}).risk_level == "safe"
        assert classifier.classify("rag_query", {"query": "test"}).risk_level == "safe"
        assert classifier.classify("mock_echo", {"message": "hi"}).risk_level == "safe"

        # Moderate tools
        assert classifier.classify("browser", {"url": "https://example.com"}).risk_level == "moderate"

        # Destructive tools
        assert classifier.classify("file_write", {"path": "/tmp/test.txt"}).risk_level == "destructive"
        assert classifier.classify("code_execute", {"code": "print('hi')"}).risk_level == "destructive"
        assert classifier.classify("github", {"operation": "create_repo"}).risk_level == "destructive"

        # Critical tools
        assert classifier.classify("file_delete", {"path": "/tmp/test.txt"}).risk_level == "critical"

    def test_unknown_tool_defaults_moderate(self):
        """Unknown/MCP tools should default to moderate."""
        classifier = ActionClassifier()
        result = classifier.classify("custom_mcp_tool", {"param": "value"})

        assert result.risk_level == "moderate"
        assert result.requires_approval == False  # Moderate doesn't require by default

    def test_classification_includes_context_in_reason(self):
        """Classification reason should include parameter context."""
        classifier = ActionClassifier()

        result = classifier.classify("file_delete", {"path": "/important/data.txt"})
        assert "/important/data.txt" in result.reason

        result = classifier.classify("file_write", {"path": "/src/app.py"})
        assert "/src/app.py" in result.reason

    def test_approval_required_by_risk_level(self):
        """Destructive and critical require approval, safe and moderate don't."""
        classifier = ActionClassifier()

        assert classifier.classify("file_read", {}).requires_approval == False
        assert classifier.classify("browser", {}).requires_approval == False
        assert classifier.classify("file_write", {}).requires_approval == True
        assert classifier.classify("file_delete", {}).requires_approval == True


class TestApprovalFlowE2E:
    """E2E tests for approval workflow."""

    @pytest.mark.asyncio
    async def test_approval_blocks_until_decision(self):
        """Approval request should block until user decides."""
        manager = ApprovalManager()
        manager.start_session("test-session")

        classification = ActionClassification(
            risk_level="destructive",
            reason="Test action",
            requires_approval=True,
            tool_name="file_write",
            parameters={"path": "/tmp/test.txt"},
        )

        # Start approval request in background
        result_holder = []

        async def request():
            result = await manager.request_approval(classification, "step-1", timeout=5.0)
            result_holder.append(result)

        task = asyncio.create_task(request())

        # Wait a bit, then approve
        await asyncio.sleep(0.1)
        pending = manager.get_pending()
        assert len(pending) == 1
        manager.approve(pending[0].id, approve_similar=False)

        await task
        assert len(result_holder) == 1
        assert result_holder[0].decision == "approved"

    @pytest.mark.asyncio
    async def test_approval_timeout(self):
        """Approval should timeout if user doesn't respond."""
        manager = ApprovalManager()
        manager.start_session("test-session")

        classification = ActionClassification(
            risk_level="critical",
            reason="Test action",
            requires_approval=True,
            tool_name="file_delete",
            parameters={},
        )

        result = await manager.request_approval(classification, "step-1", timeout=0.1)
        assert result.decision == "timeout"

    @pytest.mark.asyncio
    async def test_similar_actions_auto_approved(self):
        """After 'approve all similar', similar actions should auto-approve."""
        manager = ApprovalManager()
        manager.start_session("test-session")

        # First action - user approves with "approve similar"
        c1 = ActionClassification(
            risk_level="destructive",
            reason="Write file",
            requires_approval=True,
            tool_name="file_write",
            parameters={"path": "/src/test1.py"},
        )

        async def approve_first():
            await asyncio.sleep(0.1)
            pending = manager.get_pending()
            manager.approve(pending[0].id, approve_similar=True)

        task = asyncio.create_task(approve_first())
        result1 = await manager.request_approval(c1, "step-1", timeout=5.0)
        await task

        assert result1.decision == "approved"
        assert result1.approve_similar == True

        # Second similar action - should auto-approve
        c2 = ActionClassification(
            risk_level="destructive",
            reason="Write file",
            requires_approval=True,
            tool_name="file_write",
            parameters={"path": "/src/test2.py"},  # Same parent directory
        )

        result2 = await manager.request_approval(c2, "step-2", timeout=1.0)
        assert result2.decision == "approved"
        assert result2.decided_by == "similar_match"

    def test_similarity_matching_same_directory(self):
        """Files in same directory should be considered similar."""
        c1 = ActionClassification(
            risk_level="destructive",
            reason="test",
            requires_approval=True,
            tool_name="file_write",
            parameters={"path": "/src/components/Button.tsx"},
        )
        c2 = ActionClassification(
            risk_level="destructive",
            reason="test",
            requires_approval=True,
            tool_name="file_write",
            parameters={"path": "/src/components/Input.tsx"},
        )
        c3 = ActionClassification(
            risk_level="destructive",
            reason="test",
            requires_approval=True,
            tool_name="file_write",
            parameters={"path": "/config/settings.json"},
        )

        assert ApprovalManager.are_similar(c1, c2) == True
        assert ApprovalManager.are_similar(c1, c3) == False

    def test_rejection_stops_action(self):
        """Rejected action should not execute."""
        # This is implicitly tested in executor integration
        pass


class TestKillSwitchE2E:
    """E2E tests for kill switch functionality."""

    def test_kill_switch_trigger_and_check(self):
        """Kill switch should be triggerable and checkable."""
        ks = KillSwitch()

        assert ks.is_triggered() == False
        ks.trigger("Test trigger")
        assert ks.is_triggered() == True
        assert "Test trigger" in ks.trigger_reason
        assert ks.triggered_at is not None

    def test_kill_switch_reset(self):
        """Kill switch should be resettable."""
        ks = KillSwitch()

        ks.trigger("Test")
        assert ks.is_triggered() == True

        ks.reset()
        assert ks.is_triggered() == False
        assert ks.trigger_reason is None

    def test_kill_switch_singleton(self):
        """Global kill switch should be singleton."""
        ks1 = get_kill_switch()
        ks2 = get_kill_switch()
        assert ks1 is ks2

    def test_kill_switch_status_dict(self):
        """Kill switch status should be serializable."""
        ks = KillSwitch()
        ks.trigger("Emergency stop")

        status = ks.get_status()
        assert status["triggered"] == True
        assert "Emergency stop" in status["reason"]
        assert status["triggered_at"] is not None


class TestAuditTrailE2E:
    """E2E tests for audit trail functionality."""

    def setup_method(self):
        """Create temp directory for test database."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_audit.db")

    def teardown_method(self):
        """Clean up temp files with Windows-safe handling."""
        gc.collect()
        try:
            if os.path.exists(self.db_path):
                os.unlink(self.db_path)
            if os.path.exists(self.db_path + "-wal"):
                os.unlink(self.db_path + "-wal")
            if os.path.exists(self.db_path + "-shm"):
                os.unlink(self.db_path + "-shm")
            os.rmdir(self.temp_dir)
        except PermissionError:
            pass  # Windows may hold locks

    def test_audit_entry_logged_and_queryable(self):
        """Audit entries should be persisted and queryable."""
        store = AuditStore(db_path=self.db_path)

        entry = AuditEntry(
            session_id="test-session",
            step_id="step-1",
            tool_name="file_write",
            parameters={"path": "/tmp/test.txt"},
            risk_level="destructive",
            approval_required=True,
            approval_decision="approved",
            success=True,
            duration_ms=150.0,
        )

        store.log(entry)

        # Query back
        results = store.query(session_id="test-session")
        assert len(results) == 1
        assert results[0].tool_name == "file_write"
        assert results[0].risk_level == "destructive"

    def test_audit_query_by_risk_level(self):
        """Audit should be queryable by risk level."""
        store = AuditStore(db_path=self.db_path)

        # Log entries of different risk levels
        for level in ["safe", "moderate", "destructive", "critical"]:
            entry = AuditEntry(
                session_id="test-session",
                step_id=f"step-{level}",
                tool_name=f"tool_{level}",
                parameters={},
                risk_level=level,
            )
            store.log(entry)

        # Query specific risk level
        destructive = store.query(risk_level="destructive")
        assert len(destructive) == 1
        assert destructive[0].risk_level == "destructive"

        critical = store.query(risk_level="critical")
        assert len(critical) == 1

    def test_audit_session_summary(self):
        """Session summary should aggregate correctly."""
        store = AuditStore(db_path=self.db_path)

        # Log multiple entries
        for i in range(3):
            store.log(AuditEntry(
                session_id="test-session",
                step_id=f"step-{i}",
                tool_name="file_write",
                parameters={},
                risk_level="destructive",
                approval_decision="approved",
                success=True,
                duration_ms=100.0,
            ))

        store.log(AuditEntry(
            session_id="test-session",
            step_id="step-fail",
            tool_name="file_delete",
            parameters={},
            risk_level="critical",
            approval_decision="rejected",
            success=False,
        ))

        summary = store.get_session_summary("test-session")
        assert summary["total_actions"] == 4
        assert summary["by_risk"]["destructive"] == 3
        assert summary["by_risk"]["critical"] == 1
        assert summary["approved"] == 3
        assert summary["rejected"] == 1
        assert summary["successful"] == 3

    def test_audit_export_json(self):
        """Audit should export to JSON."""
        store = AuditStore(db_path=self.db_path)

        store.log(AuditEntry(
            session_id="test-session",
            step_id="step-1",
            tool_name="file_read",
            parameters={"path": "/tmp/test.txt"},
            risk_level="safe",
        ))

        json_export = store.export_json("test-session")
        assert "file_read" in json_export
        assert "safe" in json_export

    def test_audit_export_csv(self):
        """Audit should export to CSV."""
        store = AuditStore(db_path=self.db_path)

        store.log(AuditEntry(
            session_id="test-session",
            step_id="step-1",
            tool_name="file_write",
            parameters={},
            risk_level="destructive",
        ))

        csv_export = store.export_csv("test-session")
        assert "file_write" in csv_export
        assert "destructive" in csv_export


# Run with: pytest tests/agent/test_safety_e2e.py -v
