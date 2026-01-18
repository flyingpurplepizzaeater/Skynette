# tests/unit/test_dimension_validator.py
"""Tests for embedding dimension validation."""

import pytest
from unittest.mock import MagicMock, AsyncMock

from src.rag.dimension_validator import (
    DimensionValidator,
    DimensionMismatchError,
    EXPECTED_DIMENSIONS,
    validate_embeddings,
)


class TestValidateEmbeddings:
    """Tests for the synchronous validate_embeddings function."""

    def test_empty_embeddings_raises_error(self):
        """Empty embeddings list should raise ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_embeddings([])

    def test_consistent_dimensions_pass(self):
        """Embeddings with consistent dimensions should pass."""
        embeddings = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6], [0.7, 0.8, 0.9]]
        dim = validate_embeddings(embeddings)
        assert dim == 3

    def test_inconsistent_dimensions_raises_error(self):
        """Embeddings with inconsistent dimensions should raise error."""
        embeddings = [[0.1, 0.2, 0.3], [0.4, 0.5]]  # Different lengths
        with pytest.raises(DimensionMismatchError) as exc_info:
            validate_embeddings(embeddings)
        assert exc_info.value.expected == 3
        assert exc_info.value.actual == 2

    def test_known_model_correct_dimension(self):
        """Known model with correct dimension should pass."""
        # all-MiniLM-L6-v2 expects 384 dimensions
        embeddings = [[0.1] * 384]
        dim = validate_embeddings(embeddings, model_name="all-MiniLM-L6-v2")
        assert dim == 384

    def test_known_model_wrong_dimension_raises_error(self):
        """Known model with wrong dimension should raise error."""
        # all-MiniLM-L6-v2 expects 384, not 512
        embeddings = [[0.1] * 512]
        with pytest.raises(DimensionMismatchError) as exc_info:
            validate_embeddings(embeddings, model_name="all-MiniLM-L6-v2")
        assert exc_info.value.expected == 384
        assert exc_info.value.actual == 512
        assert "all-MiniLM-L6-v2" in str(exc_info.value)

    def test_unknown_model_allows_any_dimension(self):
        """Unknown model should allow any dimension."""
        embeddings = [[0.1] * 256]
        dim = validate_embeddings(embeddings, model_name="custom-model")
        assert dim == 256


class TestDimensionValidator:
    """Tests for the DimensionValidator class."""

    @pytest.fixture
    def validator(self):
        """Create a DimensionValidator instance."""
        return DimensionValidator()

    @pytest.fixture
    def mock_chromadb(self):
        """Create a mock ChromaDB client."""
        client = MagicMock()
        client.client = MagicMock()
        return client

    @pytest.mark.asyncio
    async def test_validate_empty_embeddings(self, validator, mock_chromadb):
        """Empty embeddings should raise ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            await validator.validate_before_write(
                "test-collection", [], mock_chromadb, "all-MiniLM-L6-v2"
            )

    @pytest.mark.asyncio
    async def test_validate_inconsistent_dimensions(self, validator, mock_chromadb):
        """Inconsistent dimensions should raise DimensionMismatchError."""
        embeddings = [[0.1] * 384, [0.2] * 256]  # Different dimensions
        mock_chromadb.client.get_collection.side_effect = ValueError("Not found")

        with pytest.raises(DimensionMismatchError) as exc_info:
            await validator.validate_before_write(
                "test-collection", embeddings, mock_chromadb, "all-MiniLM-L6-v2"
            )
        assert "index 0 has 384" in str(exc_info.value)
        assert "index 1 has 256" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_validate_model_dimension_mismatch(self, validator, mock_chromadb):
        """Wrong dimension for known model should raise error."""
        embeddings = [[0.1] * 512]  # Wrong for all-MiniLM-L6-v2
        mock_chromadb.client.get_collection.side_effect = ValueError("Not found")

        with pytest.raises(DimensionMismatchError) as exc_info:
            await validator.validate_before_write(
                "test-collection", embeddings, mock_chromadb, "all-MiniLM-L6-v2"
            )
        assert "expected 384" in str(exc_info.value)
        assert "got 512" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_validate_collection_dimension_mismatch(self, validator, mock_chromadb):
        """Dimension mismatch with existing collection should raise error."""
        embeddings = [[0.1] * 384]

        # Mock existing collection with different dimension
        mock_collection = MagicMock()
        mock_collection.metadata = {"embedding_dim": 768, "model_name": "other-model"}
        mock_chromadb.client.get_collection.return_value = mock_collection

        with pytest.raises(DimensionMismatchError) as exc_info:
            await validator.validate_before_write(
                "test-collection", embeddings, mock_chromadb, "all-MiniLM-L6-v2"
            )
        assert "collection has 768" in str(exc_info.value)
        assert "new embeddings have 384" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_validate_passes_for_correct_dimensions(self, validator, mock_chromadb):
        """Correct dimensions should pass validation."""
        embeddings = [[0.1] * 384, [0.2] * 384]

        # Mock existing collection with matching dimension
        mock_collection = MagicMock()
        mock_collection.metadata = {"embedding_dim": 384, "model_name": "all-MiniLM-L6-v2"}
        mock_chromadb.client.get_collection.return_value = mock_collection

        # Should not raise
        await validator.validate_before_write(
            "test-collection", embeddings, mock_chromadb, "all-MiniLM-L6-v2"
        )

    @pytest.mark.asyncio
    async def test_validate_new_collection_passes(self, validator, mock_chromadb):
        """New collection (not existing) should pass if model dimension correct."""
        embeddings = [[0.1] * 384]
        mock_chromadb.client.get_collection.side_effect = ValueError("Not found")

        # Should not raise
        await validator.validate_before_write(
            "new-collection", embeddings, mock_chromadb, "all-MiniLM-L6-v2"
        )


