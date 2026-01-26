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


class ApprovalManager:
    """
    Manages pending approval requests and similarity matching.

    Handles:
    - Tracking pending approval requests
    - Similarity matching for "Approve All Similar"
    - Session-scoped approval caching
    """

    def __init__(self):
        """Initialize the approval manager."""
        self._pending: dict[str, ApprovalRequest] = {}
        # Cache of approved similar actions: (tool_name, pattern) -> True
        self._similarity_cache: dict[tuple[str, str], bool] = {}
        self._session_id: Optional[str] = None

    def start_session(self, session_id: str):
        """Start a new session, clearing any cached approvals."""
        self._session_id = session_id
        self._similarity_cache.clear()
        self._pending.clear()
        logger.debug(f"Approval manager started for session {session_id}")

    def end_session(self):
        """End the session and clear caches."""
        self._session_id = None
        self._similarity_cache.clear()
        self._pending.clear()

    async def request_approval(
        self,
        classification: ActionClassification,
        step_id: str,
        timeout: Optional[float] = 60.0,
    ) -> ApprovalResult:
        """
        Request approval for an action.

        First checks similarity cache for auto-approval.
        If not cached, creates request and waits for user.

        Args:
            classification: The action classification
            step_id: ID of the plan step requesting approval
            timeout: Seconds to wait before timeout (default 60s per CONTEXT.md)

        Returns:
            ApprovalResult with decision
        """
        # Check similarity cache first
        pattern = self._get_similarity_pattern(classification)
        cache_key = (classification.tool_name, pattern)

        if cache_key in self._similarity_cache:
            logger.debug(f"Auto-approved via similarity cache: {cache_key}")
            return ApprovalResult(
                decision="approved",
                approve_similar=False,
                decided_by="similar_match",
            )

        # Create and track request
        request = ApprovalRequest(
            classification=classification,
            step_id=step_id,
            session_id=self._session_id or "",
        )
        self._pending[request.id] = request

        logger.info(f"Approval requested for {classification.tool_name}: {classification.reason}")

        # Wait for decision
        result = await request.wait_for_decision(timeout=timeout)

        # Remove from pending
        self._pending.pop(request.id, None)

        # Update similarity cache if approved with "approve similar"
        if result.decision == "approved" and result.approve_similar:
            self._similarity_cache[cache_key] = True
            logger.debug(f"Added to similarity cache: {cache_key}")

        return result

    def approve(self, request_id: str, approve_similar: bool = False):
        """
        Approve a pending request.

        Args:
            request_id: ID of the request to approve
            approve_similar: If True, auto-approve similar future actions
        """
        request = self._pending.get(request_id)
        if request:
            request.set_result(ApprovalResult(
                decision="approved",
                approve_similar=approve_similar,
            ))
            logger.info(f"Approved request {request_id} (similar={approve_similar})")

    def reject(self, request_id: str):
        """
        Reject a pending request.

        Args:
            request_id: ID of the request to reject
        """
        request = self._pending.get(request_id)
        if request:
            request.set_result(ApprovalResult(decision="rejected"))
            logger.info(f"Rejected request {request_id}")

    def resolve(self, request_id: str, decision: str, approve_similar: bool = False) -> None:
        """
        Resolve an approval request with a decision.

        This is the primary method called by UI callbacks to complete the approval flow.
        Routes to approve() or reject() based on decision string.

        Args:
            request_id: ID of the request to resolve
            decision: One of "approved", "rejected", or "timeout"
            approve_similar: If True and approved, auto-approve similar future actions
        """
        if decision == "approved":
            self.approve(request_id, approve_similar)
        elif decision == "rejected":
            self.reject(request_id)
        elif decision == "timeout":
            # Timeout is treated as rejection - user didn't approve
            self.reject(request_id)
        else:
            logger.warning(f"Unknown approval decision '{decision}' for request {request_id}")

    def get_pending(self) -> list[ApprovalRequest]:
        """Get list of pending approval requests."""
        return list(self._pending.values())

    def _get_similarity_pattern(self, classification: ActionClassification) -> str:
        """
        Generate a pattern for similarity matching.

        For file operations: parent directory path
        For other tools: empty string (exact tool match only)
        """
        params = classification.parameters
        tool = classification.tool_name

        if tool in ("file_write", "file_read", "file_delete", "file_list"):
            path = params.get("path", "")
            if path:
                return str(Path(path).parent)

        # Default: no parameter pattern (matches all uses of same tool)
        return ""

    @staticmethod
    def are_similar(a1: ActionClassification, a2: ActionClassification) -> bool:
        """
        Check if two actions are similar enough for batch approval.

        Args:
            a1: First action
            a2: Second action

        Returns:
            True if similar, False otherwise
        """
        # Must be same tool
        if a1.tool_name != a2.tool_name:
            return False

        # For file operations: check if paths share parent or one is child of other
        if a1.tool_name in ("file_write", "file_read", "file_delete", "file_list"):
            path1 = Path(a1.parameters.get("path", ""))
            path2 = Path(a2.parameters.get("path", ""))

            # Same parent directory
            if path1.parent == path2.parent:
                return True

            # One is child of the other's parent
            try:
                if path2.is_relative_to(path1.parent) or path1.is_relative_to(path2.parent):
                    return True
            except (ValueError, TypeError):
                pass

            return False

        # For other tools: same tool name is enough
        return True


# Module-level singleton
_global_approval_manager: Optional[ApprovalManager] = None


def get_approval_manager() -> ApprovalManager:
    """
    Get the global approval manager instance.

    Returns:
        Global ApprovalManager singleton
    """
    global _global_approval_manager
    if _global_approval_manager is None:
        _global_approval_manager = ApprovalManager()
    return _global_approval_manager
