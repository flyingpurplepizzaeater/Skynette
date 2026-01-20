"""
Trace Store

SQLite-backed storage for agent execution traces.
Follows patterns from src/data/storage.py.
"""

import json
import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from uuid import uuid4

from src.agent.observability.trace_models import MAX_RAW_LENGTH, TraceEntry, TraceSession

logger = logging.getLogger(__name__)


class TraceStore:
    """
    SQLite-backed trace storage for agent execution.

    Provides persistence, querying, and cleanup of trace data.
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize trace store.

        Args:
            db_path: Path to SQLite database. Defaults to ~/.skynette/agent_traces.db
        """
        if db_path:
            self.db_path = Path(db_path)
        else:
            self.db_path = Path.home() / ".skynette" / "agent_traces.db"

        # Ensure directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self._init_db()

    def _init_db(self):
        """Initialize SQLite database with required tables and indexes."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Enable WAL mode for better concurrent access
        cursor.execute("PRAGMA journal_mode=WAL")

        # Sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_trace_sessions (
                id TEXT PRIMARY KEY,
                task TEXT NOT NULL,
                started_at TEXT NOT NULL,
                completed_at TEXT,
                status TEXT NOT NULL DEFAULT 'running'
            )
        """)

        # Traces table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_traces (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                type TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                duration_ms REAL,
                parent_trace_id TEXT,
                data TEXT NOT NULL,
                input_tokens INTEGER,
                output_tokens INTEGER,
                model_used TEXT,
                provider_used TEXT,
                cost_usd REAL,
                raw_input TEXT,
                raw_output TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES agent_trace_sessions(id) ON DELETE CASCADE
            )
        """)

        # Settings table for retention configuration
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trace_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)

        # Create indexes for efficient querying
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_traces_session
            ON agent_traces(session_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_traces_timestamp
            ON agent_traces(timestamp)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_traces_type
            ON agent_traces(type)
        """)

        # Set default retention if not exists
        cursor.execute("""
            INSERT OR IGNORE INTO trace_settings (key, value)
            VALUES ('retention_days', '30')
        """)

        conn.commit()
        conn.close()
        logger.debug(f"Trace database initialized at {self.db_path}")

    # ==================== Session Management ====================

    def start_session(self, task: str) -> TraceSession:
        """
        Start a new trace session.

        Args:
            task: Description of the task being executed

        Returns:
            TraceSession model with generated ID
        """
        session = TraceSession(
            id=str(uuid4()),
            task=task,
            started_at=datetime.now(timezone.utc),
            status="running",
        )

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO agent_trace_sessions (id, task, started_at, status)
            VALUES (?, ?, ?, ?)
        """, (
            session.id,
            session.task,
            session.started_at.isoformat(),
            session.status,
        ))

        conn.commit()
        conn.close()

        logger.debug(f"Started trace session {session.id} for task: {task}")
        return session

    def end_session(self, session_id: str, status: str):
        """
        End a trace session.

        Args:
            session_id: Session ID to end
            status: Final status (completed, failed, cancelled)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE agent_trace_sessions
            SET completed_at = ?, status = ?
            WHERE id = ?
        """, (
            datetime.now(timezone.utc).isoformat(),
            status,
            session_id,
        ))

        conn.commit()
        conn.close()

        logger.debug(f"Ended trace session {session_id} with status: {status}")

    def get_session(self, session_id: str) -> Optional[TraceSession]:
        """
        Get a session by ID.

        Args:
            session_id: Session ID to retrieve

        Returns:
            TraceSession or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT s.*,
                   COUNT(t.id) as total_events,
                   COALESCE(SUM(t.input_tokens), 0) + COALESCE(SUM(t.output_tokens), 0) as total_tokens,
                   COALESCE(SUM(t.cost_usd), 0) as total_cost
            FROM agent_trace_sessions s
            LEFT JOIN agent_traces t ON s.id = t.session_id
            WHERE s.id = ?
            GROUP BY s.id
        """, (session_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return TraceSession(
            id=row["id"],
            task=row["task"],
            started_at=datetime.fromisoformat(row["started_at"]),
            completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None,
            status=row["status"],
            total_events=row["total_events"],
            total_tokens=row["total_tokens"],
            total_cost_usd=row["total_cost"],
        )

    def get_sessions(self, limit: int = 50, offset: int = 0) -> list[TraceSession]:
        """
        List recent sessions.

        Args:
            limit: Maximum number of sessions to return
            offset: Offset for pagination

        Returns:
            List of TraceSession models
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT s.*,
                   COUNT(t.id) as total_events,
                   COALESCE(SUM(t.input_tokens), 0) + COALESCE(SUM(t.output_tokens), 0) as total_tokens,
                   COALESCE(SUM(t.cost_usd), 0) as total_cost
            FROM agent_trace_sessions s
            LEFT JOIN agent_traces t ON s.id = t.session_id
            GROUP BY s.id
            ORDER BY s.started_at DESC
            LIMIT ? OFFSET ?
        """, (limit, offset))

        sessions = []
        for row in cursor.fetchall():
            sessions.append(TraceSession(
                id=row["id"],
                task=row["task"],
                started_at=datetime.fromisoformat(row["started_at"]),
                completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None,
                status=row["status"],
                total_events=row["total_events"],
                total_tokens=row["total_tokens"],
                total_cost_usd=row["total_cost"],
            ))

        conn.close()
        return sessions

    # ==================== Trace Management ====================

    def save_trace(self, entry: TraceEntry):
        """
        Save a trace entry.

        Args:
            entry: TraceEntry to persist
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Truncate raw I/O if needed
        raw_input = entry.raw_input
        raw_output = entry.raw_output
        if raw_input and len(raw_input) > MAX_RAW_LENGTH:
            raw_input = raw_input[:MAX_RAW_LENGTH]
        if raw_output and len(raw_output) > MAX_RAW_LENGTH:
            raw_output = raw_output[:MAX_RAW_LENGTH]

        cursor.execute("""
            INSERT INTO agent_traces (
                id, session_id, type, timestamp, duration_ms, parent_trace_id,
                data, input_tokens, output_tokens, model_used, provider_used,
                cost_usd, raw_input, raw_output, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            entry.id,
            entry.session_id,
            entry.type,
            entry.timestamp.isoformat(),
            entry.duration_ms,
            entry.parent_trace_id,
            json.dumps(entry.data),
            entry.input_tokens,
            entry.output_tokens,
            entry.model_used,
            entry.provider_used,
            entry.cost_usd,
            raw_input,
            raw_output,
            datetime.now(timezone.utc).isoformat(),
        ))

        conn.commit()
        conn.close()

        logger.debug(f"Saved trace {entry.id} of type {entry.type}")

    def get_traces(
        self,
        session_id: Optional[str] = None,
        event_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        search_text: Optional[str] = None,
        limit: int = 100,
    ) -> list[TraceEntry]:
        """
        Query traces with filters.

        Args:
            session_id: Filter by session
            event_type: Filter by event type
            start_time: Filter by minimum timestamp
            end_time: Filter by maximum timestamp
            search_text: Search in data JSON and raw I/O
            limit: Maximum results

        Returns:
            List of matching TraceEntry models
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = "SELECT * FROM agent_traces WHERE 1=1"
        params: list = []

        if session_id:
            query += " AND session_id = ?"
            params.append(session_id)

        if event_type:
            query += " AND type = ?"
            params.append(event_type)

        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time.isoformat())

        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time.isoformat())

        if search_text:
            query += " AND (data LIKE ? OR raw_input LIKE ? OR raw_output LIKE ?)"
            search_pattern = f"%{search_text}%"
            params.extend([search_pattern, search_pattern, search_pattern])

        query += " ORDER BY timestamp ASC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)

        traces = []
        for row in cursor.fetchall():
            traces.append(TraceEntry(
                id=row["id"],
                session_id=row["session_id"],
                type=row["type"],
                timestamp=datetime.fromisoformat(row["timestamp"]),
                duration_ms=row["duration_ms"],
                parent_trace_id=row["parent_trace_id"],
                data=json.loads(row["data"]),
                input_tokens=row["input_tokens"],
                output_tokens=row["output_tokens"],
                model_used=row["model_used"],
                provider_used=row["provider_used"],
                cost_usd=row["cost_usd"],
                raw_input=row["raw_input"],
                raw_output=row["raw_output"],
            ))

        conn.close()
        return traces

    # ==================== Retention Management ====================

    def get_retention_days(self) -> int:
        """
        Get current retention setting.

        Returns:
            Number of days to retain traces (default 30)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT value FROM trace_settings WHERE key = 'retention_days'")
        row = cursor.fetchone()
        conn.close()

        return int(row[0]) if row else 30

    def set_retention_days(self, days: int):
        """
        Update retention setting.

        Args:
            days: Number of days to retain traces
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO trace_settings (key, value)
            VALUES ('retention_days', ?)
        """, (str(days),))

        conn.commit()
        conn.close()

        logger.info(f"Set trace retention to {days} days")

    def cleanup_old_traces(self, retention_days: Optional[int] = None) -> int:
        """
        Delete traces older than retention period.

        Args:
            retention_days: Override retention setting, or use configured value

        Returns:
            Number of traces deleted
        """
        if retention_days is None:
            retention_days = self.get_retention_days()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Calculate cutoff date
        from datetime import timedelta
        cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
        cutoff_str = cutoff.isoformat()

        # Delete old traces
        cursor.execute("""
            DELETE FROM agent_traces WHERE timestamp < ?
        """, (cutoff_str,))
        deleted_traces = cursor.rowcount

        # Delete orphaned sessions (no remaining traces)
        cursor.execute("""
            DELETE FROM agent_trace_sessions
            WHERE id NOT IN (SELECT DISTINCT session_id FROM agent_traces)
            AND completed_at IS NOT NULL
        """)

        conn.commit()
        conn.close()

        logger.info(f"Cleaned up {deleted_traces} traces older than {retention_days} days")
        return deleted_traces
