# tests/unit/test_rag_context.py
"""Tests for RAGContextProvider."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from src.ui.views.code_editor.ai_panel.rag_context import RAGContextProvider


class TestRAGContextProvider:
    """Tests for RAGContextProvider class."""

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
    def rag_provider(self, mock_chromadb, mock_embedding_manager):
        """Create RAGContextProvider instance."""
        return RAGContextProvider(mock_chromadb, mock_embedding_manager)

    def test_init_creates_indexer(self, mock_chromadb, mock_embedding_manager):
        """Should create ProjectIndexer on init."""
        provider = RAGContextProvider(mock_chromadb, mock_embedding_manager)
        assert provider._indexer is not None
        assert provider._indexed_projects == set()

    def test_is_indexed_returns_false_initially(self, rag_provider):
        """is_indexed should return False for new projects."""
        assert rag_provider.is_indexed("/some/project") is False

    def test_clear_index_single_project(self, rag_provider):
        """clear_index should clear single project."""
        rag_provider._indexed_projects.add("/project1")
        rag_provider._indexed_projects.add("/project2")

        rag_provider.clear_index("/project1")

        assert "/project1" not in rag_provider._indexed_projects
        assert "/project2" in rag_provider._indexed_projects

    def test_clear_index_all_projects(self, rag_provider):
        """clear_index with None should clear all projects."""
        rag_provider._indexed_projects.add("/project1")
        rag_provider._indexed_projects.add("/project2")

        rag_provider.clear_index()

        assert len(rag_provider._indexed_projects) == 0


class TestEnsureIndexed:
    """Tests for ensure_indexed method."""

    @pytest.fixture
    def mock_chromadb(self):
        """Create mock ChromaDB client."""
        client = MagicMock()
        client.create_collection = AsyncMock()
        return client

    @pytest.fixture
    def mock_embedding_manager(self):
        """Create mock embedding manager."""
        manager = MagicMock()
        manager.embedding_dim = 384
        manager.model_name = "all-MiniLM-L6-v2"
        return manager

    @pytest.mark.asyncio
    async def test_returns_none_if_already_indexed(self, mock_chromadb, mock_embedding_manager):
        """Should return None if project already indexed."""
        provider = RAGContextProvider(mock_chromadb, mock_embedding_manager)
        provider._indexed_projects.add("/my/project")

        result = await provider.ensure_indexed("/my/project")

        assert result is None

    @pytest.mark.asyncio
    async def test_indexes_new_project(self, mock_chromadb, mock_embedding_manager, tmp_path):
        """Should index a new project and return stats."""
        # Create a test file
        test_file = tmp_path / "main.py"
        test_file.write_text("print('hello')")

        # Mock embedding manager
        mock_embedding_manager.embed_batch = AsyncMock(return_value=[[0.1] * 384])

        provider = RAGContextProvider(mock_chromadb, mock_embedding_manager)

        result = await provider.ensure_indexed(str(tmp_path))

        assert result is not None
        assert "indexed" in result
        assert str(tmp_path) in provider._indexed_projects

    @pytest.mark.asyncio
    async def test_skips_if_indexing_in_progress(self, mock_chromadb, mock_embedding_manager):
        """Should return None if indexing is already in progress."""
        provider = RAGContextProvider(mock_chromadb, mock_embedding_manager)
        provider._indexing_in_progress.add("/my/project")

        result = await provider.ensure_indexed("/my/project")

        assert result is None


class TestGetContext:
    """Tests for get_context method."""

    @pytest.fixture
    def mock_chromadb(self):
        """Create mock ChromaDB client."""
        client = MagicMock()
        client.create_collection = AsyncMock()
        client.collection_exists = AsyncMock(return_value=True)
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
    async def test_returns_empty_for_no_project(self, mock_chromadb, mock_embedding_manager):
        """Should return empty tuple if no project root."""
        provider = RAGContextProvider(mock_chromadb, mock_embedding_manager)

        context, sources = await provider.get_context("query", None)

        assert context == ""
        assert sources == []

    @pytest.mark.asyncio
    async def test_formats_context_string(self, mock_chromadb, mock_embedding_manager, tmp_path):
        """Should format context string correctly."""
        # Setup mock to return results
        from src.rag.models import Chunk

        mock_chunk = Chunk(
            document_id="doc-123",
            chunk_index=0,
            content="def main(): pass",
            metadata={"source_path": str(tmp_path / "main.py"), "language": "py"},
        )
        mock_chromadb.query = AsyncMock(return_value=[
            {"chunk": mock_chunk, "similarity": 0.9}
        ])

        # Create a file so indexing works
        (tmp_path / "main.py").write_text("def main(): pass")

        provider = RAGContextProvider(mock_chromadb, mock_embedding_manager)

        context, sources = await provider.get_context("what does main do", str(tmp_path))

        assert "## Relevant Code" in context
        assert "def main(): pass" in context
        assert len(sources) == 1
        assert sources[0]["similarity"] == 0.9

    @pytest.mark.asyncio
    async def test_returns_sources_list(self, mock_chromadb, mock_embedding_manager, tmp_path):
        """Should return sources list with correct structure."""
        from src.rag.models import Chunk

        mock_chunk = Chunk(
            document_id="doc-123",
            chunk_index=0,
            content="class MyClass: pass",
            metadata={"source_path": "/path/to/file.py", "language": "py"},
        )
        mock_chromadb.query = AsyncMock(return_value=[
            {"chunk": mock_chunk, "similarity": 0.85}
        ])

        (tmp_path / "file.py").write_text("class MyClass: pass")

        provider = RAGContextProvider(mock_chromadb, mock_embedding_manager)

        _, sources = await provider.get_context("MyClass", str(tmp_path))

        assert len(sources) == 1
        assert "path" in sources[0]
        assert "snippet" in sources[0]
        assert "language" in sources[0]
        assert "similarity" in sources[0]

    @pytest.mark.asyncio
    async def test_handles_query_error_gracefully(self, mock_chromadb, mock_embedding_manager, tmp_path):
        """Should return empty on query error."""
        # First call for indexing works, second for query fails
        call_count = [0]

        async def mock_query(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] > 0:
                raise Exception("Query failed")
            return []

        mock_chromadb.query = mock_query

        (tmp_path / "main.py").write_text("code")

        provider = RAGContextProvider(mock_chromadb, mock_embedding_manager)
        # Mark as indexed to skip indexing
        provider._indexed_projects.add(str(tmp_path))

        context, sources = await provider.get_context("query", str(tmp_path))

        # Should return empty, not raise
        assert context == ""
        assert sources == []

    @pytest.mark.asyncio
    async def test_truncates_long_snippets(self, mock_chromadb, mock_embedding_manager, tmp_path):
        """Should truncate long snippets in sources."""
        from src.rag.models import Chunk

        long_content = "x" * 500  # 500 chars, longer than 200 limit

        mock_chunk = Chunk(
            document_id="doc-123",
            chunk_index=0,
            content=long_content,
            metadata={"source_path": "/path/to/file.py", "language": "py"},
        )
        mock_chromadb.query = AsyncMock(return_value=[
            {"chunk": mock_chunk, "similarity": 0.8}
        ])

        (tmp_path / "file.py").write_text(long_content)

        provider = RAGContextProvider(mock_chromadb, mock_embedding_manager)

        _, sources = await provider.get_context("query", str(tmp_path))

        assert len(sources[0]["snippet"]) <= 203  # 200 + "..."
        assert sources[0]["snippet"].endswith("...")


class TestChatPanelRAGIntegration:
    """Tests for RAG integration in ChatPanel.

    Note: These tests verify the ChatPanel constructor signature
    accepts RAG parameters. Full integration testing requires
    a running Flet environment.
    """

    def test_chat_panel_signature_includes_rag_provider(self):
        """ChatPanel __init__ should accept rag_provider parameter."""
        import inspect
        from src.ui.views.code_editor.ai_panel.chat_panel import ChatPanel

        sig = inspect.signature(ChatPanel.__init__)
        params = list(sig.parameters.keys())

        assert "rag_provider" in params
        assert "get_project_root" in params

    def test_chat_panel_rag_provider_default_is_none(self):
        """rag_provider should default to None."""
        import inspect
        from src.ui.views.code_editor.ai_panel.chat_panel import ChatPanel

        sig = inspect.signature(ChatPanel.__init__)
        rag_param = sig.parameters["rag_provider"]

        assert rag_param.default is None

    def test_chat_panel_get_project_root_default_is_none(self):
        """get_project_root should default to None."""
        import inspect
        from src.ui.views.code_editor.ai_panel.chat_panel import ChatPanel

        sig = inspect.signature(ChatPanel.__init__)
        get_root_param = sig.parameters["get_project_root"]

        assert get_root_param.default is None

    def test_build_api_messages_accepts_rag_context(self):
        """_build_api_messages should accept rag_context parameter."""
        import inspect
        from src.ui.views.code_editor.ai_panel.chat_panel import ChatPanel

        sig = inspect.signature(ChatPanel._build_api_messages)
        params = list(sig.parameters.keys())

        assert "rag_context" in params
