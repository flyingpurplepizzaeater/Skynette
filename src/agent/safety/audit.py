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


class AuditStore:
    """
    SQLite-backed audit trail storage.

    Provides persistence, querying, and cleanup of audit data.
    Follows patterns from TraceStore for consistency.
    """

    DEFAULT_RETENTION_DAYS = 30

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize audit store.

        Args:
            db_path: Path to SQLite database. Defaults to ~/.skynette/agent_audit.db
        """
        if db_path:
            self.db_path = Path(db_path)
        else:
            self.db_path = Path.home() / ".skynette" / "agent_audit.db"

        # Ensure directory exists (handle special paths gracefully)
        if str(self.db_path) not in (":memory:", ""):
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._init_db()

    def _init_db(self):
        """Initialize SQLite database with audit table."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Enable WAL mode for better concurrent access
        cursor.execute("PRAGMA journal_mode=WAL")

        # Audit entries table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_audit (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                step_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                tool_name TEXT NOT NULL,
                parameters TEXT,
                result TEXT,
                error TEXT,
                duration_ms REAL,
                risk_level TEXT NOT NULL,
                approval_required INTEGER NOT NULL DEFAULT 0,
                approval_decision TEXT NOT NULL DEFAULT 'not_required',
                approved_by TEXT,
                approval_time_ms REAL,
                success INTEGER NOT NULL DEFAULT 1,
                parent_plan_id TEXT,
                created_at TEXT NOT NULL
            )
        """)

        # Indexes for efficient querying
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_audit_session
            ON agent_audit(session_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_audit_timestamp
            ON agent_audit(timestamp)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_audit_risk_level
            ON agent_audit(risk_level)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_audit_tool
            ON agent_audit(tool_name)
        """)

        conn.commit()
        conn.close()
        logger.debug(f"Audit database initialized at {self.db_path}")

    def log(self, entry: AuditEntry):
        """
        Log an audit entry.

        Args:
            entry: AuditEntry to persist
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        data = entry.to_dict()
        cursor.execute("""
            INSERT INTO agent_audit (
                id, session_id, step_id, timestamp, tool_name,
                parameters, result, error, duration_ms,
                risk_level, approval_required, approval_decision,
                approved_by, approval_time_ms, success, parent_plan_id, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data["id"],
            data["session_id"],
            data["step_id"],
            data["timestamp"],
            data["tool_name"],
            data["parameters"],
            data["result"],
            data["error"],
            data["duration_ms"],
            data["risk_level"],
            1 if data["approval_required"] else 0,
            data["approval_decision"],
            data["approved_by"],
            data["approval_time_ms"],
            1 if data["success"] else 0,
            data["parent_plan_id"],
            datetime.now(timezone.utc).isoformat(),
        ))

        conn.commit()
        conn.close()
        logger.debug(f"Audit logged: {entry.tool_name} ({entry.risk_level})")

    def query(
        self,
        session_id: Optional[str] = None,
        risk_level: Optional[RiskLevel] = None,
        tool_name: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        success_only: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditEntry]:
        """
        Query audit entries with filters.

        Args:
            session_id: Filter by session
            risk_level: Filter by risk level
            tool_name: Filter by tool
            start_time: Filter by minimum timestamp
            end_time: Filter by maximum timestamp
            success_only: Only return successful actions
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of matching AuditEntry models
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = "SELECT * FROM agent_audit WHERE 1=1"
        params: list = []

        if session_id:
            query += " AND session_id = ?"
            params.append(session_id)

        if risk_level:
            query += " AND risk_level = ?"
            params.append(risk_level)

        if tool_name:
            query += " AND tool_name = ?"
            params.append(tool_name)

        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time.isoformat())

        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time.isoformat())

        if success_only:
            query += " AND success = 1"

        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor.execute(query, params)

        entries = [AuditEntry.from_row(dict(row)) for row in cursor.fetchall()]
        conn.close()
        return entries

    def get_session_summary(self, session_id: str) -> dict:
        """
        Get summary statistics for a session.

        Returns:
            Dict with counts by risk level, approval decisions, etc.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN risk_level = 'safe' THEN 1 ELSE 0 END) as safe_count,
                SUM(CASE WHEN risk_level = 'moderate' THEN 1 ELSE 0 END) as moderate_count,
                SUM(CASE WHEN risk_level = 'destructive' THEN 1 ELSE 0 END) as destructive_count,
                SUM(CASE WHEN risk_level = 'critical' THEN 1 ELSE 0 END) as critical_count,
                SUM(CASE WHEN approval_decision = 'approved' THEN 1 ELSE 0 END) as approved_count,
                SUM(CASE WHEN approval_decision = 'rejected' THEN 1 ELSE 0 END) as rejected_count,
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as success_count,
                SUM(duration_ms) as total_duration_ms
            FROM agent_audit WHERE session_id = ?
        """, (session_id,))

        row = cursor.fetchone()
        conn.close()

        return {
            "total_actions": row[0] or 0,
            "by_risk": {
                "safe": row[1] or 0,
                "moderate": row[2] or 0,
                "destructive": row[3] or 0,
                "critical": row[4] or 0,
            },
            "approved": row[5] or 0,
            "rejected": row[6] or 0,
            "successful": row[7] or 0,
            "total_duration_ms": row[8] or 0,
        }

    def cleanup_old_entries(self, retention_days: int = DEFAULT_RETENTION_DAYS) -> int:
        """
        Delete audit entries older than retention period.

        Args:
            retention_days: Days to retain (default 30)

        Returns:
            Number of entries deleted
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
        cursor.execute(
            "DELETE FROM agent_audit WHERE timestamp < ?",
            (cutoff.isoformat(),)
        )
        deleted = cursor.rowcount

        conn.commit()
        conn.close()

        logger.info(f"Cleaned up {deleted} audit entries older than {retention_days} days")
        return deleted

    def export_json(self, session_id: str) -> str:
        """Export session audit as JSON string."""
        entries = self.query(session_id=session_id, limit=10000)
        return json.dumps([e.to_dict() for e in entries], indent=2)

    def export_csv(self, session_id: str) -> str:
        """Export session audit as CSV string."""
        entries = self.query(session_id=session_id, limit=10000)
        if not entries:
            return ""

        headers = ["timestamp", "tool_name", "risk_level", "approval_decision", "success", "duration_ms", "error"]
        lines = [",".join(headers)]

        for e in entries:
            row = [
                e.timestamp.isoformat(),
                e.tool_name,
                e.risk_level,
                e.approval_decision,
                str(e.success),
                str(e.duration_ms),
                (e.error or "").replace(",", ";"),
            ]
            lines.append(",".join(row))

        return "\n".join(lines)


_global_audit_store: Optional[AuditStore] = None


def get_audit_store() -> AuditStore:
    """Get the global audit store instance."""
    global _global_audit_store
    if _global_audit_store is None:
        _global_audit_store = AuditStore()
    return _global_audit_store
