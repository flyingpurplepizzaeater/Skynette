# src/rag/storage.py
"""
RAG Storage Layer

SQLite-based storage for RAG metadata (collections, documents, chunks).
ChromaDB handles vector embeddings separately.
"""

import sqlite3
import json
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from src.rag.models import Collection, Document, Chunk


class RAGStorage:
    """SQLite storage for RAG metadata."""

    def __init__(self, db_path: str):
        """Initialize storage with database path."""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize database schema."""
        schema_path = Path(__file__).parent / "schema.sql"
        with open(schema_path, 'r') as f:
            schema = f.read()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            conn.executescript(schema)

    # Collection methods

    def save_collection(self, collection: Collection) -> None:
        """Save or update collection."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            cursor = conn.cursor()

            cursor.execute("""
                INSERT OR REPLACE INTO rag_collections
                (id, name, description, embedding_model, chunk_size, chunk_overlap,
                 max_chunk_size, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                collection.id,
                collection.name,
                collection.description,
                collection.embedding_model,
                collection.chunk_size,
                collection.chunk_overlap,
                collection.max_chunk_size,
                collection.created_at.isoformat(),
                collection.updated_at.isoformat()
            ))

    def get_collection(self, collection_id: str) -> Optional[Collection]:
        """Get collection by ID."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, name, description, embedding_model, chunk_size, chunk_overlap,
                       max_chunk_size, created_at, updated_at
                FROM rag_collections
                WHERE id = ?
            """, (collection_id,))

            row = cursor.fetchone()

        if not row:
            return None

        return Collection(
            id=row[0],
            name=row[1],
            description=row[2],
            embedding_model=row[3],
            chunk_size=row[4],
            chunk_overlap=row[5],
            max_chunk_size=row[6],
            created_at=datetime.fromisoformat(row[7]),
            updated_at=datetime.fromisoformat(row[8])
        )

    def list_collections(self) -> List[Collection]:
        """List all collections."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, name, description, embedding_model, chunk_size, chunk_overlap,
                       max_chunk_size, created_at, updated_at
                FROM rag_collections
                ORDER BY created_at DESC
            """)

            rows = cursor.fetchall()

        return [
            Collection(
                id=row[0],
                name=row[1],
                description=row[2],
                embedding_model=row[3],
                chunk_size=row[4],
                chunk_overlap=row[5],
                max_chunk_size=row[6],
                created_at=datetime.fromisoformat(row[7]),
                updated_at=datetime.fromisoformat(row[8])
            )
            for row in rows
        ]

    def delete_collection(self, collection_id: str) -> None:
        """Delete collection (cascades to documents/chunks)."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM rag_collections WHERE id = ?", (collection_id,))

    # Document methods

    def save_document(self, document: Document) -> None:
        """Save or update document."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            cursor = conn.cursor()

            cursor.execute("""
                INSERT OR REPLACE INTO rag_documents
                (id, collection_id, source_path, file_type, file_hash, file_size,
                 chunk_count, indexed_at, last_updated, status, error)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                document.id,
                document.collection_id,
                document.source_path,
                document.file_type,
                document.file_hash,
                document.file_size,
                document.chunk_count,
                document.indexed_at.isoformat() if document.indexed_at else None,
                document.last_updated.isoformat() if document.last_updated else None,
                document.status,
                document.error
            ))

    def get_document(self, document_id: str) -> Optional[Document]:
        """Get document by ID."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, collection_id, source_path, file_type, file_hash, file_size,
                       chunk_count, indexed_at, last_updated, status, error
                FROM rag_documents
                WHERE id = ?
            """, (document_id,))

            row = cursor.fetchone()

        if not row:
            return None

        return Document(
            id=row[0],
            collection_id=row[1],
            source_path=row[2],
            file_type=row[3],
            file_hash=row[4],
            file_size=row[5],
            chunk_count=row[6],
            indexed_at=datetime.fromisoformat(row[7]) if row[7] else None,
            last_updated=datetime.fromisoformat(row[8]) if row[8] else None,
            status=row[9],
            error=row[10]
        )

    # Chunk methods

    def save_chunk(self, chunk: Chunk) -> None:
        """Save chunk."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            cursor = conn.cursor()

            cursor.execute("""
                INSERT OR REPLACE INTO rag_chunks
                (id, document_id, chunk_index, content, embedding_hash, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                chunk.id,
                chunk.document_id,
                chunk.chunk_index,
                chunk.content,
                chunk.embedding_hash,
                json.dumps(chunk.metadata),
                chunk.created_at.isoformat()
            ))

    def get_chunk(self, chunk_id: str) -> Optional[Chunk]:
        """Get chunk by ID."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, document_id, chunk_index, content, embedding_hash, metadata, created_at
                FROM rag_chunks
                WHERE id = ?
            """, (chunk_id,))

            row = cursor.fetchone()

        if not row:
            return None

        return Chunk(
            id=row[0],
            document_id=row[1],
            chunk_index=row[2],
            content=row[3],
            embedding_hash=row[4],
            metadata=json.loads(row[5]) if row[5] else {},
            created_at=datetime.fromisoformat(row[6])
        )

    def get_document_chunks(self, document_id: str) -> List[Chunk]:
        """Get all chunks for a document."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, document_id, chunk_index, content, embedding_hash, metadata, created_at
                FROM rag_chunks
                WHERE document_id = ?
                ORDER BY chunk_index
            """, (document_id,))

            rows = cursor.fetchall()

        return [
            Chunk(
                id=row[0],
                document_id=row[1],
                chunk_index=row[2],
                content=row[3],
                embedding_hash=row[4],
                metadata=json.loads(row[5]) if row[5] else {},
                created_at=datetime.fromisoformat(row[6])
            )
            for row in rows
        ]
