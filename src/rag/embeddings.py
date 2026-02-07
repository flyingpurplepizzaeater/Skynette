# src/rag/embeddings.py
"""
Embedding Manager

Manages embedding generation using local sentence-transformers model.
Sprint 1: Local model only (all-MiniLM-L6-v2).
"""

import asyncio

from sentence_transformers import SentenceTransformer


class EmbeddingManager:
    """Manage embedding generation."""

    def __init__(self, model: str = "all-MiniLM-L6-v2"):
        """Initialize embedding manager."""
        self.model_name = model
        self.model = None
        self.is_initialized = False
        self.embedding_dim = 384  # For all-MiniLM-L6-v2

    async def initialize(self):
        """Load embedding model."""
        if self.is_initialized:
            return

        # Load model in thread pool (blocking I/O)
        loop = asyncio.get_event_loop()
        self.model = await loop.run_in_executor(None, lambda: SentenceTransformer(self.model_name))

        self.is_initialized = True

    async def embed(self, text: str) -> list[float]:
        """
        Generate embedding for single text.

        Returns:
            List[float]: Embedding vector (384 dimensions for all-MiniLM-L6-v2)
        """
        if not self.is_initialized:
            await self.initialize()

        # Run in thread pool (CPU-bound)
        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(
            None, lambda: self.model.encode(text, normalize_embeddings=True)
        )

        return embedding.tolist()

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for multiple texts.

        More efficient than calling embed() multiple times.

        Args:
            texts: List of text strings

        Returns:
            List[List[float]]: List of embedding vectors
        """
        if not self.is_initialized:
            await self.initialize()

        # Run in thread pool
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            None,
            lambda: self.model.encode(texts, normalize_embeddings=True, show_progress_bar=False),
        )

        return [emb.tolist() for emb in embeddings]

    def shutdown(self):
        """Cleanup resources."""
        self.model = None
        self.is_initialized = False
