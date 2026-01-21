"""
MCP Server Storage

SQLite persistence for MCP server configurations and tool approvals.
Follows the pattern from src/data/storage.py.
"""

import json
import sqlite3
from datetime import datetime, UTC
from pathlib import Path
from typing import Optional
from uuid import uuid4

from src.agent.mcp.models.server import MCPServerConfig, ServerCategory
from src.agent.mcp.models.trust import ToolApproval


class MCPServerStorage:
    """Manages MCP server configuration persistence in SQLite.

    Uses the same database as WorkflowStorage (~/.skynette/skynette.db).
    """

    def __init__(self, db_path: Optional[str] = None):
        """Initialize storage with database path.

        Args:
            db_path: Path to SQLite database. Defaults to ~/.skynette/skynette.db
        """
        if db_path:
            self.db_path = Path(db_path)
        else:
            self.db_path = Path.home() / ".skynette" / "skynette.db"

        # Ensure parent directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize tables
        self._init_tables()

    def _init_tables(self) -> None:
        """Create MCP-related tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            # MCP servers table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS mcp_servers (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    transport TEXT NOT NULL,
                    command TEXT,
                    args TEXT,
                    env TEXT,
                    url TEXT,
                    headers TEXT,
                    trust_level TEXT NOT NULL,
                    sandbox_enabled INTEGER DEFAULT 1,
                    category TEXT,
                    enabled INTEGER DEFAULT 1,
                    created_at TEXT,
                    last_connected TEXT,
                    last_error TEXT
                )
            """)

            # Tool approvals table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS mcp_tool_approvals (
                    id TEXT PRIMARY KEY,
                    server_id TEXT NOT NULL,
                    tool_name TEXT NOT NULL,
                    approved INTEGER DEFAULT 0,
                    approved_at TEXT,
                    UNIQUE(server_id, tool_name)
                )
            """)

            # Index for efficient lookups
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_mcp_servers_category
                ON mcp_servers(category)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_mcp_servers_enabled
                ON mcp_servers(enabled)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_mcp_tool_approvals_server
                ON mcp_tool_approvals(server_id)
            """)

            conn.commit()

    def save_server(self, config: MCPServerConfig) -> None:
        """Save or update an MCP server configuration.

        Args:
            config: Server configuration to save
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO mcp_servers
                (id, name, description, transport, command, args, env, url, headers,
                 trust_level, sandbox_enabled, category, enabled, created_at,
                 last_connected, last_error)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                config.id,
                config.name,
                config.description,
                config.transport,
                config.command,
                json.dumps(config.args),
                json.dumps(config.env),
                config.url,
                json.dumps(config.headers),
                config.trust_level,
                1 if config.sandbox_enabled else 0,
                config.category,
                1 if config.enabled else 0,
                config.created_at.isoformat(),
                config.last_connected.isoformat() if config.last_connected else None,
                config.last_error,
            ))
            conn.commit()

    def get_server(self, server_id: str) -> Optional[MCPServerConfig]:
        """Get a server configuration by ID.

        Args:
            server_id: Unique server identifier

        Returns:
            Server configuration or None if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM mcp_servers WHERE id = ?",
                (server_id,)
            )
            row = cursor.fetchone()

            if not row:
                return None

            return self._row_to_config(row)

    def list_servers(self, enabled_only: bool = False) -> list[MCPServerConfig]:
        """List all server configurations.

        Args:
            enabled_only: If True, only return enabled servers

        Returns:
            List of server configurations
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            if enabled_only:
                cursor = conn.execute(
                    "SELECT * FROM mcp_servers WHERE enabled = 1 ORDER BY name"
                )
            else:
                cursor = conn.execute(
                    "SELECT * FROM mcp_servers ORDER BY name"
                )

            return [self._row_to_config(row) for row in cursor.fetchall()]

    def delete_server(self, server_id: str) -> bool:
        """Delete a server configuration.

        Args:
            server_id: Unique server identifier

        Returns:
            True if server was deleted, False if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM mcp_servers WHERE id = ?",
                (server_id,)
            )
            # Also delete associated tool approvals
            conn.execute(
                "DELETE FROM mcp_tool_approvals WHERE server_id = ?",
                (server_id,)
            )
            conn.commit()
            return cursor.rowcount > 0

    def get_servers_by_category(
        self, category: ServerCategory
    ) -> list[MCPServerConfig]:
        """Get servers by category.

        Per 09-CONTEXT.md: Organize by category, not transport.

        Args:
            category: Server category to filter by

        Returns:
            List of servers in the category
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM mcp_servers WHERE category = ? ORDER BY name",
                (category,)
            )
            return [self._row_to_config(row) for row in cursor.fetchall()]

    def save_tool_approval(self, approval: ToolApproval) -> None:
        """Save or update a tool approval.

        Args:
            approval: Tool approval to save
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO mcp_tool_approvals
                (id, server_id, tool_name, approved, approved_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                approval.id,
                approval.server_id,
                approval.tool_name,
                1 if approval.approved else 0,
                approval.approved_at.isoformat() if approval.approved_at else None,
            ))
            conn.commit()

    def get_tool_approval(
        self, server_id: str, tool_name: str
    ) -> Optional[ToolApproval]:
        """Get a tool approval record.

        Args:
            server_id: Server the tool belongs to
            tool_name: Name of the tool

        Returns:
            Tool approval record or None if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM mcp_tool_approvals
                WHERE server_id = ? AND tool_name = ?
            """, (server_id, tool_name))
            row = cursor.fetchone()

            if not row:
                return None

            return ToolApproval(
                id=row["id"],
                server_id=row["server_id"],
                tool_name=row["tool_name"],
                approved=bool(row["approved"]),
                approved_at=datetime.fromisoformat(row["approved_at"])
                if row["approved_at"] else None,
            )

    def is_tool_approved(self, server_id: str, tool_name: str) -> bool:
        """Check if a tool is approved for use.

        Per 09-CONTEXT.md: First-use approval, then remember.

        Args:
            server_id: Server the tool belongs to
            tool_name: Name of the tool

        Returns:
            True if tool is approved
        """
        approval = self.get_tool_approval(server_id, tool_name)
        return approval.approved if approval else False

    def _row_to_config(self, row: sqlite3.Row) -> MCPServerConfig:
        """Convert a database row to MCPServerConfig.

        Args:
            row: Database row

        Returns:
            MCPServerConfig instance
        """
        return MCPServerConfig(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            transport=row["transport"],
            command=row["command"],
            args=json.loads(row["args"]) if row["args"] else [],
            env=json.loads(row["env"]) if row["env"] else {},
            url=row["url"],
            headers=json.loads(row["headers"]) if row["headers"] else {},
            trust_level=row["trust_level"],
            sandbox_enabled=bool(row["sandbox_enabled"]),
            category=row["category"] or "other",
            enabled=bool(row["enabled"]),
            created_at=datetime.fromisoformat(row["created_at"])
            if row["created_at"] else datetime.now(UTC),
            last_connected=datetime.fromisoformat(row["last_connected"])
            if row["last_connected"] else None,
            last_error=row["last_error"],
        )


# Module-level singleton
_mcp_storage: Optional[MCPServerStorage] = None


def get_mcp_storage() -> MCPServerStorage:
    """Get the global MCP storage instance.

    Returns:
        MCPServerStorage singleton instance
    """
    global _mcp_storage
    if _mcp_storage is None:
        _mcp_storage = MCPServerStorage()
    return _mcp_storage
