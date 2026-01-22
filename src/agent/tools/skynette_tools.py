"""
Skynette System Tools

Expose existing Skynette systems (RAG) as agent tools.
"""

import logging
import time
from typing import Optional

from src.agent.models.tool import ToolResult
from src.agent.registry.base_tool import AgentContext, BaseTool

logger = logging.getLogger(__name__)


class RAGQueryTool(BaseTool):
    """Query the Skynette RAG system for relevant context."""

    name = "rag_query"
    description = (
        "Search Skynette's knowledge base using RAG (Retrieval-Augmented Generation). "
        "Returns relevant documents and context for a query."
    )
    parameters_schema = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Natural language query to search the knowledge base",
            },
            "collection": {
                "type": "string",
                "description": "Collection name to search (default: searches all)",
            },
            "top_k": {
                "type": "integer",
                "description": "Number of results to return (default: 5)",
                "default": 5,
            },
            "min_score": {
                "type": "number",
                "description": "Minimum relevance score (0-1, default: 0.5)",
                "default": 0.5,
            },
        },
        "required": ["query"],
    }

    async def execute(self, params: dict, context: AgentContext) -> ToolResult:
        """Execute RAG query using existing RAG system."""
        start = time.perf_counter()

        query = params.get("query", "")
        collection = params.get("collection")
        top_k = params.get("top_k", 5)
        min_score = params.get("min_score", 0.5)

        if not query.strip():
            return ToolResult.failure_result(
                tool_call_id=context.session_id,
                error="Query cannot be empty",
                duration_ms=(time.perf_counter() - start) * 1000,
            )

        try:
            # Import RAG query node dynamically to handle cases where RAG is not configured
            from src.core.nodes.rag.query import QueryKnowledgeNode

            # Create node instance
            # Note: RAGService would be injected in production via dependency injection
            # For now, we attempt to get it from the app state or create a placeholder
            rag_service = await self._get_rag_service()

            if rag_service is None:
                # RAG system not initialized
                duration_ms = (time.perf_counter() - start) * 1000
                return ToolResult.success_result(
                    tool_call_id=context.session_id,
                    data={
                        "query": query,
                        "results": [],
                        "count": 0,
                        "message": "RAG system not initialized. No collections available.",
                    },
                    duration_ms=duration_ms,
                )

            node = QueryKnowledgeNode(rag_service=rag_service)

            # Build inputs for the node
            inputs = {
                "query": query,
                "collection_id": collection or "",  # Empty string for all collections
                "top_k": top_k,
                "min_similarity": min_score,
            }

            # Execute the node
            result = await node.execute(inputs)

            # Check for errors from the node
            if result.get("error"):
                duration_ms = (time.perf_counter() - start) * 1000
                return ToolResult.failure_result(
                    tool_call_id=context.session_id,
                    error=f"RAG query failed: {result['error']}",
                    duration_ms=duration_ms,
                )

            # Filter results by min_score and format
            raw_results = result.get("results", [])
            filtered_docs = []

            for doc in raw_results:
                score = doc.get("similarity", doc.get("score", 0))
                if score >= min_score:
                    filtered_docs.append({
                        "content": doc.get("content", ""),
                        "score": score,
                        "metadata": doc.get("metadata", {}),
                    })

            duration_ms = (time.perf_counter() - start) * 1000
            return ToolResult.success_result(
                tool_call_id=context.session_id,
                data={
                    "query": query,
                    "results": filtered_docs,
                    "count": len(filtered_docs),
                    "context": result.get("context", ""),
                },
                duration_ms=duration_ms,
            )

        except ImportError as e:
            duration_ms = (time.perf_counter() - start) * 1000
            return ToolResult.failure_result(
                tool_call_id=context.session_id,
                error=f"RAG module not available: {e}",
                duration_ms=duration_ms,
            )
        except Exception as e:
            logger.error(f"RAG query error: {e}")
            duration_ms = (time.perf_counter() - start) * 1000
            return ToolResult.failure_result(
                tool_call_id=context.session_id,
                error=f"RAG query failed: {e}",
                duration_ms=duration_ms,
            )

    async def _get_rag_service(self) -> Optional[object]:
        """
        Get RAG service instance.

        Returns None if RAG system is not initialized.
        """
        try:
            # Try to get from app state (if running in Flet context)
            # For now, check if RAG service is available via dynamic import
            from src.core.rag.service import RAGService

            # Check if ChromaDB is configured
            # RAGService requires ChromaDB to be available
            try:
                import chromadb
            except ImportError:
                logger.debug("ChromaDB not installed, RAG service unavailable")
                return None

            # Attempt to create service - it will fail if not configured
            # In production, this would be a singleton from app state
            return RAGService()

        except ImportError:
            logger.debug("RAG service module not available")
            return None
        except Exception as e:
            logger.debug(f"RAG service initialization failed: {e}")
            return None
