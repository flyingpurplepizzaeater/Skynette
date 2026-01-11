# tests/unit/test_rag_storage.py
import pytest
from pathlib import Path
from src.rag.storage import RAGStorage
from src.rag.models import Collection, Document, Chunk


class TestRAGStorage:
    """Test RAG metadata storage."""

    @pytest.fixture
    def storage(self, tmp_path):
        """Create temp storage."""
        return RAGStorage(str(tmp_path / "test.db"))

    def test_create_collection(self, storage):
        """Should create and retrieve collection."""
        coll = Collection(name="test", description="Test collection")

        storage.save_collection(coll)

        retrieved = storage.get_collection(coll.id)
        assert retrieved is not None
        assert retrieved.name == "test"

    def test_list_collections(self, storage):
        """Should list all collections."""
        coll1 = Collection(name="coll1")
        coll2 = Collection(name="coll2")

        storage.save_collection(coll1)
        storage.save_collection(coll2)

        collections = storage.list_collections()
        assert len(collections) == 2

    def test_delete_collection(self, storage):
        """Should delete collection and cascade documents."""
        coll = Collection(name="test")
        storage.save_collection(coll)

        doc = Document(
            collection_id=coll.id,
            source_path="/test.md",
            file_type="markdown",
            file_hash="abc123"
        )
        storage.save_document(doc)

        storage.delete_collection(coll.id)

        assert storage.get_collection(coll.id) is None
        assert storage.get_document(doc.id) is None  # Cascaded

    def test_save_document(self, storage):
        """Should save and retrieve document."""
        coll = Collection(name="test")
        storage.save_collection(coll)

        doc = Document(
            collection_id=coll.id,
            source_path="/path/to/file.md",
            file_type="markdown",
            file_hash="abc123def456"
        )

        storage.save_document(doc)

        retrieved = storage.get_document(doc.id)
        assert retrieved is not None
        assert retrieved.source_path == "/path/to/file.md"

    def test_save_chunk(self, storage):
        """Should save and retrieve chunk."""
        coll = Collection(name="test")
        storage.save_collection(coll)

        doc = Document(
            collection_id=coll.id,
            source_path="/test.md",
            file_type="markdown",
            file_hash="abc"
        )
        storage.save_document(doc)

        chunk = Chunk(
            document_id=doc.id,
            chunk_index=0,
            content="# Test\n\nContent here",
            metadata={"type": "section"}
        )

        storage.save_chunk(chunk)

        retrieved = storage.get_chunk(chunk.id)
        assert retrieved is not None
        assert retrieved.content == "# Test\n\nContent here"

    def test_get_document_chunks(self, storage):
        """Should get all chunks for a document."""
        coll = Collection(name="test")
        storage.save_collection(coll)

        doc = Document(
            collection_id=coll.id,
            source_path="/test.md",
            file_type="markdown",
            file_hash="abc"
        )
        storage.save_document(doc)

        # Create 3 chunks
        for i in range(3):
            chunk = Chunk(
                document_id=doc.id,
                chunk_index=i,
                content=f"Chunk {i}",
                metadata={}
            )
            storage.save_chunk(chunk)

        chunks = storage.get_document_chunks(doc.id)
        assert len(chunks) == 3
        assert chunks[0].chunk_index == 0
