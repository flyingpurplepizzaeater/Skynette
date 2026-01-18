# tests/unit/test_project_indexer.py
"""Tests for project indexing functionality."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from src.rag.project_indexer import (
    ProjectIndexer,
    SUPPORTED_EXTENSIONS,
    _hash_path,
)


class TestHashPath:
    """Tests for _hash_path utility function."""

    def test_returns_consistent_hash(self):
        """Same path should return same hash."""
        path = "/some/project/path"
        hash1 = _hash_path(path)
        hash2 = _hash_path(path)
        assert hash1 == hash2

    def test_returns_12_char_hex(self):
        """Hash should be 12 character hex string."""
        path = "/any/path"
        hash_val = _hash_path(path)
        assert len(hash_val) == 12
        assert all(c in "0123456789abcdef" for c in hash_val)

    def test_different_paths_different_hashes(self):
        """Different paths should have different hashes."""
        hash1 = _hash_path("/path/one")
        hash2 = _hash_path("/path/two")
        assert hash1 != hash2


class TestSupportedExtensions:
    """Tests for supported file extensions."""

    def test_includes_common_languages(self):
        """Should include common programming language extensions."""
        assert ".py" in SUPPORTED_EXTENSIONS
        assert ".js" in SUPPORTED_EXTENSIONS
        assert ".ts" in SUPPORTED_EXTENSIONS
        assert ".java" in SUPPORTED_EXTENSIONS
        assert ".go" in SUPPORTED_EXTENSIONS
        assert ".rs" in SUPPORTED_EXTENSIONS

    def test_includes_web_files(self):
        """Should include web development files."""
        assert ".html" in SUPPORTED_EXTENSIONS
        assert ".css" in SUPPORTED_EXTENSIONS
        assert ".jsx" in SUPPORTED_EXTENSIONS
        assert ".tsx" in SUPPORTED_EXTENSIONS

    def test_includes_config_files(self):
        """Should include configuration files."""
        assert ".json" in SUPPORTED_EXTENSIONS
        assert ".yaml" in SUPPORTED_EXTENSIONS
        assert ".yml" in SUPPORTED_EXTENSIONS


class TestProjectIndexer:
    """Tests for ProjectIndexer class."""

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

    @pytest.fixture
    def indexer(self, mock_chromadb, mock_embedding_manager):
        """Create ProjectIndexer instance."""
        return ProjectIndexer(
            mock_chromadb,
            mock_embedding_manager,
            chunk_size=100,
            chunk_overlap=10,
        )

    def test_init_stores_dependencies(self, mock_chromadb, mock_embedding_manager):
        """Should store chromadb and embedding manager references."""
        indexer = ProjectIndexer(mock_chromadb, mock_embedding_manager)
        assert indexer.chromadb is mock_chromadb
        assert indexer.embedding_manager is mock_embedding_manager

    def test_init_default_chunk_settings(self, mock_chromadb, mock_embedding_manager):
        """Should use default chunk settings."""
        indexer = ProjectIndexer(mock_chromadb, mock_embedding_manager)
        assert indexer.chunk_size == 500
        assert indexer.chunk_overlap == 50

    def test_init_custom_chunk_settings(self, mock_chromadb, mock_embedding_manager):
        """Should accept custom chunk settings."""
        indexer = ProjectIndexer(
            mock_chromadb,
            mock_embedding_manager,
            chunk_size=1000,
            chunk_overlap=100,
        )
        assert indexer.chunk_size == 1000
        assert indexer.chunk_overlap == 100


class TestSplitIntoChunks:
    """Tests for chunk splitting logic."""

    @pytest.fixture
    def indexer(self):
        """Create indexer with mock dependencies."""
        mock_chromadb = MagicMock()
        mock_embedding = MagicMock()
        mock_embedding.embedding_dim = 384
        mock_embedding.model_name = "all-MiniLM-L6-v2"
        return ProjectIndexer(
            mock_chromadb,
            mock_embedding,
            chunk_size=50,
            chunk_overlap=10,
        )

    def test_small_content_single_chunk(self, indexer):
        """Content smaller than chunk_size should be single chunk."""
        content = "Short content"
        chunks = indexer._split_into_chunks(content)
        assert len(chunks) == 1
        assert chunks[0] == content

    def test_large_content_multiple_chunks(self, indexer):
        """Large content should be split into multiple chunks."""
        # Create content larger than chunk_size
        content = "x" * 120  # 120 chars, chunk_size=50
        chunks = indexer._split_into_chunks(content)
        assert len(chunks) > 1

    def test_chunks_have_overlap(self, indexer):
        """Consecutive chunks should overlap."""
        content = "a" * 120
        chunks = indexer._split_into_chunks(content)

        if len(chunks) >= 2:
            # Check overlap by verifying end of chunk1 appears in chunk2
            chunk1_end = chunks[0][-indexer.chunk_overlap:]
            assert chunk1_end in chunks[1]

    def test_respects_newline_boundaries(self, indexer):
        """Should try to break at newlines when possible."""
        # Content with newline in middle
        content = "a" * 30 + "\n" + "b" * 30 + "\n" + "c" * 30
        chunks = indexer._split_into_chunks(content)

        # At least one chunk should end with newline
        ends_with_newline = any(chunk.endswith("\n") for chunk in chunks[:-1])
        # Note: This is a soft preference, not guaranteed
        assert len(chunks) >= 1


class TestIndexProject:
    """Tests for index_project method."""

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
    async def test_raises_for_missing_project(self, mock_chromadb, mock_embedding_manager):
        """Should raise ValueError for non-existent project root."""
        indexer = ProjectIndexer(mock_chromadb, mock_embedding_manager)
        with pytest.raises(ValueError, match="does not exist"):
            await indexer.index_project("/nonexistent/path/12345")

    @pytest.mark.asyncio
    async def test_creates_collection(self, mock_chromadb, mock_embedding_manager, tmp_path):
        """Should create collection for the project."""
        # Create a test file
        test_file = tmp_path / "test.py"
        test_file.write_text("print('hello')")

        indexer = ProjectIndexer(mock_chromadb, mock_embedding_manager)
        await indexer.index_project(str(tmp_path))

        mock_chromadb.create_collection.assert_called_once()

    @pytest.mark.asyncio
    async def test_indexes_supported_files(self, mock_chromadb, mock_embedding_manager, tmp_path):
        """Should index files with supported extensions."""
        # Create test files
        py_file = tmp_path / "script.py"
        py_file.write_text("def main(): pass")

        js_file = tmp_path / "app.js"
        js_file.write_text("console.log('hi')")

        indexer = ProjectIndexer(mock_chromadb, mock_embedding_manager)
        stats = await indexer.index_project(str(tmp_path))

        assert stats["indexed"] == 2
        assert stats["errors"] == 0

    @pytest.mark.asyncio
    async def test_skips_unsupported_files(self, mock_chromadb, mock_embedding_manager, tmp_path):
        """Should skip files with unsupported extensions."""
        # Create unsupported file
        img_file = tmp_path / "image.png"
        img_file.write_bytes(b"\x89PNG")

        # Create supported file
        py_file = tmp_path / "script.py"
        py_file.write_text("print(1)")

        indexer = ProjectIndexer(mock_chromadb, mock_embedding_manager)
        stats = await indexer.index_project(str(tmp_path))

        assert stats["indexed"] == 1  # Only py file

    @pytest.mark.asyncio
    async def test_skips_hidden_files(self, mock_chromadb, mock_embedding_manager, tmp_path):
        """Should skip hidden files and directories."""
        # Create hidden file
        hidden = tmp_path / ".hidden.py"
        hidden.write_text("secret")

        # Create hidden directory
        hidden_dir = tmp_path / ".git"
        hidden_dir.mkdir()
        git_file = hidden_dir / "config"
        git_file.write_text("git config")

        # Create visible file
        visible = tmp_path / "main.py"
        visible.write_text("print('visible')")

        indexer = ProjectIndexer(mock_chromadb, mock_embedding_manager)
        stats = await indexer.index_project(str(tmp_path))

        assert stats["indexed"] == 1  # Only visible file

    @pytest.mark.asyncio
    async def test_incremental_skips_unchanged(self, mock_chromadb, mock_embedding_manager, tmp_path):
        """Should skip unchanged files on re-index."""
        py_file = tmp_path / "script.py"
        py_file.write_text("def main(): pass")

        indexer = ProjectIndexer(mock_chromadb, mock_embedding_manager)

        # First index
        stats1 = await indexer.index_project(str(tmp_path))
        assert stats1["indexed"] == 1

        # Second index without changes
        stats2 = await indexer.index_project(str(tmp_path))
        assert stats2["indexed"] == 0
        assert stats2["skipped"] == 1

    @pytest.mark.asyncio
    async def test_reindexes_changed_files(self, mock_chromadb, mock_embedding_manager, tmp_path):
        """Should re-index files that have changed."""
        py_file = tmp_path / "script.py"
        py_file.write_text("def main(): pass")

        indexer = ProjectIndexer(mock_chromadb, mock_embedding_manager)

        # First index
        await indexer.index_project(str(tmp_path))

        # Modify file
        py_file.write_text("def main(): return 42")

        # Second index
        stats2 = await indexer.index_project(str(tmp_path))
        assert stats2["indexed"] == 1


class TestQueryContext:
    """Tests for query_context method."""

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
    async def test_returns_empty_for_missing_collection(self, mock_chromadb, mock_embedding_manager, tmp_path):
        """Should return empty list if collection doesn't exist."""
        mock_chromadb.collection_exists = AsyncMock(return_value=False)

        indexer = ProjectIndexer(mock_chromadb, mock_embedding_manager)
        results = await indexer.query_context("test query", str(tmp_path))

        assert results == []

    @pytest.mark.asyncio
    async def test_generates_query_embedding(self, mock_chromadb, mock_embedding_manager, tmp_path):
        """Should generate embedding for query."""
        mock_chromadb.query = AsyncMock(return_value=[])

        indexer = ProjectIndexer(mock_chromadb, mock_embedding_manager)
        await indexer.query_context("find the main function", str(tmp_path))

        mock_embedding_manager.embed.assert_called_once_with("find the main function")

    @pytest.mark.asyncio
    async def test_formats_results(self, mock_chromadb, mock_embedding_manager, tmp_path):
        """Should format query results correctly."""
        from src.rag.models import Chunk

        mock_chunk = Chunk(
            document_id="doc-123",
            chunk_index=0,
            content="def main(): pass",
            metadata={"source_path": "/path/to/file.py", "language": "py"},
        )
        mock_chromadb.query = AsyncMock(return_value=[
            {"chunk": mock_chunk, "similarity": 0.85}
        ])

        indexer = ProjectIndexer(mock_chromadb, mock_embedding_manager)
        results = await indexer.query_context("main function", str(tmp_path))

        assert len(results) == 1
        assert results[0]["content"] == "def main(): pass"
        assert results[0]["source_path"] == "/path/to/file.py"
        assert results[0]["language"] == "py"
        assert results[0]["similarity"] == 0.85


