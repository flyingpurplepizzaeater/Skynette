import pytest
import flet as ft
from src.ui.dialogs.query_dialog import QueryDialog
from src.rag.service import RAGService


class TestQueryDialog:
    def test_dialog_creation(self, tmp_path):
        """QueryDialog should create with collection info."""
        rag_service = RAGService(storage_path=str(tmp_path))
        dialog = QueryDialog(
            rag_service=rag_service,
            collection_id="coll-123",
            collection_name="TestCollection",
        )

        assert dialog is not None
        assert dialog.collection_id == "coll-123"

    def test_has_query_field(self, tmp_path):
        """Dialog should have query input field."""
        rag_service = RAGService(storage_path=str(tmp_path))
        dialog = QueryDialog(
            rag_service=rag_service,
            collection_id="coll-123",
            collection_name="TestCollection",
        )

        assert hasattr(dialog, 'query_field')
        assert isinstance(dialog.query_field, ft.TextField)

    def test_has_search_button(self, tmp_path):
        """Dialog should have Search button."""
        rag_service = RAGService(storage_path=str(tmp_path))
        dialog = QueryDialog(
            rag_service=rag_service,
            collection_id="coll-123",
            collection_name="TestCollection",
        )

        # Check actions has button
        assert any(
            isinstance(action, ft.Button) or
            (hasattr(action, 'text') and 'Search' in action.text)
            for action in dialog.content.controls
        )
