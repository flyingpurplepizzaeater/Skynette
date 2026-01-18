"""
Integration tests for RAG context retrieval.

Tests the project-level RAG system including:
- Project indexing
- Context retrieval
- RAG context provider integration
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from src.rag.project_indexer import ProjectIndexer, SUPPORTED_EXTENSIONS
from src.rag.dimension_validator import (
    DimensionValidator,
    DimensionMismatchError,
    validate_embeddings,
    EXPECTED_DIMENSIONS,
)


class TestProjectIndexing:
    """Tests for project file indexing."""

    @pytest.fixture
    def mock_chromadb(self):
        """Create mock ChromaDB client."""
        client = MagicMock()
        client.create_collection = AsyncMock()
        client.collection_exists = AsyncMock(return_value=True)
        client.add_chunks = AsyncMock()
        client.delete_chunks_by_document = AsyncMock()
        client.query = AsyncMock(return_value=[])
        return client

    @pytest.fixture
    def mock_embedding_manager(self):
        """Create mock embedding manager."""
        manager = MagicMock()
        manager.embedding_dim = 384
        manager.model_name = "all-MiniLM-L6-v2"
        manager.embed = AsyncMock(return_value=[0.1] * 384)
        manager.embed_batch = AsyncMock(return_value=[[0.1] * 384])
        return manager

    @pytest.mark.asyncio
    async def test_project_indexing_basic(self, mock_chromadb, mock_embedding_manager, tmp_path):
        """Can index a project with Python files."""
        # Create test files
        (tmp_path / "main.py").write_text("def main():\n    print('Hello')")
        (tmp_path / "utils.py").write_text("def helper():\n    return 42")

        indexer = ProjectIndexer(mock_chromadb, mock_embedding_manager)
        stats = await indexer.index_project(str(tmp_path))

        assert stats["indexed"] >= 2  # main.py and utils.py
        assert stats["errors"] == 0

    @pytest.mark.asyncio
    async def test_project_skips_hidden_files(self, mock_chromadb, mock_embedding_manager, tmp_path):
        """Hidden files and directories are skipped."""
        # Create hidden file
        (tmp_path / ".hidden.py").write_text("secret code")

        # Create hidden directory
        hidden_dir = tmp_path / ".git"
        hidden_dir.mkdir()
        (hidden_dir / "config").write_text("git config")

        # Create visible file
        (tmp_path / "visible.py").write_text("print('visible')")

        indexer = ProjectIndexer(mock_chromadb, mock_embedding_manager)
        stats = await indexer.index_project(str(tmp_path))

        assert stats["indexed"] == 1  # Only visible file

    @pytest.mark.asyncio
    async def test_project_skips_unsupported_files(self, mock_chromadb, mock_embedding_manager, tmp_path):
        """Files with unsupported extensions are skipped."""
        # Create unsupported file
        (tmp_path / "image.png").write_bytes(b"\x89PNG")
        (tmp_path / "data.xlsx").write_bytes(b"excel data")

        # Create supported file
        (tmp_path / "script.py").write_text("print(1)")

        indexer = ProjectIndexer(mock_chromadb, mock_embedding_manager)
        stats = await indexer.index_project(str(tmp_path))

        assert stats["indexed"] == 1  # Only py file

    @pytest.mark.asyncio
    async def test_incremental_indexing(self, mock_chromadb, mock_embedding_manager, tmp_path):
        """Unchanged files are skipped on re-index."""
        (tmp_path / "script.py").write_text("def main(): pass")

        indexer = ProjectIndexer(mock_chromadb, mock_embedding_manager)

        # First index
        stats1 = await indexer.index_project(str(tmp_path))
        assert stats1["indexed"] == 1

        # Second index without changes
        stats2 = await indexer.index_project(str(tmp_path))
        assert stats2["indexed"] == 0
        assert stats2["skipped"] == 1


class TestRagContextQuery:
    """Tests for RAG context querying."""

    @pytest.fixture
    def mock_chromadb(self):
        """Create mock ChromaDB client."""
        client = MagicMock()
        client.collection_exists = AsyncMock(return_value=True)
        return client

    @pytest.fixture
    def mock_embedding_manager(self):
        """Create mock embedding manager."""
        manager = MagicMock()
        manager.embedding_dim = 384
        manager.model_name = "all-MiniLM-L6-v2"
        manager.embed = AsyncMock(return_value=[0.1] * 384)
        return manager

    @pytest.mark.asyncio
    async def test_query_returns_empty_for_missing_collection(self, mock_chromadb, mock_embedding_manager, tmp_path):
        """Query returns empty list if collection doesn't exist."""
        mock_chromadb.collection_exists = AsyncMock(return_value=False)

        indexer = ProjectIndexer(mock_chromadb, mock_embedding_manager)
        results = await indexer.query_context("test query", str(tmp_path))

        assert results == []

    @pytest.mark.asyncio
    async def test_query_generates_embedding(self, mock_chromadb, mock_embedding_manager, tmp_path):
        """Query generates embedding for search."""
        mock_chromadb.query = AsyncMock(return_value=[])

        indexer = ProjectIndexer(mock_chromadb, mock_embedding_manager)
        await indexer.query_context("find the main function", str(tmp_path))

        mock_embedding_manager.embed.assert_called_once_with("find the main function")


