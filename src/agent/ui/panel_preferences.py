"""
Agent Panel Preferences

Persist agent panel state using WorkflowStorage.
"""

from dataclasses import dataclass
from typing import Literal

from src.data.storage import WorkflowStorage, get_storage


@dataclass
class PanelPreferences:
    """Agent panel user preferences."""

    width: int = 350
    visible: bool = True
    step_view_mode: Literal["checklist", "timeline", "cards"] = "checklist"
    plan_view_mode: Literal["list", "tree"] = "list"
    approval_detail_level: Literal["minimal", "detailed", "progressive"] = "detailed"

    # Width constraints
    MIN_WIDTH: int = 280
    MAX_WIDTH: int = 600


def get_panel_preferences(storage: WorkflowStorage | None = None) -> PanelPreferences:
    """
    Load panel preferences from storage.

    Args:
        storage: Optional storage instance (uses global if not provided)

    Returns:
        PanelPreferences with values from storage or defaults
    """
    if storage is None:
        storage = get_storage()

    width_str = storage.get_setting("agent_panel_width")
    visible_str = storage.get_setting("agent_panel_visible")
    step_view = storage.get_setting("agent_panel_step_view_mode")
    plan_view = storage.get_setting("agent_panel_plan_view_mode")
    approval_level = storage.get_setting("agent_panel_approval_detail_level")

    prefs = PanelPreferences()

    # Parse width with bounds checking
    if width_str is not None:
        try:
            width = int(width_str)
            prefs.width = max(prefs.MIN_WIDTH, min(prefs.MAX_WIDTH, width))
        except ValueError:
            pass  # Keep default

    # Parse visibility
    if visible_str is not None:
        prefs.visible = visible_str == "1"

    # Parse step view mode
    if step_view in ("checklist", "timeline", "cards"):
        prefs.step_view_mode = step_view  # type: ignore

    # Parse plan view mode
    if plan_view in ("list", "tree"):
        prefs.plan_view_mode = plan_view  # type: ignore

    # Parse approval detail level
    if approval_level in ("minimal", "detailed", "progressive"):
        prefs.approval_detail_level = approval_level  # type: ignore

    return prefs


def save_panel_preferences(
    prefs: PanelPreferences, storage: WorkflowStorage | None = None
) -> None:
    """
    Save panel preferences to storage.

    Args:
        prefs: Panel preferences to save
        storage: Optional storage instance (uses global if not provided)
    """
    if storage is None:
        storage = get_storage()

    # Ensure width is within bounds
    width = max(prefs.MIN_WIDTH, min(prefs.MAX_WIDTH, prefs.width))

    storage.set_setting("agent_panel_width", str(width))
    storage.set_setting("agent_panel_visible", "1" if prefs.visible else "0")
    storage.set_setting("agent_panel_step_view_mode", prefs.step_view_mode)
    storage.set_setting("agent_panel_plan_view_mode", prefs.plan_view_mode)
    storage.set_setting("agent_panel_approval_detail_level", prefs.approval_detail_level)
