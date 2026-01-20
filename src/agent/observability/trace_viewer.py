"""
Trace Viewer

Utilities for viewing and debugging agent execution traces.
"""

from datetime import datetime
from typing import Optional

from src.agent.observability.trace_models import TraceEntry, TraceSession
from src.agent.observability.trace_store import TraceStore


class TraceViewer:
    """
    Trace viewing utilities for debugging agent execution.

    Provides methods for listing sessions, viewing timelines,
    searching traces, and formatting output for display.
    """

    def __init__(self, store: Optional[TraceStore] = None):
        """
        Initialize trace viewer.

        Args:
            store: TraceStore instance. Uses default store if not provided.
        """
        self._store = store or TraceStore()

    # ==================== Session Views ====================

    def list_sessions(self, limit: int = 20) -> list[dict]:
        """
        List recent sessions with summary information.

        Args:
            limit: Maximum number of sessions to return

        Returns:
            List of session summaries with id, task, status, event count, duration
        """
        sessions = self._store.get_sessions(limit=limit)

        result = []
        for session in sessions:
            duration_ms = None
            if session.completed_at and session.started_at:
                duration_ms = (session.completed_at - session.started_at).total_seconds() * 1000

            result.append({
                "id": session.id,
                "task": session.task,
                "status": session.status,
                "event_count": session.total_events,
                "total_tokens": session.total_tokens,
                "total_cost_usd": session.total_cost_usd,
                "started_at": session.started_at.isoformat(),
                "completed_at": session.completed_at.isoformat() if session.completed_at else None,
                "duration_ms": duration_ms,
            })

        return result

    def get_session_timeline(self, session_id: str) -> list[dict]:
        """
        Get chronological event list for a session.

        Args:
            session_id: Session ID to get timeline for

        Returns:
            List of events with timestamps, types, durations
        """
        traces = self._store.get_traces(session_id=session_id, limit=1000)

        result = []
        for trace in traces:
            result.append({
                "id": trace.id,
                "type": trace.type,
                "timestamp": trace.timestamp.isoformat(),
                "duration_ms": trace.duration_ms,
                "parent_trace_id": trace.parent_trace_id,
                "data": trace.data,
                "input_tokens": trace.input_tokens,
                "output_tokens": trace.output_tokens,
                "model_used": trace.model_used,
            })

        return result

    def get_session_summary(self, session_id: str) -> dict:
        """
        Get high-level stats for a session.

        Args:
            session_id: Session ID to summarize

        Returns:
            Summary with total time, tokens, cost, step count, errors
        """
        session = self._store.get_session(session_id)
        if not session:
            return {"error": "Session not found"}

        traces = self._store.get_traces(session_id=session_id, limit=1000)

        # Calculate stats
        total_duration_ms = None
        if session.completed_at and session.started_at:
            total_duration_ms = (session.completed_at - session.started_at).total_seconds() * 1000

        # Count events by type
        event_counts: dict[str, int] = {}
        error_count = 0
        step_count = 0
        total_input_tokens = 0
        total_output_tokens = 0
        total_cost = 0.0
        models_used: set[str] = set()

        for trace in traces:
            event_counts[trace.type] = event_counts.get(trace.type, 0) + 1

            if trace.type == "error":
                error_count += 1
            if trace.type in ("step_started", "step_completed"):
                if trace.type == "step_started":
                    step_count += 1

            if trace.input_tokens:
                total_input_tokens += trace.input_tokens
            if trace.output_tokens:
                total_output_tokens += trace.output_tokens
            if trace.cost_usd:
                total_cost += trace.cost_usd
            if trace.model_used:
                models_used.add(trace.model_used)

        return {
            "session_id": session_id,
            "task": session.task,
            "status": session.status,
            "started_at": session.started_at.isoformat(),
            "completed_at": session.completed_at.isoformat() if session.completed_at else None,
            "total_duration_ms": total_duration_ms,
            "total_events": len(traces),
            "step_count": step_count,
            "error_count": error_count,
            "total_input_tokens": total_input_tokens,
            "total_output_tokens": total_output_tokens,
            "total_tokens": total_input_tokens + total_output_tokens,
            "total_cost_usd": total_cost,
            "models_used": list(models_used),
            "event_counts": event_counts,
        }

    # ==================== Search and Detail ====================

    def search_traces(self, query: str, session_id: Optional[str] = None) -> list[dict]:
        """
        Full-text search across trace data.

        Args:
            query: Search string
            session_id: Optional session filter

        Returns:
            List of matching traces with context
        """
        traces = self._store.get_traces(
            session_id=session_id,
            search_text=query,
            limit=100,
        )

        result = []
        for trace in traces:
            result.append({
                "id": trace.id,
                "session_id": trace.session_id,
                "type": trace.type,
                "timestamp": trace.timestamp.isoformat(),
                "data": trace.data,
                "model_used": trace.model_used,
                "has_raw_input": bool(trace.raw_input),
                "has_raw_output": bool(trace.raw_output),
            })

        return result

    def get_trace_detail(self, trace_id: str) -> dict:
        """
        Get full trace entry with all fields including raw I/O.

        Args:
            trace_id: Trace ID to retrieve

        Returns:
            Full trace entry as dictionary
        """
        # Query by searching for the ID in the data
        # Since we don't have a direct ID query, we'll use a workaround
        # by getting traces and filtering
        conn = self._store.db_path
        import sqlite3
        import json

        db = sqlite3.connect(conn)
        db.row_factory = sqlite3.Row
        cursor = db.cursor()

        cursor.execute("SELECT * FROM agent_traces WHERE id = ?", (trace_id,))
        row = cursor.fetchone()
        db.close()

        if not row:
            return {"error": "Trace not found"}

        return {
            "id": row["id"],
            "session_id": row["session_id"],
            "type": row["type"],
            "timestamp": row["timestamp"],
            "duration_ms": row["duration_ms"],
            "parent_trace_id": row["parent_trace_id"],
            "data": json.loads(row["data"]),
            "input_tokens": row["input_tokens"],
            "output_tokens": row["output_tokens"],
            "model_used": row["model_used"],
            "provider_used": row["provider_used"],
            "cost_usd": row["cost_usd"],
            "raw_input": row["raw_input"],
            "raw_output": row["raw_output"],
            "created_at": row["created_at"],
        }

    # ==================== Formatting ====================

    def format_timeline(self, traces: list[TraceEntry]) -> str:
        """
        Format traces as human-readable timeline.

        Args:
            traces: List of trace entries

        Returns:
            Formatted string for display
        """
        if not traces:
            return "No traces found."

        lines = []
        lines.append("=" * 60)
        lines.append("TRACE TIMELINE")
        lines.append("=" * 60)

        for trace in traces:
            # Format timestamp
            ts = trace.timestamp.strftime("%H:%M:%S.%f")[:-3]

            # Format duration
            duration = f"({trace.duration_ms:.1f}ms)" if trace.duration_ms else ""

            # Format main line
            line = f"[{ts}] {trace.type:<20} {duration}"
            lines.append(line)

            # Add relevant data
            if trace.data:
                for key, value in list(trace.data.items())[:3]:  # Show first 3 data items
                    val_str = str(value)[:50]
                    if len(str(value)) > 50:
                        val_str += "..."
                    lines.append(f"           {key}: {val_str}")

            # Add token info if present
            if trace.input_tokens or trace.output_tokens:
                tokens = f"tokens: {trace.input_tokens or 0} in / {trace.output_tokens or 0} out"
                if trace.cost_usd:
                    tokens += f" (${trace.cost_usd:.4f})"
                lines.append(f"           {tokens}")

            lines.append("")

        lines.append("=" * 60)
        return "\n".join(lines)

    def format_tree(self, traces: list[TraceEntry]) -> str:
        """
        Format traces as indented tree showing parent-child relationships.

        Args:
            traces: List of trace entries

        Returns:
            Formatted tree string
        """
        if not traces:
            return "No traces found."

        # Build parent-child map
        children: dict[str, list[TraceEntry]] = {}
        roots: list[TraceEntry] = []

        for trace in traces:
            if trace.parent_trace_id:
                if trace.parent_trace_id not in children:
                    children[trace.parent_trace_id] = []
                children[trace.parent_trace_id].append(trace)
            else:
                roots.append(trace)

        # Build tree string
        lines = []
        lines.append("=" * 60)
        lines.append("TRACE TREE")
        lines.append("=" * 60)

        def format_node(trace: TraceEntry, indent: int = 0):
            prefix = "  " * indent
            ts = trace.timestamp.strftime("%H:%M:%S")
            duration = f"({trace.duration_ms:.1f}ms)" if trace.duration_ms else ""
            lines.append(f"{prefix}[{ts}] {trace.type} {duration}")

            # Show key data
            if trace.data:
                for key, value in list(trace.data.items())[:2]:
                    val_str = str(value)[:40]
                    if len(str(value)) > 40:
                        val_str += "..."
                    lines.append(f"{prefix}  {key}: {val_str}")

            # Recurse to children
            for child in children.get(trace.id, []):
                format_node(child, indent + 1)

        for root in roots:
            format_node(root)
            lines.append("")

        lines.append("=" * 60)
        return "\n".join(lines)

    # ==================== Filtering Helpers ====================

    def filter_by_type(
        self,
        traces: list[TraceEntry],
        event_types: list[str],
    ) -> list[TraceEntry]:
        """
        Filter traces to only include specified event types.

        Args:
            traces: List of traces to filter
            event_types: Event types to include

        Returns:
            Filtered list of traces
        """
        return [t for t in traces if t.type in event_types]

    def filter_errors(self, traces: list[TraceEntry]) -> list[TraceEntry]:
        """
        Filter to only error events.

        Args:
            traces: List of traces to filter

        Returns:
            Only error traces
        """
        return [t for t in traces if t.type == "error"]

    def filter_by_duration(
        self,
        traces: list[TraceEntry],
        min_ms: float,
    ) -> list[TraceEntry]:
        """
        Filter to slow operations above threshold.

        Args:
            traces: List of traces to filter
            min_ms: Minimum duration in milliseconds

        Returns:
            Only traces with duration >= min_ms
        """
        return [t for t in traces if t.duration_ms and t.duration_ms >= min_ms]
