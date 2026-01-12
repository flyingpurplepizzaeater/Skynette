import pytest
import flet as ft
from src.ui.dialogs.upload_dialog import UploadDialog
from src.rag.service import RAGService


class TestUploadDialog:
    @pytest.fixture
    def rag_service(self, tmp_path):
        """Create temp RAG service."""
        return RAGService(storage_path=str(tmp_path))

    def test_dialog_creation(self, rag_service):
        """UploadDialog should create with collection ID."""
        dialog = UploadDialog(
            rag_service=rag_service,
            collection_id="coll-123",
            page=None,
        )

        assert dialog is not None
        assert dialog.collection_id == "coll-123"
        assert len(dialog.selected_files) == 0

    def test_has_file_picker_tab(self, rag_service):
        """Dialog should have file picker tab."""
        dialog = UploadDialog(
            rag_service=rag_service,
            collection_id="coll-123",
            page=None,
        )

        # Check has upload_tabs control (Column for now)
        assert hasattr(dialog, 'upload_tabs')
        assert isinstance(dialog.upload_tabs, ft.Column)
