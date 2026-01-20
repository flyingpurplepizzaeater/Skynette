"""
Agent State Models

Defines the state tracking for agent sessions including state machine
and session data.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class AgentState(str, Enum):
    """Agent execution states."""

    IDLE = "idle"
    PLANNING = "planning"
    EXECUTING = "executing"
    AWAITING_TOOL = "awaiting_tool"
    AWAITING_APPROVAL = "awaiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentSession(BaseModel):
    """
    Tracks the state of an agent execution session.

    Maintains conversation history, token budget, and execution state
    for a single agent task.
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    task: str
    state: AgentState = AgentState.IDLE
    messages: list[dict] = Field(default_factory=list)
    variables: dict[str, Any] = Field(default_factory=dict)
    token_budget: int = 50000
    tokens_used: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    steps_completed: int = 0

    def can_continue(self) -> bool:
        """Check if the session can continue execution."""
        allowed_states = {
            AgentState.IDLE,
            AgentState.PLANNING,
            AgentState.EXECUTING,
            AgentState.AWAITING_TOOL,
            AgentState.AWAITING_APPROVAL,
        }
        return self.state in allowed_states and self.tokens_used < self.token_budget

    def remaining_tokens(self) -> int:
        """Get the number of tokens remaining in budget."""
        return self.token_budget - self.tokens_used

    def usage_percentage(self) -> float:
        """Get token usage as a percentage (0.0 to 1.0)."""
        if self.token_budget == 0:
            return 1.0
        return self.tokens_used / self.token_budget

    def is_budget_warning(self) -> bool:
        """Check if token usage is at warning level (80% or above)."""
        return self.usage_percentage() >= 0.8
