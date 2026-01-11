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
