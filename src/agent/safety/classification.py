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
