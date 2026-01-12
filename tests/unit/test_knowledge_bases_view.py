import pytest
from unittest.mock import AsyncMock, patch
import flet as ft
from src.ui.views.knowledge_bases import KnowledgeBasesView
from src.rag.models import Collection


class TestKnowledgeBasesView:
    def test_view_creation(self):
        """KnowledgeBasesView should create without error."""
        view = KnowledgeBasesView()

        assert view is not None
        assert view.expand is True

    def test_build_returns_column(self):
        """build() should return a Column."""
        view = KnowledgeBasesView()
        result = view.build()

        assert isinstance(result, ft.Column)
        assert result.expand is True

    def test_header_has_title_and_button(self):
        """Header should have title and New Collection button."""
        view = KnowledgeBasesView()
        header = view._build_header()

        assert isinstance(header, ft.Row)
        # Check has Text and Button
        has_text = any(isinstance(c, ft.Text) for c in header.controls)
        has_button = any(isinstance(c, ft.Button) for c in header.controls)
        assert has_text
        assert has_button

    def test_empty_state_shown_when_no_collections(self):
        """Empty state should display when collections list is empty."""
        view = KnowledgeBasesView()
        grid = view._build_collections_grid()

        assert isinstance(grid, ft.Container)
        assert grid.expand is True

    def test_rag_service_injection(self):
        """KnowledgeBasesView should accept RAGService via dependency injection."""
        mock_service = "mock_rag_service"
        view = KnowledgeBasesView(rag_service=mock_service)

        assert view.rag_service == mock_service

    def test_empty_state_has_cta_button(self):
        """Empty state should have a call-to-action button."""
        view = KnowledgeBasesView()
        empty_state = view._build_empty_state()

        # Navigate to inner column and find button
        inner_column = empty_state.content
        has_button = any(isinstance(c, ft.Button) for c in inner_column.controls)
        assert has_button


class TestKnowledgeBasesViewLoading:
    @pytest.mark.asyncio
    async def test_load_collections(self):
        """_load_collections should fetch and convert collections."""
        from unittest.mock import MagicMock

        # Create mock RAGService
        mock_service = MagicMock()
        view = KnowledgeBasesView(rag_service=mock_service)

        # Mock RAGService methods
        with patch.object(mock_service, 'list_collections', new_callable=AsyncMock) as mock_list:
            mock_list.return_value = [
                Collection(
                    id="coll-1",
                    name="Test1",
                    description="",
                    embedding_model="local",
                    chunk_size=1024,
                    chunk_overlap=128,
                    max_chunk_size=2048,
                ),
            ]

            with patch.object(mock_service, 'get_collection_stats', new_callable=AsyncMock) as mock_stats:
                mock_stats.return_value = {
                    "document_count": 10,
                    "chunk_count": 50,
                    "storage_size_bytes": 1024 * 1024,
                }

                await view._load_collections()

                assert len(view.collections) == 1
                assert view.collections[0].name == "Test1"
                assert view.collections[0].document_count == 10


class TestKnowledgeBasesViewCaching:
    @pytest.mark.asyncio
    async def test_collections_cached(self):
        """Collections should be cached to avoid repeated fetches."""
        from unittest.mock import MagicMock

        # Create mock RAGService
        mock_service = MagicMock()
        view = KnowledgeBasesView(rag_service=mock_service)

        with patch.object(mock_service, 'list_collections', new_callable=AsyncMock) as mock_list:
            mock_list.return_value = []

            # First load
            await view._load_collections()
            assert mock_list.call_count == 1

            # Second load within cache TTL
            await view._load_collections()
            # Should still be 1 (used cache)
            assert mock_list.call_count == 1

    @pytest.mark.asyncio
    async def test_cache_invalidated_on_create(self):
        """Cache should invalidate when collection created."""
        from unittest.mock import MagicMock

        # Create mock RAGService
        mock_service = MagicMock()
        view = KnowledgeBasesView(rag_service=mock_service)

        # Mock first load
        with patch.object(mock_service, 'list_collections', new_callable=AsyncMock) as mock_list:
            mock_list.return_value = []
            await view._load_collections()

        # Invalidate cache
        view._invalidate_cache()

        # Next load should refetch
        with patch.object(mock_service, 'list_collections', new_callable=AsyncMock) as mock_list:
            mock_list.return_value = []
            await view._load_collections()
            assert mock_list.call_count == 1
