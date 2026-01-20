"""
Agent Event Models

Defines event types for the agent execution lifecycle.
"""

from datetime import datetime, timezone
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


AgentEventType = Literal[
    "state_change",
    "plan_created",
    "step_started",
    "step_completed",
    "tool_called",
    "tool_result",
    "message",
    "error",
    "budget_warning",
    "budget_exceeded",
    "iteration_limit",
    "completed",
    "cancelled",
]


class AgentEvent(BaseModel):
    """
    An event in the agent execution lifecycle.

    Events are emitted by the agent loop and can be used for
    logging, UI updates, and debugging.
    """

    model_config = ConfigDict(use_enum_values=True)

    type: AgentEventType
    data: dict = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    session_id: Optional[str] = None

    @classmethod
    def state_change(cls, state: str, session_id: str) -> "AgentEvent":
        """Create a state change event."""
        return cls(
            type="state_change",
            data={"state": state},
            session_id=session_id,
        )

    @classmethod
    def plan_created(cls, plan_dict: dict, session_id: str) -> "AgentEvent":
        """Create a plan created event."""
        return cls(
            type="plan_created",
            data={"plan": plan_dict},
            session_id=session_id,
        )

    @classmethod
    def step_completed(cls, step_id: str, result: Any, session_id: str) -> "AgentEvent":
        """Create a step completed event."""
        return cls(
            type="step_completed",
            data={"step_id": step_id, "result": result},
            session_id=session_id,
        )

    @classmethod
    def error(cls, message: str, session_id: str) -> "AgentEvent":
        """Create an error event."""
        return cls(
            type="error",
            data={"message": message},
            session_id=session_id,
        )
