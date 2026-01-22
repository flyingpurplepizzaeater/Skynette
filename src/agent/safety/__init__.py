"""
Safety Module

Action classification and approval systems for agent safety.
"""

from src.agent.safety.classification import (
    ActionClassification,
    ActionClassifier,
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
    "RiskLevel",
    "get_kill_switch",
]
