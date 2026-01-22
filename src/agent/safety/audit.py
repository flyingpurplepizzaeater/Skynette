"""
Audit Trail

Comprehensive logging of agent actions with risk and approval metadata.
Extends the TraceStore patterns for safety-specific auditing.
"""

import json
import logging
import sqlite3
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from src.agent.safety.classification import RiskLevel

logger = logging.getLogger(__name__)

# Max length for parameter/result truncation (matches TraceStore)
MAX_AUDIT_DATA_LENGTH = 4096

# Approval decision type for audit
AuditApprovalDecision = Literal["approved", "rejected", "auto", "not_required"]


class AuditEntry(BaseModel):
    """
    Audit log entry for an agent action.

    Captures comprehensive context for security review and debugging.
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    session_id: str
    step_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Action details
    tool_name: str
    parameters: dict = Field(default_factory=dict)
    result: Optional[dict] = None
    error: Optional[str] = None
    duration_ms: float = 0

    # Safety metadata
    risk_level: RiskLevel
    approval_required: bool = False
    approval_decision: AuditApprovalDecision = "not_required"
    approved_by: Optional[str] = None  # "user", "similar_match", or None
    approval_time_ms: Optional[float] = None  # Time user spent deciding

    # Execution context
    success: bool = True
    parent_plan_id: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "step_id": self.step_id,
            "timestamp": self.timestamp.isoformat(),
            "tool_name": self.tool_name,
            "parameters": json.dumps(self.parameters)[:MAX_AUDIT_DATA_LENGTH],
            "result": json.dumps(self.result)[:MAX_AUDIT_DATA_LENGTH] if self.result else None,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "risk_level": self.risk_level,
            "approval_required": self.approval_required,
            "approval_decision": self.approval_decision,
            "approved_by": self.approved_by,
            "approval_time_ms": self.approval_time_ms,
            "success": self.success,
            "parent_plan_id": self.parent_plan_id,
        }

    @classmethod
    def from_row(cls, row: dict) -> "AuditEntry":
        """Create from database row."""
        return cls(
            id=row["id"],
            session_id=row["session_id"],
            step_id=row["step_id"],
            timestamp=datetime.fromisoformat(row["timestamp"]),
            tool_name=row["tool_name"],
            parameters=json.loads(row["parameters"]) if row["parameters"] else {},
            result=json.loads(row["result"]) if row["result"] else None,
            error=row["error"],
            duration_ms=row["duration_ms"] or 0,
            risk_level=row["risk_level"],
            approval_required=bool(row["approval_required"]),
            approval_decision=row["approval_decision"],
            approved_by=row["approved_by"],
            approval_time_ms=row["approval_time_ms"],
            success=bool(row["success"]),
            parent_plan_id=row["parent_plan_id"],
        )
