# src/rag/dimension_validator.py
"""
Embedding Dimension Validator

Validates embedding dimensions before writes to ChromaDB to prevent
corruption from embedding model changes.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.rag.chromadb_client import ChromaDBClient


# Expected dimensions for known embedding models
EXPECTED_DIMENSIONS = {
    "all-MiniLM-L6-v2": 384,
    "text-embedding-ada-002": 1536,
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
}


class DimensionMismatchError(ValueError):
    """Raised when embedding dimensions don't match expected values."""

    def __init__(self, message: str, expected: int, actual: int):
        super().__init__(message)
        self.expected = expected
        self.actual = actual


class DimensionValidator:
    """Validates embedding dimensions before ChromaDB writes.

    Prevents corruption by catching dimension mismatches that occur when:
    - Embedding model changes between indexing sessions
    - Mixed embedding models used on same collection
    - Incorrect embedding configuration
    """

    async def validate_before_write(
        self,
        collection_id: str,
        embeddings: list[list[float]],
        chromadb_client: "ChromaDBClient",
        model_name: str = "all-MiniLM-L6-v2",
    ) -> None:
        """Validate embeddings before writing to collection.

        Args:
            collection_id: Target collection ID.
            embeddings: List of embedding vectors to validate.
            chromadb_client: ChromaDB client for collection queries.
            model_name: Name of embedding model used.

        Raises:
            ValueError: If embeddings list is empty.
            DimensionMismatchError: If dimensions don't match expected/existing.
        """
        # Check embeddings not empty
        if not embeddings:
            raise ValueError("Embeddings list cannot be empty")

        # Get dimension of first embedding
        actual_dim = len(embeddings[0])

        # Verify all embeddings have same dimension
        for i, emb in enumerate(embeddings):
            if len(emb) != actual_dim:
                raise DimensionMismatchError(
                    f"Inconsistent embedding dimensions: index 0 has {actual_dim}, "
                    f"index {i} has {len(emb)}",
                    expected=actual_dim,
                    actual=len(emb),
                )

        # Check against expected dimension for known models
        if model_name in EXPECTED_DIMENSIONS:
            expected_dim = EXPECTED_DIMENSIONS[model_name]
            if actual_dim != expected_dim:
                raise DimensionMismatchError(
                    f"Embedding dimension mismatch for model '{model_name}': "
                    f"expected {expected_dim}, got {actual_dim}",
                    expected=expected_dim,
                    actual=actual_dim,
                )

        # Check against existing collection dimension
        existing_dim = await self.get_collection_dimension(
            chromadb_client, collection_id
        )
        if existing_dim is not None and actual_dim != existing_dim:
            raise DimensionMismatchError(
                f"Embedding dimension mismatch with existing collection "
                f"'{collection_id}': collection has {existing_dim}, "
                f"new embeddings have {actual_dim}. "
                f"This may indicate an embedding model change.",
                expected=existing_dim,
                actual=actual_dim,
            )

    async def get_collection_dimension(
        self,
        chromadb_client: "ChromaDBClient",
        collection_id: str,
    ) -> int | None:
        """Get the embedding dimension stored in collection metadata.

        Args:
            chromadb_client: ChromaDB client instance.
            collection_id: Collection to query.

        Returns:
            Embedding dimension if collection exists, None otherwise.
        """
        if not chromadb_client.client:
            await chromadb_client.initialize()

        try:
            collection = chromadb_client.client.get_collection(collection_id)
            if collection and collection.metadata:
                return collection.metadata.get("embedding_dim")
        except (ValueError, Exception):
            # Collection doesn't exist
            pass

        return None


def validate_embeddings(
    embeddings: list[list[float]],
    model_name: str | None = None,
) -> int:
    """Synchronous utility to validate embedding consistency.

    Args:
        embeddings: List of embedding vectors.
        model_name: Optional model name for expected dimension check.

    Returns:
        The dimension of the embeddings.

    Raises:
        ValueError: If embeddings is empty.
        DimensionMismatchError: If dimensions are inconsistent.
    """
    if not embeddings:
        raise ValueError("Embeddings list cannot be empty")

    dim = len(embeddings[0])

    # Check all have same dimension
    for i, emb in enumerate(embeddings):
        if len(emb) != dim:
            raise DimensionMismatchError(
                f"Inconsistent dimensions: index 0 has {dim}, index {i} has {len(emb)}",
                expected=dim,
                actual=len(emb),
            )

    # Check against expected for known models
    if model_name and model_name in EXPECTED_DIMENSIONS:
        expected = EXPECTED_DIMENSIONS[model_name]
        if dim != expected:
            raise DimensionMismatchError(
                f"Dimension mismatch for model '{model_name}': "
                f"expected {expected}, got {dim}",
                expected=expected,
                actual=dim,
            )

    return dim
