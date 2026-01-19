# tests/test_rag_wiring.py
"""Tests for RAG wiring in CodeEditorView."""

import pytest
from unittest.mock import MagicMock, patch


class TestRAGWiring:
    """Test RAG provider wiring to ChatPanel."""

    def test_code_editor_view_has_rag_components(self):
        """Verify CodeEditorView initializes RAG component references."""
        # Import after patching to avoid Flet initialization
        with patch('flet.Page'):
            with patch('flet.Column.__init__', return_value=None):
                with patch('flet.FilePicker'):
                    from src.ui.views.code_editor import CodeEditorView

                    # Check class has RAG attributes
                    assert hasattr(CodeEditorView, '__init__')

                    # Read the source to verify imports exist
                    import inspect
                    source = inspect.getsource(CodeEditorView)

                    assert 'RAGContextProvider' in source
                    assert '_rag_provider' in source
                    assert '_chromadb_client' in source
                    assert '_embedding_manager' in source

    def test_chat_panel_receives_rag_provider_parameter(self):
        """Verify ChatPanel is instantiated with rag_provider."""
        import inspect
        from src.ui.views.code_editor import CodeEditorView

        source = inspect.getsource(CodeEditorView)

        # Check ChatPanel instantiation includes rag_provider
        assert 'rag_provider=self._rag_provider' in source
        assert 'get_project_root=' in source

    def test_dispose_shuts_down_embedding_manager(self):
        """Verify dispose() cleans up RAG components."""
        import inspect
        from src.ui.views.code_editor import CodeEditorView

        source = inspect.getsource(CodeEditorView.dispose)

        # Check dispose includes embedding manager shutdown
        assert '_embedding_manager' in source
        assert 'shutdown' in source


class TestRAGContextProvider:
    """Test RAGContextProvider functionality."""

    @pytest.mark.asyncio
    async def test_get_context_returns_empty_without_project(self):
        """Verify get_context returns empty when no project root."""
        from src.rag.chromadb_client import ChromaDBClient
        from src.rag.embeddings import EmbeddingManager
        from src.ui.views.code_editor.ai_panel.rag_context import RAGContextProvider

        # Mock dependencies
        mock_chromadb = MagicMock(spec=ChromaDBClient)
        mock_embedding = MagicMock(spec=EmbeddingManager)

        provider = RAGContextProvider(mock_chromadb, mock_embedding)

        # Should return empty when project_root is None
        context, sources = await provider.get_context("test query", None)

        assert context == ""
        assert sources == []

    def test_rag_context_provider_imports(self):
        """Verify RAGContextProvider can be imported from ai_panel."""
        from src.ui.views.code_editor.ai_panel.rag_context import RAGContextProvider

        assert RAGContextProvider is not None
        assert hasattr(RAGContextProvider, 'get_context')
        assert hasattr(RAGContextProvider, 'ensure_indexed')
