"""
Cancellation Models

Data models for user-controlled cancellation behavior.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class CancelMode(str, Enum):
    """Cancellation mode options."""

    IMMEDIATE = "immediate"  # Stop now, mid-step
    AFTER_CURRENT = "after_current"  # Finish current step, then stop


class ResultMode(str, Enum):
    """What to do with completed work on cancellation."""

    KEEP = "keep"  # Keep all completed work
    ROLLBACK = "rollback"  # Attempt to undo (tracks intent; actual rollback is future work)


class CancellationRequest(BaseModel):
    """
    User's request to cancel execution.

    Captures the cancel mode, result mode, and optional reason.
    """

    cancel_mode: CancelMode
    result_mode: ResultMode
    reason: Optional[str] = None
    requested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CancellationResult(BaseModel):
    """
    Result of a cancellation operation.

    Summarizes what completed before cancellation and available options.
    """

    completed_steps: list[str] = Field(default_factory=list)  # Step descriptions
    cancelled_step: Optional[str] = None  # If cancelled mid-step
    cancel_mode: CancelMode
    result_mode: ResultMode
    options: list[str] = Field(default_factory=lambda: ["resume", "restart", "abandon"])
