"""
Agent Plan Models

Defines the structure for agent execution plans and steps.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class StepStatus(str, Enum):
    """Status of a plan step."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class PlanStep(BaseModel):
    """
    A single step in an agent execution plan.

    Steps can have dependencies on other steps (by ID) and can
    optionally invoke tools.
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    description: str
    tool_name: Optional[str] = None
    tool_params: dict = Field(default_factory=dict)
    dependencies: list[str] = Field(default_factory=list)
    status: StepStatus = StepStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None


class AgentPlan(BaseModel):
    """
    An execution plan for an agent task.

    Contains ordered steps with dependencies that the agent will
    execute to complete the user's task.
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    task: str
    overview: str
    steps: list[PlanStep] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def get_next_step(self) -> Optional[PlanStep]:
        """
        Get the next step ready for execution.

        Returns the first PENDING step whose dependencies are all COMPLETED.
        Returns None if no such step exists.
        """
        completed_ids = {
            step.id for step in self.steps if step.status == StepStatus.COMPLETED
        }

        for step in self.steps:
            if step.status != StepStatus.PENDING:
                continue
            # Check all dependencies are completed
            if all(dep_id in completed_ids for dep_id in step.dependencies):
                return step

        return None

    def is_complete(self) -> bool:
        """Check if all steps are completed or skipped."""
        terminal_statuses = {StepStatus.COMPLETED, StepStatus.SKIPPED}
        return all(step.status in terminal_statuses for step in self.steps)

    def has_failed(self) -> bool:
        """Check if any step has failed."""
        return any(step.status == StepStatus.FAILED for step in self.steps)
