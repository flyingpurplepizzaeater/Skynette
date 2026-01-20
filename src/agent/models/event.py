"""
Agent Event Models

Defines event types for the agent execution lifecycle.
"""

from datetime import datetime, timezone
from typing import Any, Literal, Optional
from uuid import uuid4

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
    # New event types for observability
    "model_selected",
    "model_switched",
    "trace_started",
    "trace_ended",
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

    # Trace context fields
    trace_id: str = Field(default_factory=lambda: str(uuid4()))
    parent_trace_id: Optional[str] = None
    duration_ms: Optional[float] = None

    # Token and cost tracking
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    model_used: Optional[str] = None
    provider_used: Optional[str] = None
    estimated_cost_usd: Optional[float] = None

    # Raw I/O for debugging
    raw_input: Optional[str] = None
    raw_output: Optional[str] = None

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

    @classmethod
    def model_selected(
        cls,
        model: str,
        provider: str,
        reason: str,
        session_id: str,
    ) -> "AgentEvent":
        """Create a model selected event for routing decisions."""
        return cls(
            type="model_selected",
            data={
                "model": model,
                "provider": provider,
                "reason": reason,
            },
            session_id=session_id,
            model_used=model,
            provider_used=provider,
        )

    @classmethod
    def model_switched(
        cls,
        from_model: str,
        to_model: str,
        session_id: str,
        reason: Optional[str] = None,
    ) -> "AgentEvent":
        """Create a model switched event for mid-task model changes."""
        return cls(
            type="model_switched",
            data={
                "from_model": from_model,
                "to_model": to_model,
                "reason": reason,
            },
            session_id=session_id,
            model_used=to_model,
        )
