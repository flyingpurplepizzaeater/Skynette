"""
Agent UI Components

Flet components for agent interaction.
"""

from src.agent.ui.agent_panel import AgentPanel
from src.agent.ui.approval_detail_levels import (
    render_minimal,
    render_detailed,
    render_progressive,
    render_by_level,
)
from src.agent.ui.approval_sheet import ApprovalSheet
from src.agent.ui.cancel_dialog import CancelDialog
from src.agent.ui.panel_preferences import (
    PanelPreferences,
    get_panel_preferences,
    save_panel_preferences,
)
from src.agent.ui.plan_views import PlanListView, PlanTreeView, PlanViewSwitcher
from src.agent.ui.risk_badge import RiskBadge
from src.agent.ui.status_indicator import AgentStatusIndicator
from src.agent.ui.step_views import (
    StepChecklistView,
    StepTimelineView,
    StepCardsView,
    StepViewSwitcher,
)

__all__ = [
    "AgentPanel",
    "AgentStatusIndicator",
    "ApprovalSheet",
    "CancelDialog",
    "PanelPreferences",
    "PlanListView",
    "PlanTreeView",
    "PlanViewSwitcher",
    "RiskBadge",
    "StepCardsView",
    "StepChecklistView",
    "StepTimelineView",
    "StepViewSwitcher",
    "get_panel_preferences",
    "render_by_level",
    "render_detailed",
    "render_minimal",
    "render_progressive",
    "save_panel_preferences",
]
