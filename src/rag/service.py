"""
RAG Service

Main service orchestrating RAG operations:
- Document ingestion with chunking and embedding
- Semantic search
- Collection management
"""

import hashlib
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime, timezone

from src.rag.storage import RAGStorage
from src.rag.processor import DocumentProcessor
from src.rag.embeddings import EmbeddingManager
from src.rag.chromadb_client import ChromaDBClient
from src.rag.models import Collection, Document


class RAGService:
    """Main RAG service."""

    def __init__(self, storage_path: str):
        """Initialize RAG service."""
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Initialize components
        db_path = self.storage_path / "rag.db"
        chroma_path = self.storage_path / "chromadb"

        self.storage = RAGStorage(str(db_path))
        self.processor = DocumentProcessor()
        self.embedding_manager = EmbeddingManager()
        self.chromadb = ChromaDBClient(str(chroma_path))

        self.is_initialized = False

    async def initialize(self):
        """Initialize service components."""
        if self.is_initialized:
            return

        await self.chromadb.initialize()
        await self.embedding_manager.initialize()

        self.is_initialized = True

    async def create_collection(
        self,
        name: str,
        description: str = "",
        chunk_size: int = 1024,
        chunk_overlap: int = 128
    ) -> str:
        """
        Create new collection.

        Returns:
            str: Collection ID
        """
        collection = Collection(
            name=name,
            description=description,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )

        # Save to metadata storage
        self.storage.save_collection(collection)

        # Create ChromaDB collection
        await self.chromadb.create_collection(
            collection.id,
            embedding_dim=self.embedding_manager.embedding_dim
        )

        return collection.id

    async def ingest_document(
        self,
        file_path: str,
        collection_id: str
    ) -> Dict[str, Any]:
        """
        Ingest document into collection.

        Args:
            file_path: Path to document
            collection_id: Target collection ID

        Returns:
            Dict with status, document_id, chunks_created
        """
        try:
            # Get collection config
            collection = self.storage.get_collection(collection_id)
            if not collection:
                raise ValueError(f"Collection not found: {collection_id}")

            # Compute file hash
            file_path_obj = Path(file_path)
            file_hash = self._compute_file_hash(file_path)

            # Determine file type
            file_type = self._detect_file_type(file_path)

            # Create document record
            document = Document(
                collection_id=collection_id,
                source_path=str(file_path_obj),
                file_type=file_type,
                file_hash=file_hash,
                file_size=file_path_obj.stat().st_size,
                status="processing"
            )
            self.storage.save_document(document)

            # Process file into chunks
            self.processor.chunk_size = collection.chunk_size
            self.processor.chunk_overlap = collection.chunk_overlap

            chunks = self.processor.process_file(file_path, file_type)

            # Set document_id on chunks
            for chunk in chunks:
                chunk.document_id = document.id

            # Generate embeddings
            chunk_texts = [chunk.content for chunk in chunks]
            embeddings = await self.embedding_manager.embed_batch(chunk_texts)

            # Store in ChromaDB
            await self.chromadb.add_chunks(collection_id, chunks, embeddings)

            # Save chunks to metadata storage
            for chunk in chunks:
                self.storage.save_chunk(chunk)

            # Update document status
            document.status = "indexed"
            document.chunk_count = len(chunks)
            document.indexed_at = datetime.now(timezone.utc)
            document.last_updated = datetime.now(timezone.utc)
            self.storage.save_document(document)

            return {
                "status": "success",
                "document_id": document.id,
                "chunks_created": len(chunks)
            }

        except Exception as e:
            # Update document status to failed
            if 'document' in locals():
                document.status = "failed"
                document.error = str(e)
                self.storage.save_document(document)

            return {
                "status": "error",
                "error": str(e)
            }

    async def query(
        self,
        query: str,
        collection_id: str,
        top_k: int = 5,
        min_similarity: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Query collection for similar chunks.

        Args:
            query: Query text
            collection_id: Collection to search
            top_k: Number of results to return
            min_similarity: Minimum similarity threshold

        Returns:
            List of dicts with 'content', 'similarity', 'metadata'
        """
        # Generate query embedding
        query_embedding = await self.embedding_manager.embed(query)

        # Query ChromaDB
        results = await self.chromadb.query(
            collection_id,
            query_embedding,
            top_k=top_k,
            min_similarity=min_similarity
        )

        # Format results
        output = []
        for result in results:
            chunk = result["chunk"]
            output.append({
                "chunk_id": chunk.id,
                "content": chunk.content,
                "similarity": result["similarity"],
                "metadata": chunk.metadata
            })

        return output

    async def delete_document(
        self,
        document_id: str,
        collection_id: str
    ):
        """Delete document and all its chunks."""
        # Delete from ChromaDB
        await self.chromadb.delete_chunks_by_document(collection_id, document_id)

        # Delete from metadata storage (chunks cascade)
        doc = self.storage.get_document(document_id)
        if doc:
            # Delete chunks first
            chunks = self.storage.get_document_chunks(document_id)
            # Note: SQLite cascade should handle this, but explicit is safer

            # Delete document
            with self.storage.db_path.parent.joinpath(self.storage.db_path).open() as conn:
                import sqlite3
                cursor = sqlite3.connect(str(self.storage.db_path)).cursor()
                cursor.execute("DELETE FROM rag_documents WHERE id = ?", (document_id,))
                cursor.connection.commit()

    async def get_collection_stats(self, collection_id: str) -> Dict[str, Any]:
        """Get collection statistics."""
        # Get documents
        import sqlite3
        with sqlite3.connect(str(self.storage.db_path)) as conn:
            cursor = conn.cursor()

            # Count documents
            cursor.execute(
                "SELECT COUNT(*) FROM rag_documents WHERE collection_id = ?",
                (collection_id,)
            )
            doc_count = cursor.fetchone()[0]

            # Count chunks
            cursor.execute(
                "SELECT SUM(chunk_count) FROM rag_documents WHERE collection_id = ?",
                (collection_id,)
            )
            chunk_count = cursor.fetchone()[0] or 0

        return {
            "document_count": doc_count,
            "chunk_count": chunk_count
        }

    def _compute_file_hash(self, file_path: str) -> str:
        """Compute SHA256 hash of file."""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def _detect_file_type(self, file_path: str) -> str:
        """Detect file type from extension."""
        ext = Path(file_path).suffix.lower()

        type_map = {
            ".md": "markdown",
            ".markdown": "markdown",
            ".txt": "text",
        }

        return type_map.get(ext, "text")
