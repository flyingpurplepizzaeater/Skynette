"""
Tests for Autonomy Level System

Covers: AutonomyLevel, AUTONOMY_THRESHOLDS, AutonomySettings, AutonomyLevelService
"""

import gc
import tempfile
from pathlib import Path

import pytest

from src.agent.safety.autonomy import (
    AutonomyLevel,
    AutonomySettings,
    AutonomyLevelService,
    AUTONOMY_COLORS,
    AUTONOMY_LABELS,
    AUTONOMY_THRESHOLDS,
    get_autonomy_service,
)
from src.data.storage import WorkflowStorage


class TestAutonomyThresholds:
    """Test autonomy level threshold mappings."""

    def test_l1_no_auto_execute(self):
        """L1 (Assistant) should auto-execute nothing."""
        assert AUTONOMY_THRESHOLDS["L1"] == set()

    def test_l2_safe_only(self):
        """L2 (Collaborator) should auto-execute only safe actions."""
        assert AUTONOMY_THRESHOLDS["L2"] == {"safe"}

    def test_l3_safe_and_moderate(self):
        """L3 (Trusted) should auto-execute safe and moderate actions."""
        assert AUTONOMY_THRESHOLDS["L3"] == {"safe", "moderate"}

    def test_l4_not_critical(self):
        """L4 (Expert) should auto-execute everything except critical."""
        assert AUTONOMY_THRESHOLDS["L4"] == {"safe", "moderate", "destructive"}

    def test_all_levels_have_labels(self):
        """All levels should have human-readable labels."""
        for level in ["L1", "L2", "L3", "L4"]:
            assert level in AUTONOMY_LABELS
            assert len(AUTONOMY_LABELS[level]) > 0

    def test_all_levels_have_colors(self):
        """All levels should have color codes."""
        for level in ["L1", "L2", "L3", "L4"]:
            assert level in AUTONOMY_COLORS
            assert AUTONOMY_COLORS[level].startswith("#")


class TestAutonomySettings:
    """Test AutonomySettings dataclass."""

    def test_default_level_is_l2(self):
        """Default autonomy level should be L2 (Collaborator)."""
        settings = AutonomySettings()
        assert settings.level == "L2"

    def test_auto_executes_l1(self):
        """L1 should not auto-execute any risk level."""
        settings = AutonomySettings(level="L1")
        assert not settings.auto_executes("safe")
        assert not settings.auto_executes("moderate")
        assert not settings.auto_executes("destructive")
        assert not settings.auto_executes("critical")

    def test_auto_executes_l2(self):
        """L2 should only auto-execute safe."""
        settings = AutonomySettings(level="L2")
        assert settings.auto_executes("safe")
        assert not settings.auto_executes("moderate")
        assert not settings.auto_executes("destructive")
        assert not settings.auto_executes("critical")

    def test_auto_executes_l3(self):
        """L3 should auto-execute safe and moderate."""
        settings = AutonomySettings(level="L3")
        assert settings.auto_executes("safe")
        assert settings.auto_executes("moderate")
        assert not settings.auto_executes("destructive")
        assert not settings.auto_executes("critical")

    def test_auto_executes_l4(self):
        """L4 should auto-execute everything except critical."""
        settings = AutonomySettings(level="L4")
        assert settings.auto_executes("safe")
        assert settings.auto_executes("moderate")
        assert settings.auto_executes("destructive")
        assert not settings.auto_executes("critical")

    def test_check_rules_returns_none_when_empty(self):
        """check_rules should return None when no rules defined."""
        settings = AutonomySettings()
        assert settings.check_rules("any_tool", {}) is None


class TestAutonomyLevelService:
    """Test AutonomyLevelService."""

    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage for testing."""
        temp_dir = tempfile.mkdtemp()
        storage = WorkflowStorage(temp_dir)
        yield storage
        # Cleanup
        gc.collect()  # Windows SQLite cleanup per 09-06

    @pytest.fixture
    def service(self):
        """Create fresh service instance."""
        return AutonomyLevelService()

    def test_get_settings_default(self, service):
        """get_settings with None should return default L2."""
        settings = service.get_settings(None)
        assert settings.level == "L2"

    def test_set_and_get_level(self, service, temp_storage):
        """set_level should update level and persist."""
        project = str(Path(tempfile.mkdtemp()).resolve())
        service.set_level(project, "L3")

        # Should be in cache
        assert service._current_levels.get(project) == "L3"

    def test_is_downgrade(self, service):
        """_is_downgrade should correctly identify downgrades."""
        # L4 -> L1 is downgrade
        assert service._is_downgrade("L4", "L1")
        # L3 -> L2 is downgrade
        assert service._is_downgrade("L3", "L2")
        # L1 -> L4 is upgrade (not downgrade)
        assert not service._is_downgrade("L1", "L4")
        # Same level is not downgrade
        assert not service._is_downgrade("L2", "L2")

    def test_level_changed_callback(self, service):
        """Downgrade should trigger callback."""
        callback_data = []

        def callback(path, old, new, downgrade):
            callback_data.append((path, old, new, downgrade))

        service.on_level_changed(callback)
        project = str(Path(tempfile.mkdtemp()).resolve())

        # Set initial level
        service._current_levels[project] = "L4"

        # Downgrade to L2
        service.set_level(project, "L2")

        assert len(callback_data) == 1
        assert callback_data[0][0] == project
        assert callback_data[0][1] == "L4"
        assert callback_data[0][2] == "L2"
        assert callback_data[0][3] is True  # downgrade=True


class TestGlobalService:
    """Test global service singleton."""

    def test_singleton(self):
        """get_autonomy_service should return same instance."""
        svc1 = get_autonomy_service()
        svc2 = get_autonomy_service()
        assert svc1 is svc2
