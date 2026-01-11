import pytest
import flet as ft
from src.ui.dialogs.collection_dialog import CollectionDialog
from src.rag.service import RAGService


class TestCollectionDialog:
    @pytest.fixture
    def rag_service(self, tmp_path):
        """Create temp RAG service."""
        return RAGService(storage_path=str(tmp_path))

    def test_create_mode_dialog(self, rag_service):
        """Dialog should create in create mode."""
        dialog = CollectionDialog(rag_service=rag_service, collection_id=None)

        assert dialog is not None
        assert isinstance(dialog, ft.AlertDialog)
        assert dialog.collection_id is None

    def test_edit_mode_dialog(self, rag_service):
        """Dialog should create in edit mode."""
        dialog = CollectionDialog(rag_service=rag_service, collection_id="coll-123")

        assert dialog.collection_id == "coll-123"

    def test_validate_name_valid(self, rag_service):
        """_validate_name should accept valid names."""
        dialog = CollectionDialog(rag_service=rag_service)

        assert dialog._validate_name("ProjectDocs") == True
        assert dialog._validate_name("test_123") == True
        assert dialog._validate_name("MyCollection") == True

    def test_validate_name_invalid(self, rag_service):
        """_validate_name should reject invalid names."""
        dialog = CollectionDialog(rag_service=rag_service)

        assert dialog._validate_name("") == False
        assert dialog._validate_name("my-collection") == False  # hyphen
        assert dialog._validate_name("my collection") == False  # space
        assert dialog._validate_name("123") == False  # no letters

    def test_validate_chunk_size(self, rag_service):
        """_validate_chunk_size should validate range."""
        dialog = CollectionDialog(rag_service=rag_service)

        assert dialog._validate_chunk_size(1024) == True
        assert dialog._validate_chunk_size(256) == True
        assert dialog._validate_chunk_size(4096) == True

        assert dialog._validate_chunk_size(100) == False  # too small
        assert dialog._validate_chunk_size(5000) == False  # too large
