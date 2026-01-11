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
        self._connection = None
        self._init_db()

    def _get_connection(self):
        """Get or create database connection."""
        if self._connection is None:
            self._connection = sqlite3.connect(self.db_path)
            self._connection.execute("PRAGMA foreign_keys = ON")
        return self._connection

    def close(self):
        """Close database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def _init_db(self):
        """Initialize database schema."""
        schema_path = Path(__file__).parent / "schema.sql"
        try:
            with open(schema_path, 'r') as f:
                schema = f.read()
        except FileNotFoundError:
            raise RuntimeError(
                f"Database schema file not found at {schema_path}. "
                "Ensure schema.sql is included in the package."
            )

        try:
            conn = self._get_connection()
            conn.executescript(schema)
            conn.commit()
        except sqlite3.Error as e:
            raise RuntimeError(f"Failed to initialize database: {e}")

    # Collection methods

    def save_collection(self, collection: Collection) -> None:
        """Save or update collection."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Check for duplicate name with different ID
            cursor.execute("""
                SELECT id FROM rag_collections WHERE name = ?
            """, (collection.name,))
            existing = cursor.fetchone()
            if existing and existing[0] != collection.id:
                raise ValueError(f"Collection name '{collection.name}' already exists")

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

            conn.commit()
        except sqlite3.IntegrityError as e:
            conn.rollback()
            raise RuntimeError(f"Database integrity error: {e}")
        except sqlite3.Error as e:
            conn.rollback()
            raise RuntimeError(f"Failed to save collection: {e}")

    def get_collection(self, collection_id: str) -> Optional[Collection]:
        """Get collection by ID."""
        conn = self._get_connection()
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
        conn = self._get_connection()
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
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM rag_collections WHERE id = ?", (collection_id,))
        conn.commit()

    # Document methods

    def get_collection_documents(self, collection_id: str) -> List[Document]:
        """Get all documents in a collection."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, collection_id, source_path, file_type, file_hash, file_size,
                   chunk_count, indexed_at, last_updated, status, error
            FROM rag_documents
            WHERE collection_id = ?
        """, (collection_id,))

        rows = cursor.fetchall()

        return [
            Document(
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
                error=row[10],
            )
            for row in rows
        ]

    def save_document(self, document: Document) -> None:
        """Save or update document."""
        try:
            conn = self._get_connection()
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

            conn.commit()
        except sqlite3.IntegrityError as e:
            conn.rollback()
            if "FOREIGN KEY constraint failed" in str(e):
                raise ValueError(f"Collection '{document.collection_id}' does not exist")
            raise RuntimeError(f"Database integrity error: {e}")
        except sqlite3.Error as e:
            conn.rollback()
            raise RuntimeError(f"Failed to save document: {e}")

    def get_document(self, document_id: str) -> Optional[Document]:
        """Get document by ID."""
        conn = self._get_connection()
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
        try:
            conn = self._get_connection()
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
                json.dumps(chunk.metadata) if chunk.metadata else None,
                chunk.created_at.isoformat()
            ))

            conn.commit()
        except sqlite3.IntegrityError as e:
            conn.rollback()
            if "FOREIGN KEY constraint failed" in str(e):
                raise ValueError(f"Document '{chunk.document_id}' does not exist")
            raise RuntimeError(f"Database integrity error: {e}")
        except sqlite3.Error as e:
            conn.rollback()
            raise RuntimeError(f"Failed to save chunk: {e}")

    def get_chunk(self, chunk_id: str) -> Optional[Chunk]:
        """Get chunk by ID."""
        conn = self._get_connection()
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
        conn = self._get_connection()
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