class TestDimensionValidator:
    """Tests for embedding dimension validation."""

    def test_validate_consistent_embeddings(self):
        """Embeddings with consistent dimensions pass validation."""
        embeddings = [[0.1] * 384, [0.2] * 384, [0.3] * 384]

        dim = validate_embeddings(embeddings)

        assert dim == 384

    def test_validate_inconsistent_embeddings_fails(self):
        """Embeddings with inconsistent dimensions fail validation."""
        embeddings = [[0.1] * 384, [0.2] * 256]  # Different dimensions

        with pytest.raises(DimensionMismatchError):
            validate_embeddings(embeddings)

    def test_validate_empty_embeddings_fails(self):
        """Empty embeddings list fails validation."""
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_embeddings([])

    def test_validate_known_model_wrong_dimension(self):
        """Known model with wrong dimension fails."""
        # all-MiniLM-L6-v2 expects 384 dimensions
        embeddings = [[0.1] * 256]

        with pytest.raises(DimensionMismatchError):
            validate_embeddings(embeddings, model_name="all-MiniLM-L6-v2")

    def test_expected_dimensions_contains_known_models(self):
        """EXPECTED_DIMENSIONS contains common models."""
        assert "all-MiniLM-L6-v2" in EXPECTED_DIMENSIONS
        assert EXPECTED_DIMENSIONS["all-MiniLM-L6-v2"] == 384

        assert "text-embedding-ada-002" in EXPECTED_DIMENSIONS
        assert EXPECTED_DIMENSIONS["text-embedding-ada-002"] == 1536


class TestDimensionValidatorAsync:
    """Async tests for DimensionValidator class."""

    @pytest.mark.asyncio
    async def test_validate_before_write_valid(self):
        """Valid embeddings pass async validation."""
        mock_chromadb = MagicMock()
        mock_chromadb.client = MagicMock()
        mock_chromadb.client.get_collection.return_value = None

        validator = DimensionValidator()
        embeddings = [[0.1] * 384]

        # Should not raise
        await validator.validate_before_write(
            "test-collection",
            embeddings,
            mock_chromadb,
            model_name="all-MiniLM-L6-v2",
        )

    @pytest.mark.asyncio
    async def test_validate_before_write_wrong_dimension(self):
        """Wrong dimension fails async validation."""
        mock_chromadb = MagicMock()
        mock_chromadb.client = MagicMock()
        mock_chromadb.client.get_collection.return_value = None

        validator = DimensionValidator()
        embeddings = [[0.1] * 256]  # Wrong dimension for model

        with pytest.raises(DimensionMismatchError):
            await validator.validate_before_write(
                "test-collection",
                embeddings,
                mock_chromadb,
                model_name="all-MiniLM-L6-v2",
            )

    @pytest.mark.asyncio
    async def test_validate_against_existing_collection(self):
        """Validation checks against existing collection dimension."""
        mock_collection = MagicMock()
        mock_collection.metadata = {"embedding_dim": 384}

        mock_chromadb = MagicMock()
        mock_chromadb.client = MagicMock()
        mock_chromadb.client.get_collection.return_value = mock_collection

        validator = DimensionValidator()

        # Try to add embeddings with different dimension
        embeddings = [[0.1] * 256]

        with pytest.raises(DimensionMismatchError) as exc_info:
            await validator.validate_before_write(
                "existing-collection",
                embeddings,
                mock_chromadb,
                model_name="custom-model",  # Unknown model, so dimension check is vs collection
            )

        assert exc_info.value.expected == 384
        assert exc_info.value.actual == 256


