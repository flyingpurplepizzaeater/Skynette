"""
Safety Module

Action classification and approval systems for agent safety.
"""

from src.agent.safety.approval import (
    ApprovalDecision,
    ApprovalManager,
    ApprovalRequest,
    ApprovalResult,
    get_approval_manager,
)
from src.agent.safety.audit import (
    AuditEntry,
    AuditStore,
    get_audit_store,
)
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
from src.agent.safety.allowlist import (
    AutonomyRule,
    matches_rules,
)
from src.agent.safety.autonomy import (
    AutonomyLevel,
    AutonomySettings,
    AutonomyLevelService,
    AUTONOMY_COLORS,
    AUTONOMY_LABELS,
    AUTONOMY_THRESHOLDS,
    get_autonomy_service,
)

__all__ = [
    "ActionClassification",
    "ActionClassifier",
    "ApprovalDecision",
    "ApprovalManager",
    "ApprovalRequest",
    "ApprovalResult",
    "AuditEntry",
    "AuditStore",
    "AutonomyLevel",
    "AutonomyLevelService",
    "AutonomyRule",
    "AutonomySettings",
    "AUTONOMY_COLORS",
    "AUTONOMY_LABELS",
    "AUTONOMY_THRESHOLDS",
    "KillSwitch",
    "RISK_COLORS",
    "RISK_LABELS",
    "RiskLevel",
    "get_approval_manager",
    "get_audit_store",
    "get_autonomy_service",
    "get_kill_switch",
    "matches_rules",
]
