"""
Integration tests for knowledge base upload workflow.

Tests the complete upload workflow: create collection → upload files → query.
"""

import pytest
from pathlib import Path
from src.rag.service import RAGService


@pytest.mark.integration
@pytest.mark.asyncio
class TestKnowledgeBasesUpload:
    """Test knowledge base upload workflows."""

    @pytest.fixture
    async def rag_service(self, tmp_path):
        """Create and initialize RAG service."""
        service = RAGService(storage_path=str(tmp_path / "test_rag"))
        await service.initialize()
        return service

    async def test_create_collection_and_upload_files(self, rag_service, tmp_path):
        """Full workflow: create collection → upload files → query."""
        # Step 1: Create collection
        collection_id = await rag_service.create_collection(
            name="TestCollection",
            description="Test collection",
            embedding_model="local",
            chunk_size=1024,
            chunk_overlap=128,
            max_chunk_size=2048,
        )

        assert collection_id is not None

        # Step 2: Create test files
        file1 = tmp_path / "doc1.md"
        file1.write_text("# Document 1\n\nThis is the first test document.")

        file2 = tmp_path / "doc2.txt"
        file2.write_text("This is the second test document with different content.")

        # Step 3: Upload files
        results = []
        for file_path in [str(file1), str(file2)]:
            result = await rag_service.ingest_document(
                file_path=file_path,
                collection_id=collection_id,
            )
            results.append(result)

        # Step 4: Verify uploads
        assert len(results) == 2
        assert all(r["status"] == "success" for r in results)
        assert all("document_id" in r for r in results)
        assert all("chunks_created" in r for r in results)

        # Step 5: Query collection
        query_results = await rag_service.query(
            query="test document",
            collection_id=collection_id,
            top_k=5,
            min_similarity=0.3,
        )

        # Step 6: Verify query results
        # Should find chunks from both documents
        assert len(query_results) >= 2

        # Extract content from results
        contents = [r["content"].lower() for r in query_results]
        combined_content = " ".join(contents)

        # Should find content from both documents
        assert "first" in combined_content or "document 1" in combined_content
        assert "second" in combined_content or "different content" in combined_content

    async def test_upload_with_errors(self, rag_service, tmp_path):
        """Upload should handle errors gracefully."""
        # Step 1: Create collection
        collection_id = await rag_service.create_collection(
            name="ErrorTest",
            embedding_model="local",
        )

        # Step 2: Create test files
        # Valid file
        valid_file = tmp_path / "valid.md"
        valid_file.write_text("# Valid Document\n\nThis is valid content that should be indexed.")

        # Invalid file (binary file that will fail UTF-8 decoding)
        invalid_file = tmp_path / "invalid.bin"
        invalid_file.write_bytes(b'\x00\x01\x02\x03\xFF\xFE\xFD\xFC')

        # Nonexistent file
        nonexistent_file = tmp_path / "does_not_exist.md"

        # Step 3: Process files
        results = []
        for file_path in [str(valid_file), str(invalid_file), str(nonexistent_file)]:
            result = await rag_service.ingest_document(
                file_path=file_path,
                collection_id=collection_id,
            )
            results.append(result)

        # Step 4: Verify results
        assert len(results) == 3

        # First file should succeed
        assert results[0]["status"] == "success"
        assert "document_id" in results[0]

        # Second file should fail (binary file - UTF-8 decode error)
        assert results[1]["status"] == "error"
        assert "error" in results[1]

        # Third file should fail (file not found)
        assert results[2]["status"] == "error"
        assert "error" in results[2]

        # Step 5: Query collection
        # Valid file should be indexed and queryable
        query_results = await rag_service.query(
            query="valid",
            collection_id=collection_id,
            top_k=5,
        )

        # Should find the valid document
        assert len(query_results) >= 1
        assert any("valid" in r["content"].lower() for r in query_results)

    async def test_multiple_file_upload_to_same_collection(self, rag_service, tmp_path):
        """Test uploading multiple files to the same collection."""
        # Step 1: Create collection
        collection_id = await rag_service.create_collection(
            name="MultiFileTest",
            description="Test multiple file uploads",
            embedding_model="local",
        )

        # Step 2: Create multiple test files with distinct content
        files = []
        for i in range(3):
            file_path = tmp_path / f"document_{i}.md"
            file_path.write_text(f"# Document {i}\n\nUnique content for document number {i}.")
            files.append(str(file_path))

        # Step 3: Upload all files
        results = []
        for file_path in files:
            result = await rag_service.ingest_document(
                file_path=file_path,
                collection_id=collection_id,
            )
            results.append(result)

        # Step 4: Verify all uploads succeeded
        assert len(results) == 3
        assert all(r["status"] == "success" for r in results)

        # Step 5: Verify collection stats
        stats = await rag_service.get_collection_stats(collection_id)
        assert stats["document_count"] == 3
        assert stats["chunk_count"] >= 3  # At least one chunk per document

        # Step 6: Query for content from different documents
        for i in range(3):
            query_results = await rag_service.query(
                query=f"document number {i}",
                collection_id=collection_id,
                top_k=5,
            )

            # Should find content from the specific document
            assert len(query_results) >= 1
            contents = " ".join([r["content"].lower() for r in query_results])
            assert f"document {i}" in contents or f"number {i}" in contents
