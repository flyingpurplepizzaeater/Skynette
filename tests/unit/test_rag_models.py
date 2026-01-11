# tests/unit/test_rag_models.py
import pytest
from datetime import datetime
from src.rag.models import Collection, Document, Chunk


class TestCollection:
    """Test Collection data model."""

    def test_create_collection_with_defaults(self):
        """Collection should create with default values."""
        coll = Collection(
            name="test_collection",
            description="Test collection"
        )

        assert coll.id is not None
        assert coll.name == "test_collection"
        assert coll.embedding_model == "local"
        assert coll.chunk_size == 1024
        assert coll.chunk_overlap == 128
        assert isinstance(coll.created_at, datetime)

    def test_collection_validates_chunk_size(self):
        """Chunk size must be reasonable."""
        with pytest.raises(ValueError):
            Collection(name="test", chunk_size=50)  # Too small

        with pytest.raises(ValueError):
            Collection(name="test", chunk_size=10000)  # Too large


class TestDocument:
    """Test Document data model."""

    def test_create_document(self):
        """Document should store file metadata."""
        doc = Document(
            collection_id="coll-123",
            source_path="/path/to/file.md",
            file_type="markdown",
            file_hash="abc123"
        )

        assert doc.id is not None
        assert doc.status == "queued"
        assert doc.chunk_count == 0


class TestChunk:
    """Test Chunk data model."""

    def test_create_chunk(self):
        """Chunk should store content and metadata."""
        chunk = Chunk(
            document_id="doc-123",
            chunk_index=0,
            content="# Test Document\n\nContent here",
            metadata={"type": "section", "heading": "Test Document"}
        )

        assert chunk.id is not None
        assert chunk.chunk_index == 0
        assert "Test Document" in chunk.content
