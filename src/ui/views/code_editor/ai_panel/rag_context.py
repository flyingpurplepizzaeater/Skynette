# src/ui/views/code_editor/ai_panel/rag_context.py
"""
RAG Context Provider for AI Chat Panel

Provides relevant codebase context for AI chat interactions.
Integrates ProjectIndexer for lazy project indexing and context retrieval.
"""

import logging
from typing import TYPE_CHECKING

from src.rag.project_indexer import ProjectIndexer

if TYPE_CHECKING:
    from src.rag.chromadb_client import ChromaDBClient
    from src.rag.embeddings import EmbeddingManager

logger = logging.getLogger(__name__)


class RAGContextProvider:
    """Provides RAG-based code context for AI chat.

    Features:
    - Lazy project indexing on first query
    - Caches indexed projects to avoid re-indexing
    - Formats context for AI consumption
    - Returns sources for display in UI
    """

    def __init__(
        self,
        chromadb_client: "ChromaDBClient",
        embedding_manager: "EmbeddingManager",
    ):
        """Initialize the RAG context provider.

        Args:
            chromadb_client: ChromaDB client for vector storage.
            embedding_manager: EmbeddingManager for generating embeddings.
        """
        self.chromadb = chromadb_client
        self.embedding_manager = embedding_manager
        self._indexer = ProjectIndexer(chromadb_client, embedding_manager)
        self._indexed_projects: set[str] = set()
        self._indexing_in_progress: set[str] = set()

    async def ensure_indexed(self, project_root: str) -> dict | None:
        """Ensure a project is indexed.

        Indexes the project if not already indexed.
        Returns stats if indexing was performed, None if already indexed.

        Args:
            project_root: Root directory of the project.

        Returns:
            Index stats dict if indexing performed, None if already indexed.
        """
        if project_root in self._indexed_projects:
            return None

        if project_root in self._indexing_in_progress:
            # Another coroutine is already indexing this project
            return None

        try:
            self._indexing_in_progress.add(project_root)
            logger.info(f"Indexing project: {project_root}")
            stats = await self._indexer.index_project(project_root)
            self._indexed_projects.add(project_root)
            logger.info(
                f"Project indexed: {stats['indexed']} files, {stats['total_chunks']} chunks"
            )
            return stats
        except Exception as e:
            logger.error(f"Failed to index project {project_root}: {e}")
            raise
        finally:
            self._indexing_in_progress.discard(project_root)

    async def get_context(
        self,
        query: str,
        project_root: str | None,
        top_k: int = 5,
    ) -> tuple[str, list[dict]]:
        """Get relevant code context for a query.

        Args:
            query: User query to find context for.
            project_root: Root directory of the project, or None.
            top_k: Number of context chunks to retrieve.

        Returns:
            Tuple of (context_string, sources_list).
            context_string: Formatted context for AI prompt.
            sources_list: List of source dicts for UI display.
        """
        if not project_root:
            return ("", [])

        # Ensure project is indexed (lazy initialization)
        await self.ensure_indexed(project_root)

        # Query for relevant chunks
        try:
            results = await self._indexer.query_context(query, project_root, top_k=top_k)
        except Exception as e:
            logger.warning(f"RAG query failed: {e}")
            return ("", [])

        if not results:
            return ("", [])

        # Format context string for AI
        context_parts = ["## Relevant Code\n"]
        sources = []

        for result in results:
            source_path = result["source_path"]
            content = result["content"]
            language = result.get("language", "")
            similarity = result["similarity"]

            # Format for AI prompt
            context_parts.append(f"### {source_path}")
            context_parts.append(f"```{language}")
            context_parts.append(content)
            context_parts.append("```\n")

            # Track source for UI display
            sources.append(
                {
                    "path": source_path,
                    "snippet": content[:200] + ("..." if len(content) > 200 else ""),
                    "language": language,
                    "similarity": similarity,
                }
            )

        context_string = "\n".join(context_parts)
        return (context_string, sources)

    def is_indexed(self, project_root: str) -> bool:
        """Check if a project is already indexed.

        Args:
            project_root: Root directory of the project.

        Returns:
            True if project is indexed, False otherwise.
        """
        return project_root in self._indexed_projects

    def clear_index(self, project_root: str | None = None) -> None:
        """Clear index cache for a project or all projects.

        Args:
            project_root: Project to clear, or None to clear all.
        """
        if project_root:
            self._indexed_projects.discard(project_root)
            self._indexer.clear_cache()
        else:
            self._indexed_projects.clear()
            self._indexer.clear_cache()
