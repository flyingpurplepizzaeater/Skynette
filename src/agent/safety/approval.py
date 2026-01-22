"""
Approval Flow

Models and manager for human-in-the-loop approval of agent actions.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, UTC
from pathlib import Path
from typing import Literal, Optional
from uuid import uuid4

from src.agent.safety.classification import ActionClassification

logger = logging.getLogger(__name__)

# Approval decision type
ApprovalDecision = Literal["approved", "rejected", "timeout"]


@dataclass
class ApprovalResult:
    """Result of an approval request."""

    decision: ApprovalDecision
    approve_similar: bool = False  # If True, auto-approve similar future actions
    modified_params: Optional[dict] = None  # If user modified parameters
    decided_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    decided_by: str = "user"  # "user" or "similar_match"


@dataclass
class ApprovalRequest:
    """
    Request for user approval of an action.

    Contains the classification and provides async waiting.
    """

    id: str = field(default_factory=lambda: str(uuid4()))
    classification: ActionClassification = field(default_factory=lambda: ActionClassification(
        risk_level="moderate",
        reason="Unknown action",
        requires_approval=True,
        tool_name="unknown",
        parameters={},
    ))
    step_id: str = ""
    session_id: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    # Internal async coordination
    _approved: asyncio.Event = field(default_factory=asyncio.Event, repr=False)
    result: Optional[ApprovalResult] = field(default=None, repr=False)

    async def wait_for_decision(self, timeout: Optional[float] = None) -> ApprovalResult:
        """
        Wait for user decision.

        Args:
            timeout: Optional timeout in seconds. None means wait indefinitely.

        Returns:
            ApprovalResult with decision

        Raises:
            asyncio.TimeoutError if timeout expires
        """
        try:
            await asyncio.wait_for(self._approved.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            self.result = ApprovalResult(decision="timeout")
        return self.result

    def set_result(self, result: ApprovalResult):
        """Set the approval result and unblock waiting."""
        self.result = result
        self._approved.set()
