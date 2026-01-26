"""
Tests for YOLO (L5) mode functionality.
"""

import gc
import json
import tempfile
from pathlib import Path

import pytest

from src.agent.safety.autonomy import (
    AutonomyLevel,
    AutonomyLevelService,
    AutonomySettings,
    AUTONOMY_THRESHOLDS,
    AUTONOMY_LABELS,
    AUTONOMY_COLORS,
)
from src.agent.safety.classification import ActionClassifier
from src.agent.safety.audit import AuditStore, AuditEntry


class TestL5AutonomyLevel:
    """Tests for L5 autonomy level types and constants."""

    def test_l5_in_thresholds(self):
        """L5 exists in AUTONOMY_THRESHOLDS."""
        assert "L5" in AUTONOMY_THRESHOLDS

    def test_l5_auto_executes_all_risk_levels(self):
        """L5 threshold includes all risk levels."""
        l5_threshold = AUTONOMY_THRESHOLDS["L5"]
        assert "safe" in l5_threshold
        assert "moderate" in l5_threshold
        assert "destructive" in l5_threshold
        assert "critical" in l5_threshold

    def test_l5_has_yolo_label(self):
        """L5 has 'YOLO' label."""
        assert AUTONOMY_LABELS["L5"] == "YOLO"

    def test_l5_has_purple_color(self):
        """L5 has purple color (#8B5CF6)."""
        assert AUTONOMY_COLORS["L5"] == "#8B5CF6"

    def test_autonomy_settings_l5_auto_executes(self):
        """AutonomySettings with L5 auto-executes all risk levels."""
        settings = AutonomySettings(level="L5")
        assert settings.auto_executes("safe") is True
        assert settings.auto_executes("moderate") is True
        assert settings.auto_executes("destructive") is True
        assert settings.auto_executes("critical") is True


class TestL5Classification:
    """Tests for L5 classification bypass."""

    def test_l5_bypasses_approval_for_safe(self):
        """L5 does not require approval for safe actions."""
        class MockService:
            def get_settings(self, p): return AutonomySettings(level="L5")

        classifier = ActionClassifier(autonomy_service=MockService())
        result = classifier.classify("web_search", {})
        assert result.requires_approval is False

    def test_l5_bypasses_approval_for_moderate(self):
        """L5 does not require approval for moderate actions."""
        class MockService:
            def get_settings(self, p): return AutonomySettings(level="L5")

        classifier = ActionClassifier(autonomy_service=MockService())
        result = classifier.classify("browser", {"url": "http://test.com"})
        assert result.requires_approval is False

    def test_l5_bypasses_approval_for_destructive(self):
        """L5 does not require approval for destructive actions."""
        class MockService:
            def get_settings(self, p): return AutonomySettings(level="L5")

        classifier = ActionClassifier(autonomy_service=MockService())
        result = classifier.classify("file_write", {"path": "/tmp/test"})
        assert result.requires_approval is False

    def test_l5_bypasses_approval_for_critical(self):
        """L5 does not require approval for critical actions."""
        class MockService:
            def get_settings(self, p): return AutonomySettings(level="L5")

        classifier = ActionClassifier(autonomy_service=MockService())
        result = classifier.classify("file_delete", {"path": "/important"})
        assert result.requires_approval is False

    def test_l5_bypasses_blocklist_rules(self):
        """L5 ignores blocklist rules (true YOLO)."""
        class MockService:
            def get_settings(self, p):
                return AutonomySettings(
                    level="L5",
                    blocklist_rules=[{"type": "block", "rule_type": "path", "pattern": "*"}]
                )

        classifier = ActionClassifier(autonomy_service=MockService())
        result = classifier.classify("file_delete", {"path": "/blocked"})
        # L5 should bypass the blocklist
        assert result.requires_approval is False


class TestL5SessionBehavior:
    """Tests for session-only L5 behavior."""

    def test_l5_tracked_in_session(self):
        """L5 is tracked in session projects set."""
        svc = AutonomyLevelService()
        path = tempfile.mkdtemp()

        svc.set_level(path, "L5")
        assert svc.is_yolo_active(path) is True

    def test_l5_returns_l5_settings(self):
        """get_settings returns L5 for session YOLO projects."""
        svc = AutonomyLevelService()
        path = tempfile.mkdtemp()

        svc.set_level(path, "L5")
        settings = svc.get_settings(path)
        assert settings.level == "L5"

    def test_downgrade_from_l5_clears_session(self):
        """Downgrading from L5 removes session tracking."""
        svc = AutonomyLevelService()
        path = tempfile.mkdtemp()

        svc.set_level(path, "L5")
        assert svc.is_yolo_active(path) is True

        svc.set_level(path, "L2")
        assert svc.is_yolo_active(path) is False

    def test_is_yolo_active_returns_false_for_none_path(self):
        """is_yolo_active returns False for None path."""
        svc = AutonomyLevelService()
        assert svc.is_yolo_active(None) is False

    def test_l4_is_not_yolo(self):
        """L4 is not tracked as YOLO."""
        svc = AutonomyLevelService()
        path = tempfile.mkdtemp()

        svc.set_level(path, "L4")
        assert svc.is_yolo_active(path) is False

    def test_l5_not_persisted_to_storage(self):
        """L5 is session-only and not persisted to storage."""
        svc = AutonomyLevelService()
        path = tempfile.mkdtemp()

        # Set L5 level
        svc.set_level(path, "L5")

        # Create fresh service to simulate restart
        svc2 = AutonomyLevelService()

        # L5 should not be persisted, new instance shouldn't see it
        assert svc2.is_yolo_active(path) is False

    def test_l5_clears_on_downgrade_to_l1(self):
        """L5 clears when downgrading to L1."""
        svc = AutonomyLevelService()
        path = tempfile.mkdtemp()

        svc.set_level(path, "L5")
        assert svc.is_yolo_active(path) is True

        svc.set_level(path, "L1")
        assert svc.is_yolo_active(path) is False

    def test_upgrade_callback_not_downgrade(self):
        """Upgrading to L5 does not trigger downgrade callback."""
        svc = AutonomyLevelService()
        path = tempfile.mkdtemp()
        callback_data = []

        def callback(p, old, new, downgrade):
            callback_data.append((p, old, new, downgrade))

        svc.on_level_changed(callback)
        svc._current_levels[str(Path(path).resolve())] = "L2"

        # Upgrade to L5
        svc.set_level(path, "L5")

        # Should have callback but downgrade=False
        assert len(callback_data) == 1
        assert callback_data[0][3] is False  # Not a downgrade


