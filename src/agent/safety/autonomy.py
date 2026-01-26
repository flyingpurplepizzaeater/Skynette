"""
Autonomy Level System

Defines autonomy levels (L1-L4) with threshold mappings for auto-execution
and provides a service to manage the current level per project.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Literal, Optional

from src.agent.safety.allowlist import AutonomyRule, matches_rules
from src.agent.safety.classification import RiskLevel
from src.data.storage import get_storage


# Autonomy level type using Literal (per 07-01 decision pattern)
AutonomyLevel = Literal["L1", "L2", "L3", "L4"]


# Threshold mappings: which risk levels auto-execute at each autonomy level
AUTONOMY_THRESHOLDS: dict[AutonomyLevel, set[RiskLevel]] = {
    "L1": set(),                              # Nothing auto-executes (suggest only)
    "L2": {"safe"},                           # Only safe auto-executes
    "L3": {"safe", "moderate"},               # Safe + moderate auto-execute
    "L4": {"safe", "moderate", "destructive"},  # Only critical requires approval
}


# Human-readable labels for each level
AUTONOMY_LABELS: dict[AutonomyLevel, str] = {
    "L1": "Assistant",    # Most cautious - agent suggests only
    "L2": "Collaborator", # Default - safe actions auto-execute
    "L3": "Trusted",      # More autonomy for trusted projects
    "L4": "Expert",       # High autonomy - only critical needs approval
}


# Colors that harmonize with existing RISK_COLORS
AUTONOMY_COLORS: dict[AutonomyLevel, str] = {
    "L1": "#3B82F6",  # Blue - most cautious
    "L2": "#10B981",  # Emerald - collaborative (default)
    "L3": "#F59E0B",  # Amber - trusted
    "L4": "#EF4444",  # Red - expert/high autonomy
}


# Level order for comparison (higher index = more autonomous)
_LEVEL_ORDER: list[AutonomyLevel] = ["L1", "L2", "L3", "L4"]


@dataclass
class AutonomySettings:
    """Settings for a project's autonomy configuration."""

    level: AutonomyLevel = "L2"  # Default to Collaborator
    allowlist_rules: list = field(default_factory=list)  # Placeholder for Plan 04
    blocklist_rules: list = field(default_factory=list)  # Placeholder for Plan 04

    def auto_executes(self, risk_level: RiskLevel) -> bool:
        """Check if given risk level auto-executes at current autonomy level."""
        return risk_level in AUTONOMY_THRESHOLDS[self.level]

    def check_rules(self, tool_name: str, params: dict) -> bool | None:
        """
        Check allowlist/blocklist rules for a specific tool call.

        Args:
            tool_name: Name of the tool being called
            params: Tool parameters

        Returns:
            True if explicitly allowed (skip approval)
            False if explicitly blocked (require approval)
            None if no rule matches (use autonomy level)
        """
        # Convert dict rules to AutonomyRule objects if needed
        allowlist = [
            AutonomyRule.from_dict(r) if isinstance(r, dict) else r
            for r in self.allowlist_rules
        ]
        blocklist = [
            AutonomyRule.from_dict(r) if isinstance(r, dict) else r
            for r in self.blocklist_rules
        ]

        return matches_rules(tool_name, params, allowlist, blocklist)


class AutonomyLevelService:
    """Service for managing autonomy levels per project."""

    def __init__(self) -> None:
        """Initialize the autonomy level service."""
        self._current_levels: dict[str, AutonomyLevel] = {}  # project path -> level
        self._level_changed_callbacks: list[Callable[[str, AutonomyLevel, AutonomyLevel], None]] = []

    def get_settings(self, project_path: str | None = None) -> AutonomySettings:
        """
        Get autonomy settings for a project.

        Args:
            project_path: Project directory path, or None for global default

        Returns:
            AutonomySettings for the project
        """
        if project_path is None:
            # Return global defaults
            return AutonomySettings(level=self.get_default_level())

        # Check in-memory cache first
        normalized = str(Path(project_path).resolve())
        if normalized in self._current_levels:
            cached_level = self._current_levels[normalized]
            # Load full settings from storage but use cached level
            storage = get_storage()
            data = storage.get_project_autonomy(normalized)
            return AutonomySettings(
                level=cached_level,
                allowlist_rules=data.get("allowlist", []),
                blocklist_rules=data.get("blocklist", []),
            )

        # Load from storage
        storage = get_storage()
        data = storage.get_project_autonomy(project_path)

        return AutonomySettings(
            level=data.get("level", self.get_default_level()),
            allowlist_rules=data.get("allowlist", []),
            blocklist_rules=data.get("blocklist", []),
        )

    def set_level(self, project_path: str, level: AutonomyLevel) -> None:
        """
        Set autonomy level for a project.

        Persists to storage and notifies callbacks on downgrade.

        Args:
            project_path: Project directory path
            level: New autonomy level
        """
        normalized = str(Path(project_path).resolve())
        old_level = self._current_levels.get(normalized, self.get_default_level())
        self._current_levels[normalized] = level

        # Persist to storage
        storage = get_storage()
        storage.set_project_autonomy(normalized, level)

        # Notify callbacks on downgrade
        if self._is_downgrade(old_level, level):
            for callback in self._level_changed_callbacks:
                callback(project_path, old_level, level, downgrade=True)

    def get_default_level(self) -> AutonomyLevel:
        """Get the global default autonomy level."""
        storage = get_storage()
        level = storage.get_setting("default_autonomy_level", "L2")
        if level in ("L1", "L2", "L3", "L4"):
            return level  # type: ignore
        return "L2"

    def on_level_changed(
        self, callback: Callable[[str, AutonomyLevel, AutonomyLevel], None]
    ) -> None:
        """
        Register a callback for level changes.

        Args:
            callback: Function called with (project_path, old_level, new_level)
        """
        self._level_changed_callbacks.append(callback)

    def _is_downgrade(self, old: AutonomyLevel, new: AutonomyLevel) -> bool:
        """
        Check if level change is more restrictive (downgrade).

        Args:
            old: Previous autonomy level
            new: New autonomy level

        Returns:
            True if new level is more restrictive than old
        """
        return _LEVEL_ORDER.index(new) < _LEVEL_ORDER.index(old)


# Module-level singleton
_global_autonomy_service: Optional[AutonomyLevelService] = None


def get_autonomy_service() -> AutonomyLevelService:
    """Get the global autonomy level service singleton."""
    global _global_autonomy_service
    if _global_autonomy_service is None:
        _global_autonomy_service = AutonomyLevelService()
    return _global_autonomy_service
