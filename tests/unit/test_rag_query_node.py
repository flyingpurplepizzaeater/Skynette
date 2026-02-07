# tests/unit/test_rag_query_node.py
import pytest
from pathlib import Path
from src.core.nodes.rag.query import QueryKnowledgeNode
from src.rag.service import RAGService


class TestQueryKnowledgeNode:
    """Test QueryKnowledge workflow node."""

    @pytest.fixture
    async def rag_service(self, tmp_path, mock_sentence_transformer):
        """Create temp RAG service with test data and mocked embeddings."""
        service = RAGService(storage_path=str(tmp_path / "rag"))
        await service.initialize()

        # Create collection and ingest test document
        coll_id = await service.create_collection(name="test")

        md_file = tmp_path / "test.md"
        md_file.write_text("""# Python Programming

Python is a high-level programming language.

## Features

Python supports object-oriented programming.
""")

        await service.ingest_document(str(md_file), coll_id)

        return service, coll_id

    @pytest.fixture
    def node(self, rag_service):
        """Create node with service."""
        service, _ = rag_service
        return QueryKnowledgeNode(rag_service=service)

    def test_node_metadata(self, node):
        """Node should have correct metadata."""
        assert node.type == "rag-query-knowledge"
        assert node.name == "Query Knowledge"
        assert node.category == "RAG"
        assert node.color == "#7C3AED"

    def test_node_inputs(self, node):
        """Node should have required inputs."""
        input_names = [field.name for field in node.inputs]

        assert "query" in input_names
        assert "collection_id" in input_names
        assert "top_k" in input_names
        assert "min_similarity" in input_names

    def test_node_outputs(self, node):
        """Node should have outputs."""
        output_names = [field.name for field in node.outputs]

        assert "results" in output_names
        assert "context" in output_names
        assert "error" in output_names

    @pytest.mark.asyncio
    async def test_execute_query(self, rag_service):
        """Should query and return results."""
        service, coll_id = rag_service
        node = QueryKnowledgeNode(rag_service=service)

        result = await node.execute({
            "query": "What is Python?",
            "collection_id": coll_id,
            "top_k": 3,
            "min_similarity": 0.0
        })

        assert result["error"] is None
        assert len(result["results"]) > 0
        assert "Python" in result["context"]

        # Check result structure
        first_result = result["results"][0]
        assert "content" in first_result
        assert "similarity" in first_result

    @pytest.mark.asyncio
    async def test_execute_no_results(self, rag_service):
        """Should handle no results gracefully."""
        service, coll_id = rag_service
        node = QueryKnowledgeNode(rag_service=service)

        result = await node.execute({
            "query": "quantum physics",
            "collection_id": coll_id,
            "top_k": 3,
            "min_similarity": 0.95  # Very high threshold
        })

        assert result["error"] is None
        assert result["results"] == []
        assert result["context"] == ""

    @pytest.mark.asyncio
    async def test_execute_invalid_collection(self, rag_service):
        """Should handle invalid collection."""
        service, _ = rag_service
        node = QueryKnowledgeNode(rag_service=service)

        result = await node.execute({
            "query": "test",
            "collection_id": "nonexistent",
            "top_k": 3
        })

        assert result["error"] is not None
        assert result["results"] == []