class TestGetCollectionDimension:
    """Tests for get_collection_dimension method."""

    @pytest.fixture
    def validator(self):
        return DimensionValidator()

    @pytest.mark.asyncio
    async def test_returns_dimension_for_existing_collection(self, validator):
        """Should return dimension from collection metadata."""
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_collection.metadata = {"embedding_dim": 384}
        mock_client.client = MagicMock()
        mock_client.client.get_collection.return_value = mock_collection

        dim = await validator.get_collection_dimension(mock_client, "test-collection")
        assert dim == 384

    @pytest.mark.asyncio
    async def test_returns_none_for_missing_collection(self, validator):
        """Should return None if collection doesn't exist."""
        mock_client = MagicMock()
        mock_client.client = MagicMock()
        mock_client.client.get_collection.side_effect = ValueError("Not found")

        dim = await validator.get_collection_dimension(mock_client, "missing")
        assert dim is None

    @pytest.mark.asyncio
    async def test_initializes_client_if_needed(self, validator):
        """Should initialize client if not already initialized."""
        mock_client = MagicMock()
        mock_client.client = None
        mock_client.initialize = AsyncMock()

        # After initialize, client should be set
        async def set_client():
            mock_client.client = MagicMock()
            mock_client.client.get_collection.side_effect = ValueError("Not found")

        mock_client.initialize.side_effect = set_client

        dim = await validator.get_collection_dimension(mock_client, "test")
        mock_client.initialize.assert_called_once()
        assert dim is None


class TestExpectedDimensions:
    """Tests for EXPECTED_DIMENSIONS constant."""

    def test_contains_common_models(self):
        """Should contain common embedding models."""
        assert "all-MiniLM-L6-v2" in EXPECTED_DIMENSIONS
        assert "text-embedding-ada-002" in EXPECTED_DIMENSIONS
        assert "text-embedding-3-small" in EXPECTED_DIMENSIONS

    def test_dimensions_are_positive(self):
        """All dimensions should be positive integers."""
        for model, dim in EXPECTED_DIMENSIONS.items():
            assert isinstance(dim, int)
            assert dim > 0
