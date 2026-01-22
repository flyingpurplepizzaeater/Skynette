"""
Action Classification System

Risk-based classification for agent tool actions.
"""

from datetime import datetime, UTC
from typing import Literal

from pydantic import BaseModel, Field


# Risk level type using Literal (per 07-01 decision)
RiskLevel = Literal["safe", "moderate", "destructive", "critical"]


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

    # Approval requirements by risk level
    APPROVAL_REQUIRED: dict[RiskLevel, bool] = {
        "safe": False,
        "moderate": False,  # May require approval based on autonomy level (Phase 13)
        "destructive": True,
        "critical": True,
    }

    def classify(self, tool_name: str, parameters: dict) -> ActionClassification:
        """Classify an action by tool name and parameters."""
        # Built-in tool classification
        if tool_name in self.TOOL_CLASSIFICATIONS:
            risk = self.TOOL_CLASSIFICATIONS[tool_name]
        else:
            # Unknown/MCP tools default to moderate
            risk = "moderate"

        return ActionClassification(
            risk_level=risk,
            reason=self._get_reason(tool_name, risk, parameters),
            requires_approval=self.APPROVAL_REQUIRED[risk],
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