class TestYoloAuditLogging:
    """Tests for YOLO audit logging enhancements."""

    def setup_method(self):
        """Create temp database for each test."""
        self.db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.db_file.name
        self.db_file.close()
        self.store = AuditStore(db_path=self.db_path)

    def teardown_method(self):
        """Clean up temp database."""
        del self.store
        gc.collect()
        try:
            Path(self.db_path).unlink()
        except PermissionError:
            pass  # Windows cleanup handling

    def test_audit_entry_has_yolo_mode_field(self):
        """AuditEntry has yolo_mode field."""
        entry = AuditEntry(
            session_id="test",
            step_id="step1",
            tool_name="test",
            risk_level="safe",
            yolo_mode=True,
        )
        assert entry.yolo_mode is True

    def test_yolo_entry_stored_with_flag(self):
        """YOLO entries persist yolo_mode flag."""
        entry = AuditEntry(
            session_id="yolo-session",
            step_id="step1",
            tool_name="file_delete",
            risk_level="critical",
            yolo_mode=True,
            parameters={"path": "/test"},
        )
        self.store.log(entry)

        entries = self.store.query(session_id="yolo-session")
        assert len(entries) == 1
        assert entries[0].yolo_mode is True

    def test_yolo_entry_stores_full_parameters(self):
        """YOLO entries store full_parameters without truncation."""
        # Create large parameters that would normally be truncated
        large_content = "x" * 10000  # 10KB, larger than 4KB limit
        entry = AuditEntry(
            session_id="yolo-full",
            step_id="step1",
            tool_name="file_write",
            risk_level="destructive",
            yolo_mode=True,
            parameters={"path": "/test", "content": large_content},
        )
        self.store.log(entry)

        entries = self.store.query(session_id="yolo-full")
        assert len(entries) == 1
        assert entries[0].full_parameters is not None
        # Full parameters should contain the full content
        full_params = json.loads(entries[0].full_parameters)
        assert len(full_params.get("content", "")) == 10000

    def test_non_yolo_entry_no_full_parameters(self):
        """Non-YOLO entries don't store full_parameters."""
        entry = AuditEntry(
            session_id="normal-session",
            step_id="step1",
            tool_name="file_write",
            risk_level="destructive",
            yolo_mode=False,
            parameters={"path": "/test"},
        )
        self.store.log(entry)

        entries = self.store.query(session_id="normal-session")
        assert len(entries) == 1
        assert entries[0].full_parameters is None

    def test_yolo_retention_constant_exists(self):
        """AuditStore has YOLO_RETENTION_DAYS constant."""
        assert hasattr(AuditStore, "YOLO_RETENTION_DAYS")
        assert AuditStore.YOLO_RETENTION_DAYS > AuditStore.DEFAULT_RETENTION_DAYS

    def test_yolo_retention_is_90_days(self):
        """YOLO retention is 90 days (3x standard)."""
        assert AuditStore.YOLO_RETENTION_DAYS == 90
        assert AuditStore.DEFAULT_RETENTION_DAYS == 30

    def test_yolo_entry_default_false(self):
        """yolo_mode defaults to False."""
        entry = AuditEntry(
            session_id="test",
            step_id="step1",
            tool_name="test",
            risk_level="safe",
        )
        assert entry.yolo_mode is False

    def test_to_dict_includes_yolo_fields(self):
        """to_dict includes yolo_mode and full_parameters."""
        entry = AuditEntry(
            session_id="test",
            step_id="step1",
            tool_name="test",
            risk_level="safe",
            yolo_mode=True,
            full_parameters='{"key": "value"}',
        )
        data = entry.to_dict()
        assert "yolo_mode" in data
        assert data["yolo_mode"] is True
        assert "full_parameters" in data


class TestL5DowngradeCallback:
    """Tests for L5 downgrade callback behavior."""

    def test_downgrade_from_l5_triggers_callback(self):
        """Downgrading from L5 triggers callback with downgrade=True."""
        svc = AutonomyLevelService()
        path = tempfile.mkdtemp()
        callback_data = []

        def callback(p, old, new, downgrade):
            callback_data.append((p, old, new, downgrade))

        svc.on_level_changed(callback)

        # Set L5 first
        svc.set_level(path, "L5")

        # Downgrade to L2
        svc.set_level(path, "L2")

        # Should have two callbacks: upgrade to L5 (downgrade=False), downgrade to L2 (downgrade=True)
        assert len(callback_data) == 2
        # First callback: default L2 -> L5, not downgrade
        assert callback_data[0][2] == "L5"
        assert callback_data[0][3] is False
        # Second callback: L5 -> L2, is downgrade
        assert callback_data[1][1] == "L5"
        assert callback_data[1][2] == "L2"
        assert callback_data[1][3] is True