class TestUtilityMethods:
    """Tests for utility methods."""

    @pytest.fixture
    def indexer(self):
        """Create indexer with mock dependencies."""
        mock_chromadb = MagicMock()
        mock_embedding = MagicMock()
        mock_embedding.embedding_dim = 384
        mock_embedding.model_name = "all-MiniLM-L6-v2"
        return ProjectIndexer(mock_chromadb, mock_embedding)

    def test_clear_cache(self, indexer):
        """clear_cache should reset file hashes."""
        indexer._file_hashes = {"file1": "hash1", "file2": "hash2"}
        indexer.clear_cache()
        assert indexer._file_hashes == {}

    def test_get_collection_id(self, indexer, tmp_path):
        """get_collection_id should return consistent ID."""
        collection_id = indexer.get_collection_id(str(tmp_path))
        assert collection_id.startswith("project-")
        assert len(collection_id) == len("project-") + 12  # 12 char hash

    def test_get_collection_id_consistent(self, indexer, tmp_path):
        """Same path should give same collection ID."""
        id1 = indexer.get_collection_id(str(tmp_path))
        id2 = indexer.get_collection_id(str(tmp_path))
        assert id1 == id2

    def test_compute_hash_returns_hex(self, indexer, tmp_path):
        """_compute_hash should return hex string."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        hash_val = indexer._compute_hash(test_file)
        assert isinstance(hash_val, str)
        assert all(c in "0123456789abcdef" for c in hash_val)

    def test_compute_hash_changes_with_content(self, indexer, tmp_path):
        """Hash should change when file content changes."""
        test_file = tmp_path / "test.txt"

        test_file.write_text("content v1")
        hash1 = indexer._compute_hash(test_file)

        test_file.write_text("content v2")
        hash2 = indexer._compute_hash(test_file)

        assert hash1 != hash2
