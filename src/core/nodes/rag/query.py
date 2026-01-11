"""
Query Knowledge Node

Workflow node for semantic search in RAG collections.
"""

from typing import Any, Dict
from src.core.nodes.base import BaseNode, NodeField, FieldType


class QueryKnowledgeNode(BaseNode):
    """
    Query RAG collection for similar content.

    Performs semantic search and returns top-k similar chunks.
    """

    type = "rag-query-knowledge"
    name = "Query Knowledge"
    category = "RAG"
    description = "Semantic search in knowledge base"
    icon = "search"
    color = "#7C3AED"  # Purple (RAG category color)

    inputs = [
        NodeField(
            name="query",
            label="Query",
            type=FieldType.TEXT,
            required=True,
            description="Search query"
        ),
        NodeField(
            name="collection_id",
            label="Collection ID",
            type=FieldType.STRING,
            required=True,
            description="Collection to search"
        ),
        NodeField(
            name="top_k",
            label="Top K Results",
            type=FieldType.NUMBER,
            required=False,
            default=5,
            description="Number of results to return"
        ),
        NodeField(
            name="min_similarity",
            label="Min Similarity",
            type=FieldType.NUMBER,
            required=False,
            default=0.0,
            description="Minimum similarity threshold (0-1)"
        ),
    ]

    outputs = [
        NodeField(
            name="results",
            label="Results",
            type=FieldType.JSON,
            description="List of matching chunks with similarity scores"
        ),
        NodeField(
            name="context",
            label="Context",
            type=FieldType.TEXT,
            description="Concatenated text from results (ready for AI prompts)"
        ),
        NodeField(
            name="error",
            label="Error",
            type=FieldType.STRING,
            description="Error message if failed"
        ),
    ]

    def __init__(self, rag_service=None, **kwargs):
        """Initialize with RAG service."""
        super().__init__(**kwargs)
        self.rag_service = rag_service

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute semantic search."""
        try:
            query = inputs["query"]
            collection_id = inputs["collection_id"]
            top_k = inputs.get("top_k", 5)
            min_similarity = inputs.get("min_similarity", 0.0)

            # Query collection
            results = await self.rag_service.query(
                query=query,
                collection_id=collection_id,
                top_k=top_k,
                min_similarity=min_similarity
            )

            # Build context (concatenated chunks)
            context = "\n\n".join([
                result["content"]
                for result in results
            ])

            return {
                "results": results,
                "context": context,
                "error": None
            }

        except Exception as e:
            return {
                "results": [],
                "context": "",
                "error": str(e)
            }
