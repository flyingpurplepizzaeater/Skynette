"""
Action Classification System

Risk-based classification for agent tool actions.
"""

from datetime import datetime, UTC
from typing import Literal, TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from src.agent.safety.autonomy import AutonomyLevelService


# Risk level type using Literal (per 07-01 decision)
RiskLevel = Literal["safe", "moderate", "destructive", "critical"]


# Risk level colors matching Theme patterns
RISK_COLORS: dict[RiskLevel, str] = {
    "safe": "#22C55E",       # Theme.SUCCESS (green)
    "moderate": "#F59E0B",   # Theme.WARNING (amber)
    "destructive": "#F97316",  # Orange
    "critical": "#EF4444",   # Theme.ERROR (red)
}

RISK_LABELS: dict[RiskLevel, str] = {
    "safe": "Safe",
    "moderate": "Moderate",
    "destructive": "Destructive",
    "critical": "Critical",
}


class ActionClassification(BaseModel):
    """Classification result for a tool action."""

    risk_level: RiskLevel
    reason: str  # Human-readable explanation
    requires_approval: bool
    tool_name: str
    parameters: dict = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ActionClassifier:
    """Classifies tool actions by risk level."""

    # Static classification for built-in tools
    TOOL_CLASSIFICATIONS: dict[str, RiskLevel] = {
        # Safe - read-only operations
        "mock_echo": "safe",
        "web_search": "safe",
        "file_read": "safe",
        "file_list": "safe",
        "rag_query": "safe",

        # Moderate - external interactions, reversible changes
        "browser": "moderate",

        # Destructive - file modifications, code execution
        "file_write": "destructive",
        "code_execute": "destructive",
        "github": "destructive",

        # Critical - file deletion (data loss)
        "file_delete": "critical",
    }

    def __init__(self, autonomy_service: "AutonomyLevelService | None" = None):
        """
        Initialize classifier.

        Args:
            autonomy_service: Optional AutonomyLevelService (uses global if not provided)
        """
        self._autonomy_service = autonomy_service

    @property
    def autonomy_service(self) -> "AutonomyLevelService":
        """Get autonomy service, using global singleton if not provided."""
        if self._autonomy_service is None:
            from src.agent.safety.autonomy import get_autonomy_service
            self._autonomy_service = get_autonomy_service()
        return self._autonomy_service

    def classify(
        self,
        tool_name: str,
        parameters: dict,
        project_path: str | None = None,
    ) -> ActionClassification:
        """
        Classify an action by tool name and parameters.

        Args:
            tool_name: Name of the tool being called
            parameters: Tool parameters
            project_path: Optional project path for autonomy level lookup

        Returns:
            ActionClassification with risk level and approval requirement
        """
        # Import here to avoid circular dependency
        from src.agent.safety.autonomy import AUTONOMY_THRESHOLDS

        # Built-in tool classification
        if tool_name in self.TOOL_CLASSIFICATIONS:
            risk = self.TOOL_CLASSIFICATIONS[tool_name]
        else:
            # Unknown/MCP tools default to moderate
            risk = "moderate"

        # Get autonomy settings
        settings = self.autonomy_service.get_settings(project_path)

        # Check allowlist/blocklist rules first (override autonomy level)
        rule_result = settings.check_rules(tool_name, parameters)
        if rule_result is not None:
            # Rule explicitly allows or blocks
            requires_approval = not rule_result  # allow=True means no approval needed
            return ActionClassification(
                risk_level=risk,
                reason=self._get_reason(tool_name, risk, parameters),
                requires_approval=requires_approval,
                tool_name=tool_name,
                parameters=parameters,
            )

        # Apply autonomy threshold
        auto_execute_levels = AUTONOMY_THRESHOLDS[settings.level]
        requires_approval = risk not in auto_execute_levels

        return ActionClassification(
            risk_level=risk,
            reason=self._get_reason(tool_name, risk, parameters),
            requires_approval=requires_approval,
            tool_name=tool_name,
            parameters=parameters,
        )

    def _get_reason(self, tool_name: str, risk: RiskLevel, params: dict) -> str:
        """Generate human-readable reason for classification."""
        # Tool-specific reasons with parameter context
        reasons = {
            "file_write": f"Destructive: modifies file {params.get('path', 'unknown')}",
            "file_delete": f"Critical: deletes file {params.get('path', 'unknown')}",
            "code_execute": f"Destructive: executes {params.get('language', 'code')} code",
            "github": f"Destructive: GitHub operation ({params.get('operation', 'unknown')})",
            "browser": f"Moderate: web interaction at {params.get('url', 'unknown URL')}",
        }
        if tool_name in reasons:
            return reasons[tool_name]

        # Generic reasons by risk level
        generic = {
            "safe": f"Safe: read-only operation ({tool_name})",
            "moderate": f"Moderate: external interaction ({tool_name})",
            "destructive": f"Destructive: modifies data ({tool_name})",
            "critical": f"Critical: potential data loss ({tool_name})",
        }
        return generic[risk]