class TestSupportedExtensions:
    """Tests for supported file extensions."""

    def test_python_supported(self):
        """Python files are supported."""
        assert ".py" in SUPPORTED_EXTENSIONS

    def test_javascript_supported(self):
        """JavaScript files are supported."""
        assert ".js" in SUPPORTED_EXTENSIONS
        assert ".ts" in SUPPORTED_EXTENSIONS
        assert ".jsx" in SUPPORTED_EXTENSIONS
        assert ".tsx" in SUPPORTED_EXTENSIONS

    def test_config_files_supported(self):
        """Configuration files are supported."""
        assert ".json" in SUPPORTED_EXTENSIONS
        assert ".yaml" in SUPPORTED_EXTENSIONS
        assert ".yml" in SUPPORTED_EXTENSIONS

    def test_web_files_supported(self):
        """Web files are supported."""
        assert ".html" in SUPPORTED_EXTENSIONS
        assert ".css" in SUPPORTED_EXTENSIONS
        assert ".scss" in SUPPORTED_EXTENSIONS


class TestRAGContextProvider:
    """Tests for RAGContextProvider integration."""

    @pytest.fixture
    def mock_chromadb(self):
        """Create mock ChromaDB client."""
        client = MagicMock()
        client.create_collection = AsyncMock()
        client.collection_exists = AsyncMock(return_value=True)
        client.add_chunks = AsyncMock()
        client.delete_chunks_by_document = AsyncMock()
        client.query = AsyncMock(return_value=[])
        return client

    @pytest.fixture
    def mock_embedding_manager(self):
        """Create mock embedding manager."""
        manager = MagicMock()
        manager.embedding_dim = 384
        manager.model_name = "all-MiniLM-L6-v2"
        manager.embed = AsyncMock(return_value=[0.1] * 384)
        manager.embed_batch = AsyncMock(return_value=[[0.1] * 384])
        return manager

    @pytest.mark.asyncio
    async def test_rag_context_provider_imports(self):
        """RAGContextProvider can be imported."""
        from src.ui.views.code_editor.ai_panel.rag_context import RAGContextProvider

        assert RAGContextProvider is not None

    @pytest.mark.asyncio
    async def test_rag_context_provider_lazy_indexing(self, mock_chromadb, mock_embedding_manager, tmp_path):
        """RAGContextProvider uses lazy indexing."""
        from src.ui.views.code_editor.ai_panel.rag_context import RAGContextProvider

        # Create test file
        (tmp_path / "test.py").write_text("print('hello')")

        provider = RAGContextProvider(mock_chromadb, mock_embedding_manager)

        # Should not be indexed yet
        assert not provider.is_indexed(str(tmp_path))

        # Ensure indexed (triggers lazy indexing)
        await provider.ensure_indexed(str(tmp_path))

        # Now should be indexed
        assert provider.is_indexed(str(tmp_path))

    @pytest.mark.asyncio
    async def test_rag_context_provider_get_context(self, mock_chromadb, mock_embedding_manager, tmp_path):
        """RAGContextProvider returns formatted context."""
        from src.ui.views.code_editor.ai_panel.rag_context import RAGContextProvider
        from src.rag.models import Chunk

        # Create test file
        (tmp_path / "main.py").write_text("def main():\n    pass")

        # Mock query results
        mock_chunk = Chunk(
            document_id="doc-123",
            chunk_index=0,
            content="def main():\n    pass",
            metadata={"source_path": str(tmp_path / "main.py"), "language": "py"},
        )
        mock_chromadb.query = AsyncMock(return_value=[
            {"chunk": mock_chunk, "similarity": 0.85}
        ])

        provider = RAGContextProvider(mock_chromadb, mock_embedding_manager)
        context, sources = await provider.get_context("main function", str(tmp_path))

        assert "def main()" in context
        assert len(sources) == 1
        assert sources[0]["similarity"] == 0.85
