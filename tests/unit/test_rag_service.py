# tests/unit/test_rag_service.py
import pytest
from pathlib import Path
from src.rag.service import RAGService
from src.rag.models import Collection


class TestRAGService:
    """Test RAG service integration."""

    @pytest.fixture
    async def service(self, tmp_path):
        """Create temp RAG service."""
        service = RAGService(storage_path=str(tmp_path))
        await service.initialize()
        return service

    @pytest.mark.asyncio
    async def test_create_collection(self, service):
        """Should create collection."""
        coll_id = await service.create_collection(
            name="test_collection",
            description="Test"
        )

        assert coll_id is not None

        coll = service.storage.get_collection(coll_id)
        assert coll.name == "test_collection"

    @pytest.mark.asyncio
    async def test_ingest_document(self, service, tmp_path):
        """Should ingest markdown document."""
        # Create collection
        coll_id = await service.create_collection(name="test")

        # Create test file
        md_file = tmp_path / "test.md"
        md_file.write_text("""# Test Document

This is a test document for ingestion.

## Section 1

Content for section 1.
""")

        # Ingest
        result = await service.ingest_document(
            file_path=str(md_file),
            collection_id=coll_id
        )

        assert result["status"] == "success"
        assert result["chunks_created"] > 0

        # Verify document saved
        doc = service.storage.get_document(result["document_id"])
        assert doc is not None
        assert doc.status == "indexed"

    @pytest.mark.asyncio
    async def test_query_collection(self, service, tmp_path):
        """Should query and return similar chunks."""
        # Create collection
        coll_id = await service.create_collection(name="test")

        # Ingest document
        md_file = tmp_path / "test.md"
        md_file.write_text("""# Python Programming

Python is a high-level programming language.

## Features

Python supports multiple programming paradigms.
""")

        await service.ingest_document(str(md_file), coll_id)

        # Query
        results = await service.query(
            query="What is Python?",
            collection_id=coll_id,
            top_k=3
        )

        assert len(results) > 0
        assert "Python" in results[0]["content"]
        assert "similarity" in results[0]

    @pytest.mark.asyncio
    async def test_delete_document(self, service, tmp_path):
        """Should delete document and chunks."""
        # Create collection
        coll_id = await service.create_collection(name="test")

        # Ingest document
        md_file = tmp_path / "test.md"
        md_file.write_text("# Test\n\nContent")

        result = await service.ingest_document(str(md_file), coll_id)
        doc_id = result["document_id"]

        # Delete
        await service.delete_document(doc_id, coll_id)

        # Verify deleted
        doc = service.storage.get_document(doc_id)
        assert doc is None

    @pytest.mark.asyncio
    async def test_get_collection_stats(self, service, tmp_path):
        """Should return collection statistics."""
        # Create collection
        coll_id = await service.create_collection(name="test")

        # Ingest document
        md_file = tmp_path / "test.md"
        md_file.write_text("# Test\n\nContent " * 100)

        await service.ingest_document(str(md_file), coll_id)

        # Get stats
        stats = await service.get_collection_stats(coll_id)

        assert stats["document_count"] == 1
        assert stats["chunk_count"] > 0
