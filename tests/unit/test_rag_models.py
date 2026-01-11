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

    def test_chunk_overlap_must_be_less_than_chunk_size(self):
        """chunk_overlap must be less than chunk_size."""
        with pytest.raises(ValueError, match="chunk_overlap must be less than chunk_size"):
            Collection(name="test", chunk_size=1024, chunk_overlap=1024)

        with pytest.raises(ValueError, match="chunk_overlap must be less than chunk_size"):
            Collection(name="test", chunk_size=512, chunk_overlap=600)

    def test_max_chunk_size_must_be_gte_chunk_size(self):
        """max_chunk_size must be >= chunk_size."""
        with pytest.raises(ValueError, match="max_chunk_size must be >= chunk_size"):
            Collection(name="test", chunk_size=2048, max_chunk_size=1024)

        # This should work
        coll = Collection(name="test", chunk_size=1024, max_chunk_size=1024)
        assert coll.max_chunk_size == 1024

    def test_embedding_model_only_accepts_valid_values(self):
        """embedding_model must be one of: local, openai, cohere."""
        # Valid values should work
        coll1 = Collection(name="test1", embedding_model="local")
        assert coll1.embedding_model == "local"

        coll2 = Collection(name="test2", embedding_model="openai")
        assert coll2.embedding_model == "openai"

        coll3 = Collection(name="test3", embedding_model="cohere")
        assert coll3.embedding_model == "cohere"

        # Invalid value should fail
        with pytest.raises(ValueError):
            Collection(name="test", embedding_model="invalid_model")


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

    def test_status_only_accepts_valid_values(self):
        """status must be one of: queued, processing, indexed, failed."""
        # Valid values should work
        doc1 = Document(
            collection_id="coll-123",
            source_path="/path/to/file.md",
            file_type="markdown",
            file_hash="abc123",
            status="queued"
        )
        assert doc1.status == "queued"

        doc2 = Document(
            collection_id="coll-123",
            source_path="/path/to/file.md",
            file_type="markdown",
            file_hash="abc123",
            status="processing"
        )
        assert doc2.status == "processing"

        doc3 = Document(
            collection_id="coll-123",
            source_path="/path/to/file.md",
            file_type="markdown",
            file_hash="abc123",
            status="indexed"
        )
        assert doc3.status == "indexed"

        doc4 = Document(
            collection_id="coll-123",
            source_path="/path/to/file.md",
            file_type="markdown",
            file_hash="abc123",
            status="failed"
        )
        assert doc4.status == "failed"

        # Invalid value should fail
        with pytest.raises(ValueError):
            Document(
                collection_id="coll-123",
                source_path="/path/to/file.md",
                file_type="markdown",
                file_hash="abc123",
                status="invalid_status"
            )

    def test_empty_string_validation(self):
        """source_path, file_type, and file_hash must not be empty."""
        with pytest.raises(ValueError):
            Document(
                collection_id="coll-123",
                source_path="",
                file_type="markdown",
                file_hash="abc123"
            )

        with pytest.raises(ValueError):
            Document(
                collection_id="coll-123",
                source_path="/path/to/file.md",
                file_type="",
                file_hash="abc123"
            )

        with pytest.raises(ValueError):
            Document(
                collection_id="coll-123",
                source_path="/path/to/file.md",
                file_type="markdown",
                file_hash=""
            )


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

    def test_chunk_index_must_be_non_negative(self):
        """chunk_index must be >= 0."""
        # Valid values should work
        chunk1 = Chunk(
            document_id="doc-123",
            chunk_index=0,
            content="Content"
        )
        assert chunk1.chunk_index == 0

        chunk2 = Chunk(
            document_id="doc-123",
            chunk_index=100,
            content="Content"
        )
        assert chunk2.chunk_index == 100

        # Negative value should fail
        with pytest.raises(ValueError):
            Chunk(
                document_id="doc-123",
                chunk_index=-1,
                content="Content"
            )
