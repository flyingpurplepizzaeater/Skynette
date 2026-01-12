# tests/unit/test_rag_ingest_node.py
import pytest
from pathlib import Path
from src.core.nodes.rag.ingest import IngestDocumentNode
from src.rag.service import RAGService


class TestIngestDocumentNode:
    """Test IngestDocument workflow node."""

    @pytest.fixture
    async def rag_service(self, tmp_path):
        """Create temp RAG service."""
        service = RAGService(storage_path=str(tmp_path / "rag"))
        await service.initialize()
        return service

    @pytest.fixture
    def node(self, rag_service):
        """Create node with service."""
        return IngestDocumentNode(rag_service=rag_service)

    def test_node_metadata(self, node):
        """Node should have correct metadata."""
        assert node.type == "rag-ingest-document"
        assert node.name == "Ingest Document"
        assert node.category == "RAG"
        assert node.color == "#7C3AED"

    def test_node_inputs(self, node):
        """Node should have required inputs."""
        input_names = [field.name for field in node.inputs]

        assert "file_path" in input_names
        assert "collection_id" in input_names

    def test_node_outputs(self, node):
        """Node should have outputs."""
        output_names = [field.name for field in node.outputs]

        assert "document_id" in output_names
        assert "chunks_created" in output_names
        assert "status" in output_names
        assert "error" in output_names

    @pytest.mark.asyncio
    async def test_execute_success(self, node, rag_service, tmp_path):
        """Should ingest document successfully."""
        # Create collection
        coll_id = await rag_service.create_collection(name="test")

        # Create test file
        md_file = tmp_path / "test.md"
        md_file.write_text("# Test\n\nContent here.")

        # Execute node
        result = await node.execute({
            "file_path": str(md_file),
            "collection_id": coll_id
        })

        assert result["status"] == "success"
        assert result["document_id"] is not None
        assert result["chunks_created"] > 0
        assert result["error"] is None

    @pytest.mark.asyncio
    async def test_execute_missing_file(self, node, rag_service):
        """Should handle missing file."""
        # Create collection
        coll_id = await rag_service.create_collection(name="test")

        # Execute with non-existent file
        result = await node.execute({
            "file_path": "/nonexistent/file.md",
            "collection_id": coll_id
        })

        assert result["status"] == "error"
        assert result["error"] is not None

    @pytest.mark.asyncio
    async def test_execute_invalid_collection(self, node, tmp_path):
        """Should handle invalid collection."""
        # Create test file
        md_file = tmp_path / "test.md"
        md_file.write_text("# Test")

        # Execute with invalid collection
        result = await node.execute({
            "file_path": str(md_file),
            "collection_id": "nonexistent-collection"
        })

        assert result["status"] == "error"
        assert result["error"] is not None
