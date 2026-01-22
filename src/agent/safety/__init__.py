"""
Safety Module

Action classification and approval systems for agent safety.
"""

from src.agent.safety.classification import (
    ActionClassification,
    ActionClassifier,
    RISK_COLORS,
    RISK_LABELS,
    RiskLevel,
)
from src.agent.safety.kill_switch import (
    KillSwitch,
    get_kill_switch,
)

__all__ = [
    "ActionClassification",
    "ActionClassifier",
    "KillSwitch",
    "RISK_COLORS",
    "RISK_LABELS",
    "RiskLevel",
    "get_kill_switch",
]
