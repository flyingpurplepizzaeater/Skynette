"""
Workflow Storage Service

Handles persistence of workflows to YAML files and execution history to SQLite.
"""

import os
import yaml
import sqlite3
from datetime import datetime, UTC
from pathlib import Path
from typing import Optional
import logging
import json

from src.core.workflow.models import Workflow, WorkflowExecution

logger = logging.getLogger(__name__)


class WorkflowStorage:
    """Manages workflow storage in YAML files and SQLite database."""

    def __init__(self, data_dir: Optional[str] = None):
        """Initialize storage with data directory."""
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            # Default to user's app data directory
            self.data_dir = Path.home() / ".skynette"

        self.workflows_dir = self.data_dir / "workflows"
        self.db_path = self.data_dir / "skynette.db"

        # Ensure directories exist
        self.workflows_dir.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self._init_db()

    def _init_db(self):
        """Initialize SQLite database with required tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Workflow metadata table (for quick listing without reading YAML files)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS workflows (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                version TEXT,
                tags TEXT,
                created_at TEXT,
                updated_at TEXT,
                file_path TEXT
            )
        """)

        # Execution history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS executions (
                id TEXT PRIMARY KEY,
                workflow_id TEXT NOT NULL,
                status TEXT NOT NULL,
                trigger_type TEXT,
                trigger_data TEXT,
                node_results TEXT,
                started_at TEXT,
                completed_at TEXT,
                error TEXT,
                duration_ms REAL,
                FOREIGN KEY (workflow_id) REFERENCES workflows(id)
            )
        """)

        # Settings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        # Credentials table (encrypted)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS credentials (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                service TEXT NOT NULL,
                data TEXT NOT NULL,
                created_at TEXT,
                updated_at TEXT
            )
        """)

        # AI Providers table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_providers (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                enabled INTEGER DEFAULT 1,
                priority INTEGER DEFAULT 0,
                config TEXT NOT NULL,
                created_at TEXT,
                updated_at TEXT
            )
        """)

        # AI Usage Log table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_usage (
                id TEXT PRIMARY KEY,
                workflow_id TEXT,
                node_id TEXT,
                provider TEXT NOT NULL,
                model TEXT NOT NULL,
                prompt_tokens INTEGER,
                completion_tokens INTEGER,
                total_tokens INTEGER,
                cost_usd REAL,
                latency_ms INTEGER,
                timestamp TEXT,
                success INTEGER DEFAULT 1,
                error_message TEXT,
                FOREIGN KEY (workflow_id) REFERENCES workflows(id) ON DELETE CASCADE
            )
        """)

        # Create indices for ai_usage
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_ai_usage_workflow
            ON ai_usage(workflow_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_ai_usage_timestamp
            ON ai_usage(timestamp)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_ai_usage_provider
            ON ai_usage(provider)
        """)

        # Local Models table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS local_models (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                file_path TEXT NOT NULL UNIQUE,
                size_bytes INTEGER,
                quantization TEXT,
                source TEXT,
                huggingface_repo TEXT,
                downloaded_at TEXT,
                last_used TEXT,
                usage_count INTEGER DEFAULT 0
            )
        """)

        # AI Budgets table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_budgets (
                id TEXT PRIMARY KEY DEFAULT 'default',
                monthly_limit_usd REAL,
                alert_threshold REAL DEFAULT 0.8,
                email_notifications INTEGER DEFAULT 0,
                notification_email TEXT,
                reset_day INTEGER DEFAULT 1,
                created_at TEXT,
                updated_at TEXT
            )
        """)

        # Project autonomy settings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS project_autonomy (
                project_path TEXT PRIMARY KEY,
                autonomy_level TEXT NOT NULL DEFAULT 'L2',
                allowlist_rules TEXT,
                blocklist_rules TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)

        conn.commit()
        conn.close()
        logger.info(f"Database initialized at {self.db_path}")

    # ==================== Workflow Operations ====================

    def save_workflow(self, workflow: Workflow) -> str:
        """Save a workflow to YAML file and update database."""
        # Update timestamp
        workflow.updated_at = datetime.now(UTC)

        # Generate file path
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in workflow.name)
        file_name = f"{safe_name}_{workflow.id[:8]}.yaml"
        file_path = self.workflows_dir / file_name

        # Write YAML file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(workflow.to_yaml())

        # Update database metadata
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO workflows
            (id, name, description, version, tags, created_at, updated_at, file_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            workflow.id,
            workflow.name,
            workflow.description,
            workflow.version,
            json.dumps(workflow.tags),
            workflow.created_at.isoformat(),
            workflow.updated_at.isoformat(),
            str(file_path),
        ))

        conn.commit()
        conn.close()

        logger.info(f"Saved workflow '{workflow.name}' to {file_path}")
        return str(file_path)

    def load_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Load a workflow by ID."""
        # Get file path from database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT file_path FROM workflows WHERE id = ?", (workflow_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            logger.warning(f"Workflow {workflow_id} not found in database")
            return None

        file_path = Path(row[0])
        if not file_path.exists():
            logger.warning(f"Workflow file not found: {file_path}")
            return None

        # Load from YAML
        with open(file_path, "r", encoding="utf-8") as f:
            return Workflow.from_yaml(f.read())

    def delete_workflow(self, workflow_id: str) -> bool:
        """Delete a workflow."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT file_path FROM workflows WHERE id = ?", (workflow_id,))
        row = cursor.fetchone()

        if row:
            # Delete file
            file_path = Path(row[0])
            if file_path.exists():
                file_path.unlink()

            # Delete from database
            cursor.execute("DELETE FROM workflows WHERE id = ?", (workflow_id,))
            cursor.execute("DELETE FROM executions WHERE workflow_id = ?", (workflow_id,))
            conn.commit()
            conn.close()
            logger.info(f"Deleted workflow {workflow_id}")
            return True

        conn.close()
        return False

    def list_workflows(self) -> list[dict]:
        """List all workflows with metadata."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, name, description, version, tags, created_at, updated_at
            FROM workflows
            ORDER BY updated_at DESC
        """)

        workflows = []
        for row in cursor.fetchall():
            workflows.append({
                "id": row["id"],
                "name": row["name"],
                "description": row["description"],
                "version": row["version"],
                "tags": json.loads(row["tags"]) if row["tags"] else [],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            })

        conn.close()
        return workflows

    def search_workflows(self, query: str) -> list[dict]:
        """Search workflows by name or description."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, name, description, version, tags, created_at, updated_at
            FROM workflows
            WHERE name LIKE ? OR description LIKE ?
            ORDER BY updated_at DESC
        """, (f"%{query}%", f"%{query}%"))

        workflows = []
        for row in cursor.fetchall():
            workflows.append({
                "id": row["id"],
                "name": row["name"],
                "description": row["description"],
                "version": row["version"],
                "tags": json.loads(row["tags"]) if row["tags"] else [],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            })

        conn.close()
        return workflows

    # ==================== Execution History ====================

    def save_execution(self, execution: WorkflowExecution) -> str:
        """Save an execution record."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO executions
            (id, workflow_id, status, trigger_type, trigger_data, node_results,
             started_at, completed_at, error, duration_ms)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            execution.id,
            execution.workflow_id,
            execution.status,
            execution.trigger_type,
            json.dumps(execution.trigger_data),
            json.dumps([r.model_dump() for r in execution.node_results], default=str),
            execution.started_at.isoformat(),
            execution.completed_at.isoformat() if execution.completed_at else None,
            execution.error,
            execution.duration_ms,
        ))

        conn.commit()
        conn.close()
        return execution.id

    def get_executions(
        self, workflow_id: Optional[str] = None, limit: int = 100
    ) -> list[dict]:
        """Get execution history, optionally filtered by workflow."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if workflow_id:
            cursor.execute("""
                SELECT e.*, w.name as workflow_name
                FROM executions e
                LEFT JOIN workflows w ON e.workflow_id = w.id
                WHERE e.workflow_id = ?
                ORDER BY e.started_at DESC
                LIMIT ?
            """, (workflow_id, limit))
        else:
            cursor.execute("""
                SELECT e.*, w.name as workflow_name
                FROM executions e
                LEFT JOIN workflows w ON e.workflow_id = w.id
                ORDER BY e.started_at DESC
                LIMIT ?
            """, (limit,))

        executions = []
        for row in cursor.fetchall():
            executions.append({
                "id": row["id"],
                "workflow_id": row["workflow_id"],
                "workflow_name": row["workflow_name"],
                "status": row["status"],
                "trigger_type": row["trigger_type"],
                "started_at": row["started_at"],
                "completed_at": row["completed_at"],
                "error": row["error"],
                "duration_ms": row["duration_ms"],
            })

        conn.close()
        return executions

    # ==================== Settings ====================

    def get_setting(self, key: str, default: str = None) -> Optional[str]:
        """Get a setting value."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else default

    def set_setting(self, key: str, value: str):
        """Set a setting value."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, value)
        )
        conn.commit()
        conn.close()

    # ==================== Project Autonomy ====================

    def get_project_autonomy(self, project_path: str) -> dict:
        """
        Get autonomy settings for a project.

        Args:
            project_path: Project directory path

        Returns:
            Dict with keys: level, allowlist, blocklist
            Falls back to global defaults if project not found
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Normalize path
        normalized_path = str(Path(project_path).resolve())

        cursor.execute("""
            SELECT autonomy_level, allowlist_rules, blocklist_rules
            FROM project_autonomy
            WHERE project_path = ?
        """, (normalized_path,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                "level": row["autonomy_level"],
                "allowlist": json.loads(row["allowlist_rules"] or "[]"),
                "blocklist": json.loads(row["blocklist_rules"] or "[]"),
            }

        # Return defaults
        return {
            "level": self.get_setting("default_autonomy_level", "L2"),
            "allowlist": json.loads(self.get_setting("global_allowlist", "[]")),
            "blocklist": json.loads(self.get_setting("global_blocklist", "[]")),
        }

    def set_project_autonomy(
        self,
        project_path: str,
        level: str,
        allowlist: list | None = None,
        blocklist: list | None = None,
    ) -> None:
        """
        Set autonomy settings for a project.

        Args:
            project_path: Project directory path
            level: Autonomy level (L1, L2, L3, L4)
            allowlist: Optional list of allowlist rules
            blocklist: Optional list of blocklist rules
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Normalize path
        normalized_path = str(Path(project_path).resolve())
        now = datetime.now(UTC).isoformat()

        # Check if exists
        cursor.execute(
            "SELECT created_at FROM project_autonomy WHERE project_path = ?",
            (normalized_path,)
        )
        existing = cursor.fetchone()

        if existing:
            # Update
            cursor.execute("""
                UPDATE project_autonomy
                SET autonomy_level = ?,
                    allowlist_rules = ?,
                    blocklist_rules = ?,
                    updated_at = ?
                WHERE project_path = ?
            """, (
                level,
                json.dumps(allowlist) if allowlist is not None else None,
                json.dumps(blocklist) if blocklist is not None else None,
                now,
                normalized_path,
            ))
        else:
            # Insert
            cursor.execute("""
                INSERT INTO project_autonomy
                (project_path, autonomy_level, allowlist_rules, blocklist_rules, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                normalized_path,
                level,
                json.dumps(allowlist) if allowlist is not None else None,
                json.dumps(blocklist) if blocklist is not None else None,
                now,
                now,
            ))

        conn.commit()
        conn.close()
        logger.info(f"Set autonomy level {level} for {normalized_path}")

    def delete_project_autonomy(self, project_path: str) -> bool:
        """
        Delete autonomy settings for a project.

        Args:
            project_path: Project directory path

        Returns:
            True if deleted, False if not found
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        normalized_path = str(Path(project_path).resolve())

        cursor.execute(
            "DELETE FROM project_autonomy WHERE project_path = ?",
            (normalized_path,)
        )

        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()

        return deleted


# Global storage instance
_storage: Optional[WorkflowStorage] = None


def get_storage() -> WorkflowStorage:
    """Get the global storage instance."""
    global _storage
    if _storage is None:
        _storage = WorkflowStorage()
    return _storage
