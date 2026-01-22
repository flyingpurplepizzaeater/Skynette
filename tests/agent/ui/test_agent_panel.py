"""Tests for AgentPanel and PanelPreferences."""

import gc
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestPanelPreferences:
    """Tests for PanelPreferences defaults and persistence."""

    def test_panel_preferences_defaults(self):
        """Test preference defaults without storage."""
        with patch("src.agent.ui.panel_preferences.get_storage") as mock_get_storage:
            mock_storage = MagicMock()
            mock_storage.get_setting.return_value = None
            mock_get_storage.return_value = mock_storage

            # Need to reimport to use the patched storage
            from src.agent.ui.panel_preferences import get_panel_preferences

            prefs = get_panel_preferences(mock_storage)

            assert prefs.width == 350
            assert prefs.visible is True
            assert prefs.step_view_mode == "checklist"
            assert prefs.plan_view_mode == "list"
            assert prefs.approval_detail_level == "detailed"

    def test_panel_preferences_loads_from_storage(self):
        """Test preferences load correctly from storage."""
        mock_storage = MagicMock()
        mock_storage.get_setting.side_effect = lambda key: {
            "agent_panel_width": "400",
            "agent_panel_visible": "0",
            "agent_panel_step_view_mode": "timeline",
            "agent_panel_plan_view_mode": "tree",
            "agent_panel_approval_detail_level": "minimal",
        }.get(key)

        from src.agent.ui.panel_preferences import get_panel_preferences

        prefs = get_panel_preferences(mock_storage)

        assert prefs.width == 400
        assert prefs.visible is False
        assert prefs.step_view_mode == "timeline"
        assert prefs.plan_view_mode == "tree"
        assert prefs.approval_detail_level == "minimal"

    def test_panel_preferences_width_bounds(self):
        """Test width is clamped to MIN/MAX bounds."""
        mock_storage = MagicMock()

        # Test below MIN
        mock_storage.get_setting.side_effect = lambda key: {
            "agent_panel_width": "100",  # Below MIN of 280
        }.get(key)

        from src.agent.ui.panel_preferences import get_panel_preferences

        prefs = get_panel_preferences(mock_storage)
        assert prefs.width == 280  # Clamped to MIN

        # Test above MAX
        mock_storage.get_setting.side_effect = lambda key: {
            "agent_panel_width": "800",  # Above MAX of 600
        }.get(key)

        prefs = get_panel_preferences(mock_storage)
        assert prefs.width == 600  # Clamped to MAX

    def test_save_panel_preferences(self):
        """Test preferences are saved correctly."""
        mock_storage = MagicMock()

        from src.agent.ui.panel_preferences import PanelPreferences, save_panel_preferences

        prefs = PanelPreferences(
            width=420,
            visible=False,
            step_view_mode="cards",
            plan_view_mode="tree",
            approval_detail_level="progressive",
        )

        save_panel_preferences(prefs, mock_storage)

        # Verify all settings were saved
        calls = {call[0][0]: call[0][1] for call in mock_storage.set_setting.call_args_list}
        assert calls["agent_panel_width"] == "420"
        assert calls["agent_panel_visible"] == "0"
        assert calls["agent_panel_step_view_mode"] == "cards"
        assert calls["agent_panel_plan_view_mode"] == "tree"
        assert calls["agent_panel_approval_detail_level"] == "progressive"


class TestAgentPanelImports:
    """Tests for AgentPanel imports and exports."""

    def test_agent_panel_imports(self):
        """Test AgentPanel can be imported."""
        from src.agent.ui import AgentPanel, PanelPreferences

        assert AgentPanel is not None
        assert PanelPreferences is not None

    def test_all_exports_available(self):
        """Test all expected exports are available."""
        from src.agent.ui import (
            AgentPanel,
            AgentStatusIndicator,
            ApprovalSheet,
            CancelDialog,
            PanelPreferences,
            RiskBadge,
            get_panel_preferences,
            save_panel_preferences,
        )

        assert AgentPanel is not None
        assert AgentStatusIndicator is not None
        assert ApprovalSheet is not None
        assert CancelDialog is not None
        assert PanelPreferences is not None
        assert RiskBadge is not None
        assert get_panel_preferences is not None
        assert save_panel_preferences is not None

    def test_panel_preferences_dataclass(self):
        """Test PanelPreferences is a proper dataclass."""
        from src.agent.ui import PanelPreferences

        prefs = PanelPreferences()

        # Check all fields exist with defaults
        assert hasattr(prefs, "width")
        assert hasattr(prefs, "visible")
        assert hasattr(prefs, "step_view_mode")
        assert hasattr(prefs, "plan_view_mode")
        assert hasattr(prefs, "approval_detail_level")

        # Check constraints exist
        assert hasattr(prefs, "MIN_WIDTH")
        assert hasattr(prefs, "MAX_WIDTH")
        assert prefs.MIN_WIDTH == 280
        assert prefs.MAX_WIDTH == 600
