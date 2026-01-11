import pytest
import flet as ft
from src.ui.views.knowledge_bases import KnowledgeBasesView


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
