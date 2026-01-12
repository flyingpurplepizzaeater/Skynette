"""
Integration tests for complete RAG workflows.

Tests end-to-end flows: create collection → ingest → query.
"""

import pytest
from pathlib import Path
from src.rag.service import RAGService
from src.core.nodes.rag import IngestDocumentNode, QueryKnowledgeNode


@pytest.mark.integration
class TestRAGWorkflow:
    """Test complete RAG workflows."""

    @pytest.fixture
    async def service(self, tmp_path):
        """Create RAG service."""
        service = RAGService(storage_path=str(tmp_path / "rag"))
        await service.initialize()
        return service

    @pytest.mark.asyncio
    async def test_create_ingest_query_workflow(self, service, tmp_path):
        """Test complete workflow: create → ingest → query."""
        # Step 1: Create collection
        coll_id = await service.create_collection(
            name="test_collection",
            description="Test workflow collection"
        )

        assert coll_id is not None

        # Step 2: Create test documents
        doc1 = tmp_path / "python.md"
        doc1.write_text("""# Python Programming Guide

Python is a versatile programming language.

## Features
- Easy to learn
- Object-oriented
- Dynamic typing

## Use Cases
- Web development with Django
- Data science with pandas
- Machine learning with TensorFlow
""")

        doc2 = tmp_path / "javascript.md"
        doc2.write_text("""# JavaScript Guide

JavaScript is the language of the web.

## Features
- Event-driven
- Asynchronous
- Prototype-based

## Use Cases
- Frontend with React
- Backend with Node.js
- Mobile with React Native
""")

        # Step 3: Ingest documents
        ingest_node = IngestDocumentNode(rag_service=service)

        result1 = await ingest_node.execute({
            "file_path": str(doc1),
            "collection_id": coll_id
        })

        result2 = await ingest_node.execute({
            "file_path": str(doc2),
            "collection_id": coll_id
        })

        assert result1["status"] == "success"
        assert result2["status"] == "success"

        # Step 4: Query collection
        query_node = QueryKnowledgeNode(rag_service=service)

        # Query about Python
        python_result = await query_node.execute({
            "query": "What is Python good for?",
            "collection_id": coll_id,
            "top_k": 3
        })

        assert python_result["error"] is None
        assert len(python_result["results"]) > 0

        # Results should mention Python, not JavaScript
        context = python_result["context"].lower()
        assert "python" in context

        # Query about JavaScript
        js_result = await query_node.execute({
            "query": "What is JavaScript used for?",
            "collection_id": coll_id,
            "top_k": 3
        })

        assert js_result["error"] is None
        assert len(js_result["results"]) > 0

        js_context = js_result["context"].lower()
        assert "javascript" in js_context

    @pytest.mark.asyncio
    async def test_multiple_collections(self, service, tmp_path):
        """Test working with multiple collections."""
        # Create two collections
        coll1 = await service.create_collection(name="tech_docs")
        coll2 = await service.create_collection(name="recipes")

        # Create documents for each
        tech_doc = tmp_path / "tech.md"
        tech_doc.write_text("# API Documentation\n\nREST API endpoints.")

        recipe_doc = tmp_path / "recipe.md"
        recipe_doc.write_text("# Pasta Recipe\n\nBoil water, add pasta.")

        # Ingest into different collections
        ingest_node = IngestDocumentNode(rag_service=service)

        await ingest_node.execute({
            "file_path": str(tech_doc),
            "collection_id": coll1
        })

        await ingest_node.execute({
            "file_path": str(recipe_doc),
            "collection_id": coll2
        })

        # Query each collection
        query_node = QueryKnowledgeNode(rag_service=service)

        tech_result = await query_node.execute({
            "query": "API",
            "collection_id": coll1,
            "top_k": 5
        })

        recipe_result = await query_node.execute({
            "query": "cooking",
            "collection_id": coll2,
            "top_k": 5
        })

        # Each should only return relevant results
        assert "API" in tech_result["context"]
        assert "pasta" in recipe_result["context"].lower()

    @pytest.mark.asyncio
    async def test_large_document_chunking(self, service, tmp_path):
        """Test chunking of large documents."""
        # Create large document
        large_doc = tmp_path / "large.md"
        content = "# Large Document\n\n"
        content += "\n\n".join([
            f"## Section {i}\n\nContent for section {i}. " + " ".join(["Word"] * 50)
            for i in range(20)
        ])
        large_doc.write_text(content)

        # Create collection
        coll_id = await service.create_collection(name="large_test")

        # Ingest
        ingest_node = IngestDocumentNode(rag_service=service)
        result = await ingest_node.execute({
            "file_path": str(large_doc),
            "collection_id": coll_id
        })

        # Should create multiple chunks
        assert result["chunks_created"] > 5

        # Query should work
        query_node = QueryKnowledgeNode(rag_service=service)
        query_result = await query_node.execute({
            "query": "Section 10",
            "collection_id": coll_id,
            "top_k": 3
        })

        assert query_result["error"] is None
        assert len(query_result["results"]) > 0
