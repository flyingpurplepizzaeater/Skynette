# src/rag/chromadb_client.py
"""
ChromaDB Client

Wrapper for ChromaDB vector database operations.
Uses in-memory implementation for MVP testing.
"""

import numpy as np
from typing import List, Dict, Any
from pathlib import Path

from src.rag.models import Chunk


class InMemoryVectorStore:
    """In-memory vector store for testing."""

    def __init__(self, name: str, metadata: Dict[str, Any]):
        self.name = name
        self.metadata = metadata
        self.vectors = {}  # id -> embedding
        self.documents = {}  # id -> document text
        self.metadatas = {}  # id -> metadata

    def add(self, ids: List[str], embeddings: List[List[float]],
            documents: List[str], metadatas: List[Dict[str, Any]]):
        """Add vectors to store."""
        for i, id_ in enumerate(ids):
            self.vectors[id_] = np.array(embeddings[i])
            self.documents[id_] = documents[i]
            self.metadatas[id_] = metadatas[i]

    def query(self, query_embeddings: List[List[float]], n_results: int):
        """Query for similar vectors using cosine similarity."""
        if not self.vectors:
            return {'ids': [[]], 'distances': [[]], 'documents': [[]], 'metadatas': [[]]}

        query_vec = np.array(query_embeddings[0])

        # Calculate cosine similarities
        similarities = []
        for id_, vec in self.vectors.items():
            # Cosine similarity = dot product of normalized vectors
            query_norm = np.linalg.norm(query_vec)
            vec_norm = np.linalg.norm(vec)

            if query_norm == 0 or vec_norm == 0:
                # Handle zero vectors
                similarity = 0.0
            else:
                similarity = np.dot(query_vec, vec) / (query_norm * vec_norm)

            # Convert to distance (lower is better for ChromaDB API compatibility)
            distance = 1 - similarity
            similarities.append((id_, distance))

        # Sort by distance (ascending)
        similarities.sort(key=lambda x: x[1])

        # Take top_k
        top_results = similarities[:n_results]

        ids = [id_ for id_, _ in top_results]
        distances = [dist for _, dist in top_results]
        documents = [self.documents[id_] for id_ in ids]
        metadatas = [self.metadatas[id_] for id_ in ids]

        return {
            'ids': [ids],
            'distances': [distances],
            'documents': [documents],
            'metadatas': [metadatas]
        }

    def get(self, where: Dict[str, Any]):
        """Get items matching metadata filter."""
        matching_ids = []
        for id_, metadata in self.metadatas.items():
            # Simple equality check
            match = all(metadata.get(k) == v for k, v in where.items())
            if match:
                matching_ids.append(id_)

        return {'ids': matching_ids}

    def delete(self, ids: List[str]):
        """Delete items by ID."""
        for id_ in ids:
            self.vectors.pop(id_, None)
            self.documents.pop(id_, None)
            self.metadatas.pop(id_, None)

    def count(self) -> int:
        """Count items in collection."""
        return len(self.vectors)


class InMemoryClient:
    """In-memory ChromaDB-like client for testing."""

    def __init__(self):
        self.collections = {}

    def get_or_create_collection(self, name: str, metadata: Dict[str, Any] = None):
        """Get or create collection."""
        if name not in self.collections:
            self.collections[name] = InMemoryVectorStore(name, metadata or {})
        return self.collections[name]

    def get_collection(self, name: str):
        """Get existing collection."""
        if name not in self.collections:
            raise ValueError(f"Collection {name} does not exist")
        return self.collections[name]

    def delete_collection(self, name: str):
        """Delete collection."""
        self.collections.pop(name, None)


class ChromaDBClient:
    """ChromaDB client for vector storage."""

    def __init__(self, storage_path: str):
        """Initialize ChromaDB client."""
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.client = None
        self.collections = {}  # Cache of collection objects

    async def initialize(self):
        """Initialize ChromaDB client."""
        if self.client:
            return

        # Use in-memory implementation for MVP/testing
        # In production, this would use actual ChromaDB client
        self.client = InMemoryClient()

    async def create_collection(
        self,
        collection_id: str,
        embedding_dim: int = 384
    ):
        """Create new collection."""
        if not self.client:
            await self.initialize()

        # Create or get collection
        collection = self.client.get_or_create_collection(
            name=collection_id,
            metadata={"embedding_dim": embedding_dim}
        )

        self.collections[collection_id] = collection

    async def collection_exists(self, collection_id: str) -> bool:
        """Check if collection exists."""
        if not self.client:
            await self.initialize()

        try:
            self.client.get_collection(collection_id)
            return True
        except Exception:
            return False

    async def delete_collection(self, collection_id: str):
        """Delete collection."""
        if not self.client:
            await self.initialize()

        self.client.delete_collection(collection_id)

        if collection_id in self.collections:
            del self.collections[collection_id]

    async def add_chunks(
        self,
        collection_id: str,
        chunks: List[Chunk],
        embeddings: List[List[float]]
    ):
        """Add chunks with embeddings to collection."""
        if collection_id not in self.collections:
            collection = self.client.get_collection(collection_id)
            self.collections[collection_id] = collection
        else:
            collection = self.collections[collection_id]

        # Prepare data
        ids = [chunk.id for chunk in chunks]
        documents = [chunk.content for chunk in chunks]
        metadatas = [
            {
                "document_id": chunk.document_id,
                "chunk_index": chunk.chunk_index,
                **chunk.metadata
            }
            for chunk in chunks
        ]

        # Add to collection
        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )

    async def query(
        self,
        collection_id: str,
        query_embedding: List[float],
        top_k: int = 5,
        min_similarity: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Query for similar chunks.

        Returns:
            List of dicts with 'chunk' (Chunk object) and 'similarity' (float)
        """
        if collection_id not in self.collections:
            collection = self.client.get_collection(collection_id)
            self.collections[collection_id] = collection
        else:
            collection = self.collections[collection_id]

        # Query collection
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )

        # Parse results
        output = []
        if results and results['ids'] and results['ids'][0]:
            for i, chunk_id in enumerate(results['ids'][0]):
                # Calculate similarity from distance
                distance = results['distances'][0][i]
                similarity = 1 - distance  # Distance is already 1-cosine_sim

                # Filter by min_similarity
                if similarity < min_similarity:
                    continue

                # Reconstruct chunk
                chunk = Chunk(
                    id=chunk_id,
                    document_id=results['metadatas'][0][i]['document_id'],
                    chunk_index=results['metadatas'][0][i]['chunk_index'],
                    content=results['documents'][0][i],
                    metadata=results['metadatas'][0][i]
                )

                output.append({
                    "chunk": chunk,
                    "similarity": similarity
                })

        return output

    async def get_count(self, collection_id: str) -> int:
        """Get number of chunks in collection."""
        if collection_id not in self.collections:
            collection = self.client.get_collection(collection_id)
            self.collections[collection_id] = collection
        else:
            collection = self.collections[collection_id]

        return collection.count()

    async def delete_chunks_by_document(
        self,
        collection_id: str,
        document_id: str
    ):
        """Delete all chunks for a document."""
        if collection_id not in self.collections:
            collection = self.client.get_collection(collection_id)
            self.collections[collection_id] = collection
        else:
            collection = self.collections[collection_id]

        # Query for all chunks from this document
        results = collection.get(
            where={"document_id": document_id}
        )

        if results and results['ids']:
            # Delete by IDs
            collection.delete(ids=results['ids'])
