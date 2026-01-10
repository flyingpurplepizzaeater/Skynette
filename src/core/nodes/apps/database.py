"""
Database Nodes - Query and manipulate databases.
"""

import asyncio
from typing import Any, Optional

from src.core.nodes.base import BaseNode, NodeField, FieldType


class SQLiteQueryNode(BaseNode):
    """
    Execute SQLite queries.

    Supports:
    - SELECT queries with parameter binding
    - INSERT, UPDATE, DELETE operations
    - Creating tables
    - Transaction support
    """

    type = "sqlite-query"
    name = "SQLite: Query"
    category = "Data"
    description = "Execute SQLite database queries"
    icon = "storage"
    color = "#003B57"  # SQLite blue

    inputs = [
        NodeField(
            name="database",
            label="Database Path",
            type=FieldType.STRING,
            required=True,
            description="Path to SQLite database file.",
        ),
        NodeField(
            name="query",
            label="SQL Query",
            type=FieldType.TEXT,
            required=True,
            description="SQL query to execute. Use ? for parameters.",
        ),
        NodeField(
            name="parameters",
            label="Parameters",
            type=FieldType.JSON,
            required=False,
            description="Query parameters as JSON array.",
        ),
        NodeField(
            name="operation",
            label="Operation Type",
            type=FieldType.SELECT,
            required=False,
            default="query",
            options=[
                {"value": "query", "label": "Query (SELECT)"},
                {"value": "execute", "label": "Execute (INSERT/UPDATE/DELETE)"},
                {"value": "executemany", "label": "Execute Many (batch)"},
            ],
            description="Type of database operation.",
        ),
    ]

    outputs = [
        NodeField(
            name="rows",
            label="Rows",
            type=FieldType.JSON,
            description="Query results as list of objects.",
        ),
        NodeField(
            name="row_count",
            label="Row Count",
            type=FieldType.NUMBER,
            description="Number of rows returned/affected.",
        ),
        NodeField(
            name="last_id",
            label="Last Insert ID",
            type=FieldType.NUMBER,
            description="ID of last inserted row.",
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """Execute SQLite query."""
        import sqlite3

        database = config.get("database", "")
        query = config.get("query", "")
        parameters = config.get("parameters", [])
        operation = config.get("operation", "query")

        # Ensure parameters is a list
        if isinstance(parameters, str):
            import json
            try:
                parameters = json.loads(parameters)
            except:
                parameters = []

        loop = asyncio.get_event_loop()

        def run_query():
            conn = sqlite3.connect(database)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            try:
                if operation == "query":
                    cursor.execute(query, parameters or [])
                    rows = [dict(row) for row in cursor.fetchall()]
                    return {
                        "rows": rows,
                        "row_count": len(rows),
                        "last_id": 0,
                    }
                elif operation == "execute":
                    cursor.execute(query, parameters or [])
                    conn.commit()
                    return {
                        "rows": [],
                        "row_count": cursor.rowcount,
                        "last_id": cursor.lastrowid,
                    }
                elif operation == "executemany":
                    cursor.executemany(query, parameters or [])
                    conn.commit()
                    return {
                        "rows": [],
                        "row_count": cursor.rowcount,
                        "last_id": cursor.lastrowid,
                    }
            finally:
                conn.close()

        result = await loop.run_in_executor(None, run_query)
        return result


class PostgreSQLQueryNode(BaseNode):
    """
    Execute PostgreSQL queries.

    Requires asyncpg library.
    """

    type = "postgresql-query"
    name = "PostgreSQL: Query"
    category = "Data"
    description = "Execute PostgreSQL database queries"
    icon = "storage"
    color = "#336791"  # PostgreSQL blue

    inputs = [
        NodeField(
            name="connection_string",
            label="Connection String",
            type=FieldType.SECRET,
            required=True,
            description="PostgreSQL connection string (postgresql://user:pass@host:port/db).",
        ),
        NodeField(
            name="query",
            label="SQL Query",
            type=FieldType.TEXT,
            required=True,
            description="SQL query to execute. Use $1, $2, etc. for parameters.",
        ),
        NodeField(
            name="parameters",
            label="Parameters",
            type=FieldType.JSON,
            required=False,
            description="Query parameters as JSON array.",
        ),
        NodeField(
            name="operation",
            label="Operation Type",
            type=FieldType.SELECT,
            required=False,
            default="fetch",
            options=[
                {"value": "fetch", "label": "Fetch All (SELECT)"},
                {"value": "fetchrow", "label": "Fetch One Row"},
                {"value": "execute", "label": "Execute (INSERT/UPDATE/DELETE)"},
            ],
            description="Type of database operation.",
        ),
    ]

    outputs = [
        NodeField(
            name="rows",
            label="Rows",
            type=FieldType.JSON,
            description="Query results.",
        ),
        NodeField(
            name="row_count",
            label="Row Count",
            type=FieldType.NUMBER,
            description="Number of rows returned/affected.",
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """Execute PostgreSQL query."""
        try:
            import asyncpg
        except ImportError:
            raise RuntimeError(
                "asyncpg not installed. Install with: pip install asyncpg"
            )

        connection_string = config.get("connection_string", "")
        query = config.get("query", "")
        parameters = config.get("parameters", [])
        operation = config.get("operation", "fetch")

        # Ensure parameters is a list
        if isinstance(parameters, str):
            import json
            try:
                parameters = json.loads(parameters)
            except:
                parameters = []

        conn = await asyncpg.connect(connection_string)

        try:
            if operation == "fetch":
                rows = await conn.fetch(query, *parameters)
                rows = [dict(row) for row in rows]
                return {
                    "rows": rows,
                    "row_count": len(rows),
                }
            elif operation == "fetchrow":
                row = await conn.fetchrow(query, *parameters)
                if row:
                    return {
                        "rows": [dict(row)],
                        "row_count": 1,
                    }
                return {
                    "rows": [],
                    "row_count": 0,
                }
            elif operation == "execute":
                result = await conn.execute(query, *parameters)
                # Parse affected row count from result string
                count = 0
                if result:
                    parts = result.split()
                    if len(parts) >= 2 and parts[-1].isdigit():
                        count = int(parts[-1])
                return {
                    "rows": [],
                    "row_count": count,
                }
        finally:
            await conn.close()
