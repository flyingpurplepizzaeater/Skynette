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
    # Safety system event types
    "action_classified",
    "approval_requested",
    "approval_received",
    "kill_switch_triggered",
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

    # Safety system event factory methods

    @classmethod
    def action_classified(
        cls,
        tool_name: str,
        risk_level: str,
        reason: str,
        requires_approval: bool,
        session_id: str,
    ) -> "AgentEvent":
        """Create an action_classified event."""
        return cls(
            type="action_classified",
            data={
                "tool_name": tool_name,
                "risk_level": risk_level,
                "reason": reason,
                "requires_approval": requires_approval,
            },
            session_id=session_id,
        )

    @classmethod
    def approval_requested(
        cls,
        request_id: str,
        tool_name: str,
        risk_level: str,
        reason: str,
        parameters: dict,
        session_id: str,
    ) -> "AgentEvent":
        """Create an approval_requested event."""
        return cls(
            type="approval_requested",
            data={
                "request_id": request_id,
                "tool_name": tool_name,
                "risk_level": risk_level,
                "reason": reason,
                "parameters": parameters,
            },
            session_id=session_id,
        )

    @classmethod
    def approval_received(
        cls,
        request_id: str,
        decision: str,  # "approved", "rejected", "timeout"
        approve_similar: bool,
        session_id: str,
    ) -> "AgentEvent":
        """Create an approval_received event."""
        return cls(
            type="approval_received",
            data={
                "request_id": request_id,
                "decision": decision,
                "approve_similar": approve_similar,
            },
            session_id=session_id,
        )

    @classmethod
    def kill_switch_triggered(cls, reason: str, session_id: str) -> "AgentEvent":
        """Create a kill_switch_triggered event."""
        return cls(
            type="kill_switch_triggered",
            data={"reason": reason},
            session_id=session_id,
        )
