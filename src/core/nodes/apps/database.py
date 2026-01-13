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


class MySQLQueryNode(BaseNode):
    """
    Execute MySQL queries.

    Requires aiomysql library.
    """

    type = "mysql-query"
    name = "MySQL: Query"
    category = "Data"
    description = "Execute MySQL database queries"
    icon = "storage"
    color = "#4479A1"  # MySQL blue

    inputs = [
        NodeField(
            name="host",
            label="Host",
            type=FieldType.STRING,
            required=True,
            default="localhost",
            description="MySQL server hostname.",
        ),
        NodeField(
            name="port",
            label="Port",
            type=FieldType.NUMBER,
            required=False,
            default=3306,
            description="MySQL server port.",
        ),
        NodeField(
            name="database",
            label="Database",
            type=FieldType.STRING,
            required=True,
            description="Database name.",
        ),
        NodeField(
            name="username",
            label="Username",
            type=FieldType.STRING,
            required=True,
            description="Database username.",
        ),
        NodeField(
            name="password",
            label="Password",
            type=FieldType.SECRET,
            required=True,
            description="Database password.",
        ),
        NodeField(
            name="query",
            label="SQL Query",
            type=FieldType.TEXT,
            required=True,
            description="SQL query to execute. Use %s for parameters.",
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
                {"value": "fetchone", "label": "Fetch One Row"},
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
        NodeField(
            name="last_id",
            label="Last Insert ID",
            type=FieldType.NUMBER,
            description="ID of last inserted row.",
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """Execute MySQL query."""
        try:
            import aiomysql
        except ImportError:
            raise RuntimeError(
                "aiomysql not installed. Install with: pip install aiomysql"
            )

        host = config.get("host", "localhost")
        port = config.get("port", 3306)
        database = config.get("database", "")
        username = config.get("username", "")
        password = config.get("password", "")
        query = config.get("query", "")
        parameters = config.get("parameters", [])
        operation = config.get("operation", "fetch")

        # Ensure parameters is a tuple
        if isinstance(parameters, str):
            import json
            try:
                parameters = json.loads(parameters)
            except:
                parameters = []
        if parameters:
            parameters = tuple(parameters)

        conn = await aiomysql.connect(
            host=host,
            port=int(port),
            db=database,
            user=username,
            password=password,
            autocommit=True,
        )

        try:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                if operation == "fetch":
                    await cursor.execute(query, parameters or ())
                    rows = await cursor.fetchall()
                    return {
                        "rows": list(rows),
                        "row_count": len(rows),
                        "last_id": 0,
                    }
                elif operation == "fetchone":
                    await cursor.execute(query, parameters or ())
                    row = await cursor.fetchone()
                    if row:
                        return {
                            "rows": [row],
                            "row_count": 1,
                            "last_id": 0,
                        }
                    return {
                        "rows": [],
                        "row_count": 0,
                        "last_id": 0,
                    }
                elif operation == "execute":
                    await cursor.execute(query, parameters or ())
                    return {
                        "rows": [],
                        "row_count": cursor.rowcount,
                        "last_id": cursor.lastrowid or 0,
                    }
        finally:
            conn.close()


class MongoDBQueryNode(BaseNode):
    """
    Query MongoDB collections.

    Requires motor library (async MongoDB driver).
    """

    type = "mongodb-query"
    name = "MongoDB: Query"
    category = "Data"
    description = "Query MongoDB collections"
    icon = "storage"
    color = "#47A248"  # MongoDB green

    inputs = [
        NodeField(
            name="connection_string",
            label="Connection String",
            type=FieldType.SECRET,
            required=True,
            description="MongoDB connection string (mongodb://...).",
        ),
        NodeField(
            name="database",
            label="Database",
            type=FieldType.STRING,
            required=True,
            description="Database name.",
        ),
        NodeField(
            name="collection",
            label="Collection",
            type=FieldType.STRING,
            required=True,
            description="Collection name.",
        ),
        NodeField(
            name="operation",
            label="Operation",
            type=FieldType.SELECT,
            required=True,
            default="find",
            options=[
                {"value": "find", "label": "Find Documents"},
                {"value": "find_one", "label": "Find One Document"},
                {"value": "count", "label": "Count Documents"},
                {"value": "aggregate", "label": "Aggregate Pipeline"},
            ],
            description="MongoDB operation to perform.",
        ),
        NodeField(
            name="query",
            label="Query/Filter",
            type=FieldType.JSON,
            required=False,
            default="{}",
            description="MongoDB query filter as JSON.",
        ),
        NodeField(
            name="projection",
            label="Projection",
            type=FieldType.JSON,
            required=False,
            description="Fields to include/exclude as JSON.",
        ),
        NodeField(
            name="sort",
            label="Sort",
            type=FieldType.JSON,
            required=False,
            description="Sort specification as JSON (e.g., {\"name\": 1}).",
        ),
        NodeField(
            name="limit",
            label="Limit",
            type=FieldType.NUMBER,
            required=False,
            default=100,
            description="Maximum number of documents to return.",
        ),
    ]

    outputs = [
        NodeField(
            name="documents",
            label="Documents",
            type=FieldType.JSON,
            description="Retrieved documents.",
        ),
        NodeField(
            name="count",
            label="Count",
            type=FieldType.NUMBER,
            description="Number of documents returned/counted.",
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """Execute MongoDB query."""
        try:
            from motor.motor_asyncio import AsyncIOMotorClient
        except ImportError:
            raise RuntimeError(
                "motor not installed. Install with: pip install motor"
            )

        connection_string = config.get("connection_string", "")
        database = config.get("database", "")
        collection_name = config.get("collection", "")
        operation = config.get("operation", "find")
        query = config.get("query", "{}")
        projection = config.get("projection", None)
        sort = config.get("sort", None)
        limit = config.get("limit", 100)

        # Parse JSON strings
        import json
        if isinstance(query, str):
            try:
                query = json.loads(query)
            except:
                query = {}
        if isinstance(projection, str):
            try:
                projection = json.loads(projection) if projection else None
            except:
                projection = None
        if isinstance(sort, str):
            try:
                sort = json.loads(sort) if sort else None
            except:
                sort = None

        client = AsyncIOMotorClient(connection_string)
        try:
            db = client[database]
            collection = db[collection_name]

            if operation == "find":
                cursor = collection.find(query, projection)
                if sort:
                    cursor = cursor.sort(list(sort.items()))
                if limit:
                    cursor = cursor.limit(int(limit))

                documents = []
                async for doc in cursor:
                    # Convert ObjectId to string for JSON serialization
                    if "_id" in doc:
                        doc["_id"] = str(doc["_id"])
                    documents.append(doc)

                return {
                    "documents": documents,
                    "count": len(documents),
                }

            elif operation == "find_one":
                doc = await collection.find_one(query, projection)
                if doc:
                    if "_id" in doc:
                        doc["_id"] = str(doc["_id"])
                    return {
                        "documents": [doc],
                        "count": 1,
                    }
                return {
                    "documents": [],
                    "count": 0,
                }

            elif operation == "count":
                count = await collection.count_documents(query)
                return {
                    "documents": [],
                    "count": count,
                }

            elif operation == "aggregate":
                # For aggregate, query should be the pipeline array
                pipeline = query if isinstance(query, list) else [query]
                cursor = collection.aggregate(pipeline)

                documents = []
                async for doc in cursor:
                    if "_id" in doc:
                        doc["_id"] = str(doc["_id"])
                    documents.append(doc)

                return {
                    "documents": documents,
                    "count": len(documents),
                }

        finally:
            client.close()


class MongoDBWriteNode(BaseNode):
    """
    Write to MongoDB collections.

    Supports insert, update, and delete operations.
    Requires motor library.
    """

    type = "mongodb-write"
    name = "MongoDB: Write"
    category = "Data"
    description = "Insert, update, or delete MongoDB documents"
    icon = "edit"
    color = "#47A248"

    inputs = [
        NodeField(
            name="connection_string",
            label="Connection String",
            type=FieldType.SECRET,
            required=True,
            description="MongoDB connection string.",
        ),
        NodeField(
            name="database",
            label="Database",
            type=FieldType.STRING,
            required=True,
            description="Database name.",
        ),
        NodeField(
            name="collection",
            label="Collection",
            type=FieldType.STRING,
            required=True,
            description="Collection name.",
        ),
        NodeField(
            name="operation",
            label="Operation",
            type=FieldType.SELECT,
            required=True,
            default="insert_one",
            options=[
                {"value": "insert_one", "label": "Insert One"},
                {"value": "insert_many", "label": "Insert Many"},
                {"value": "update_one", "label": "Update One"},
                {"value": "update_many", "label": "Update Many"},
                {"value": "delete_one", "label": "Delete One"},
                {"value": "delete_many", "label": "Delete Many"},
                {"value": "replace_one", "label": "Replace One"},
            ],
            description="Write operation to perform.",
        ),
        NodeField(
            name="filter",
            label="Filter",
            type=FieldType.JSON,
            required=False,
            description="Query filter for update/delete operations.",
        ),
        NodeField(
            name="document",
            label="Document",
            type=FieldType.JSON,
            required=False,
            description="Document(s) to insert, or update document.",
        ),
        NodeField(
            name="upsert",
            label="Upsert",
            type=FieldType.BOOLEAN,
            required=False,
            default=False,
            description="Create document if it doesn't exist (update operations).",
        ),
    ]

    outputs = [
        NodeField(
            name="success",
            label="Success",
            type=FieldType.BOOLEAN,
            description="Whether the operation was successful.",
        ),
        NodeField(
            name="inserted_id",
            label="Inserted ID",
            type=FieldType.STRING,
            description="ID of inserted document.",
        ),
        NodeField(
            name="matched_count",
            label="Matched Count",
            type=FieldType.NUMBER,
            description="Number of documents matched.",
        ),
        NodeField(
            name="modified_count",
            label="Modified Count",
            type=FieldType.NUMBER,
            description="Number of documents modified.",
        ),
        NodeField(
            name="deleted_count",
            label="Deleted Count",
            type=FieldType.NUMBER,
            description="Number of documents deleted.",
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """Execute MongoDB write operation."""
        try:
            from motor.motor_asyncio import AsyncIOMotorClient
        except ImportError:
            raise RuntimeError(
                "motor not installed. Install with: pip install motor"
            )

        connection_string = config.get("connection_string", "")
        database = config.get("database", "")
        collection_name = config.get("collection", "")
        operation = config.get("operation", "insert_one")
        filter_doc = config.get("filter", "{}")
        document = config.get("document", "{}")
        upsert = config.get("upsert", False)

        # Parse JSON strings
        import json
        if isinstance(filter_doc, str):
            try:
                filter_doc = json.loads(filter_doc)
            except:
                filter_doc = {}
        if isinstance(document, str):
            try:
                document = json.loads(document)
            except:
                document = {}

        client = AsyncIOMotorClient(connection_string)
        try:
            db = client[database]
            collection = db[collection_name]

            result = {
                "success": False,
                "inserted_id": "",
                "matched_count": 0,
                "modified_count": 0,
                "deleted_count": 0,
            }

            if operation == "insert_one":
                res = await collection.insert_one(document)
                result["success"] = res.acknowledged
                result["inserted_id"] = str(res.inserted_id)

            elif operation == "insert_many":
                docs = document if isinstance(document, list) else [document]
                res = await collection.insert_many(docs)
                result["success"] = res.acknowledged
                result["inserted_id"] = str(res.inserted_ids[0]) if res.inserted_ids else ""

            elif operation == "update_one":
                res = await collection.update_one(filter_doc, document, upsert=upsert)
                result["success"] = res.acknowledged
                result["matched_count"] = res.matched_count
                result["modified_count"] = res.modified_count
                if res.upserted_id:
                    result["inserted_id"] = str(res.upserted_id)

            elif operation == "update_many":
                res = await collection.update_many(filter_doc, document, upsert=upsert)
                result["success"] = res.acknowledged
                result["matched_count"] = res.matched_count
                result["modified_count"] = res.modified_count

            elif operation == "delete_one":
                res = await collection.delete_one(filter_doc)
                result["success"] = res.acknowledged
                result["deleted_count"] = res.deleted_count

            elif operation == "delete_many":
                res = await collection.delete_many(filter_doc)
                result["success"] = res.acknowledged
                result["deleted_count"] = res.deleted_count

            elif operation == "replace_one":
                res = await collection.replace_one(filter_doc, document, upsert=upsert)
                result["success"] = res.acknowledged
                result["matched_count"] = res.matched_count
                result["modified_count"] = res.modified_count

            return result

        finally:
            client.close()
