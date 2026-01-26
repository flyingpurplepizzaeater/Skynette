"""
Autonomy Level System

Defines autonomy levels (L1-L4) with threshold mappings for auto-execution
and provides a service to manage the current level per project.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Literal, Optional

from src.agent.safety.classification import RiskLevel


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

        Returns:
            True if explicitly allowed by allowlist
            False if explicitly blocked by blocklist
            None if no rule matches (use default level behavior)

        Note: Implemented in Plan 04 - returns None for now.
        """
        return None


class AutonomyLevelService:
    """Service for managing autonomy levels per project."""

    def __init__(self) -> None:
        """Initialize the autonomy level service."""
        self._current_levels: dict[str, AutonomyLevel] = {}  # project path -> level
        self._level_changed_callbacks: list[Callable[[str, AutonomyLevel, AutonomyLevel], None]] = []

    def get_settings(self, project_path: str | None) -> AutonomySettings:
        """
        Get autonomy settings for a project.

        Args:
            project_path: Project path, or None for global default

        Returns:
            AutonomySettings with the appropriate level
        """
        if project_path is None:
            return AutonomySettings(level=self.get_default_level())

        # Normalize path
        normalized = str(Path(project_path).resolve())

        # Get level from cache or use default
        level = self._current_levels.get(normalized, self.get_default_level())
        return AutonomySettings(level=level)

    def set_level(self, project_path: str, level: AutonomyLevel) -> None:
        """
        Set autonomy level for a project.

        Args:
            project_path: Project path to set level for
            level: New autonomy level
        """
        # Normalize path
        normalized = str(Path(project_path).resolve())

        # Get old level for callbacks
        old_level = self._current_levels.get(normalized, self.get_default_level())

        # Update cache
        self._current_levels[normalized] = level

        # Notify callbacks if level changed
        if old_level != level:
            for callback in self._level_changed_callbacks:
                callback(normalized, old_level, level)

    def get_default_level(self) -> AutonomyLevel:
        """Get the global default autonomy level."""
        return "L2"  # Collaborator - safe actions auto-execute

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
