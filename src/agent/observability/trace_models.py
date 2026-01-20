"""
Trace Models

Data models for agent execution tracing and observability.
"""

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


# Maximum length for raw input/output to prevent excessive storage
MAX_RAW_LENGTH = 4096


class TraceEntry(BaseModel):
    """
    A single trace entry representing an event in the agent execution.

    Captures timing, token usage, cost, and raw I/O for debugging and audit.
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    session_id: str
    type: str  # Event type (e.g., 'tool_called', 'step_completed')
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    duration_ms: Optional[float] = None
    parent_trace_id: Optional[str] = None
    data: dict = Field(default_factory=dict)

    # Token and cost tracking
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    model_used: Optional[str] = None
    provider_used: Optional[str] = None
    cost_usd: Optional[float] = None

    # Raw I/O for debugging (truncated to MAX_RAW_LENGTH)
    raw_input: Optional[str] = None
    raw_output: Optional[str] = None

    @classmethod
    def from_agent_event(cls, event: Any) -> "TraceEntry":
        """
        Create a TraceEntry from an AgentEvent.

        Args:
            event: An AgentEvent instance

        Returns:
            TraceEntry with fields populated from the event
        """
        # Import here to avoid circular dependency
        from src.agent.models.event import AgentEvent

        if not isinstance(event, AgentEvent):
            raise TypeError(f"Expected AgentEvent, got {type(event)}")

        # Truncate raw I/O if present
        raw_input = None
        raw_output = None
        if hasattr(event, 'raw_input') and event.raw_input:
            raw_input = event.raw_input[:MAX_RAW_LENGTH] if len(event.raw_input) > MAX_RAW_LENGTH else event.raw_input
        if hasattr(event, 'raw_output') and event.raw_output:
            raw_output = event.raw_output[:MAX_RAW_LENGTH] if len(event.raw_output) > MAX_RAW_LENGTH else event.raw_output

        return cls(
            id=getattr(event, 'trace_id', str(uuid4())),
            session_id=event.session_id or '',
            type=event.type,
            timestamp=event.timestamp,
            duration_ms=getattr(event, 'duration_ms', None),
            parent_trace_id=getattr(event, 'parent_trace_id', None),
            data=event.data,
            input_tokens=getattr(event, 'input_tokens', None),
            output_tokens=getattr(event, 'output_tokens', None),
            model_used=getattr(event, 'model_used', None),
            provider_used=getattr(event, 'provider_used', None),
            cost_usd=getattr(event, 'estimated_cost_usd', None),
            raw_input=raw_input,
            raw_output=raw_output,
        )


class TraceSession(BaseModel):
    """
    A trace session representing a complete agent task execution.

    Groups related trace entries and tracks aggregate metrics.
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    task: str
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    status: str = "running"  # running, completed, failed, cancelled

    # Aggregate metrics
    total_events: int = 0
    total_tokens: int = 0
    total_cost_usd: float = 0.0
