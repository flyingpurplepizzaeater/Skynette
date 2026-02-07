# src/rag/project_indexer.py
"""
Project Indexer

Indexes project files for RAG-based code context retrieval.
Supports incremental indexing via file hash comparison.
"""

import hashlib
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from src.rag.models import Chunk

if TYPE_CHECKING:
    from src.rag.chromadb_client import ChromaDBClient
    from src.rag.embeddings import EmbeddingManager

logger = logging.getLogger(__name__)


# Supported file extensions for indexing
SUPPORTED_EXTENSIONS = {
    ".py",
    ".js",
    ".ts",
    ".jsx",
    ".tsx",
    ".mjs",
    ".md",
    ".txt",
    ".json",
    ".yaml",
    ".yml",
    ".html",
    ".css",
    ".scss",
    ".sql",
    ".sh",
    ".bash",
    ".java",
    ".kt",
    ".go",
    ".rs",
    ".c",
    ".cpp",
    ".h",
    ".hpp",
    ".dart",
    ".swift",
    ".rb",
    ".php",
    ".vue",
    ".svelte",
}

# File size limits
MAX_FILE_SIZE_WARN = 50 * 1024  # 50KB - warn but skip
MAX_FILE_SIZE_REFUSE = 500 * 1024  # 500KB - refuse entirely


def _hash_path(path: str) -> str:
    """Generate a short hash for a file path.

    Args:
        path: File path to hash.

    Returns:
        12-character hex hash.
    """
    return hashlib.md5(path.encode()).hexdigest()[:12]


class ProjectIndexer:
    """Indexes project files for RAG-based code context retrieval.

    Features:
    - Incremental indexing (skips unchanged files)
    - Supports common programming languages
    - Chunking with overlap for context preservation
    - Respects file size limits
    """

    def __init__(
        self,
        chromadb_client: "ChromaDBClient",
        embedding_manager: "EmbeddingManager",
        chunk_size: int = 500,
        chunk_overlap: int = 50,
    ):
        """Initialize the project indexer.

        Args:
            chromadb_client: ChromaDB client for vector storage.
            embedding_manager: EmbeddingManager for generating embeddings.
            chunk_size: Target chunk size in characters.
            chunk_overlap: Overlap between chunks in characters.
        """
        self.chromadb = chromadb_client
        self.embedding_manager = embedding_manager
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # Track file hashes for incremental indexing
        self._file_hashes: dict[str, str] = {}

    async def index_project(self, project_root: str) -> dict:
        """Index all supported files in a project.

        Args:
            project_root: Root directory of the project.

        Returns:
            Dict with stats: indexed, skipped, errors, total_chunks
        """
        root_path = Path(project_root).resolve()
        if not root_path.exists():
            raise ValueError(f"Project root does not exist: {project_root}")

        # Generate collection ID from project root
        collection_id = f"project-{_hash_path(str(root_path))}"

        # Ensure collection exists
        await self.chromadb.create_collection(
            collection_id,
            embedding_dim=self.embedding_manager.embedding_dim,
            model_name=self.embedding_manager.model_name,
        )

        stats = {"indexed": 0, "skipped": 0, "errors": 0, "total_chunks": 0}

        # Iterate through all files
        for file_path in root_path.rglob("*"):
            # Skip directories
            if file_path.is_dir():
                continue

            # Skip hidden files and folders
            if any(part.startswith(".") for part in file_path.parts):
                continue

            # Skip unsupported extensions
            if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue

            # Check file size
            try:
                file_size = file_path.stat().st_size
            except OSError:
                stats["errors"] += 1
                continue

            if file_size > MAX_FILE_SIZE_WARN:
                logger.warning(f"Skipping large file ({file_size / 1024:.1f}KB): {file_path}")
                stats["skipped"] += 1
                continue

            # Check if file has changed
            file_hash = self._compute_hash(file_path)
            str_path = str(file_path)

            if str_path in self._file_hashes:
                if self._file_hashes[str_path] == file_hash:
                    # File unchanged, skip
                    stats["skipped"] += 1
                    continue

            # Index the file
            try:
                chunk_count = await self._index_file(collection_id, file_path)
                self._file_hashes[str_path] = file_hash
                stats["indexed"] += 1
                stats["total_chunks"] += chunk_count
            except Exception as e:
                logger.error(f"Error indexing {file_path}: {e}")
                stats["errors"] += 1

        return stats

    async def _index_file(self, collection_id: str, file_path: Path) -> int:
        """Index a single file.

        Args:
            collection_id: Target collection ID.
            file_path: Path to the file to index.

        Returns:
            Number of chunks created.
        """
        # Read file content
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            raise RuntimeError(f"Failed to read file: {e}") from e

        # Skip empty files
        if not content.strip():
            return 0

        # Delete existing chunks for this file (re-indexing)
        document_id = f"doc-{_hash_path(str(file_path))}"
        await self.chromadb.delete_chunks_by_document(collection_id, document_id)

        # Split into chunks
        chunks_text = self._split_into_chunks(content)
        if not chunks_text:
            return 0

        # Generate embeddings
        embeddings = await self.embedding_manager.embed_batch(chunks_text)

        # Determine language from extension
        language = file_path.suffix.lstrip(".") or "text"

        # Create Chunk objects
        chunks = []
        for i, text in enumerate(chunks_text):
            chunk = Chunk(
                document_id=document_id,
                chunk_index=i,
                content=text,
                metadata={
                    "source_path": str(file_path),
                    "language": language,
                    "chunk_index": i,
                    "total_chunks": len(chunks_text),
                },
            )
            chunks.append(chunk)

        # Add to ChromaDB
        await self.chromadb.add_chunks(
            collection_id,
            chunks,
            embeddings,
            model_name=self.embedding_manager.model_name,
        )

        return len(chunks)

    def _split_into_chunks(self, content: str) -> list[str]:
        """Split content into overlapping chunks.

        Args:
            content: Text content to split.

        Returns:
            List of chunk strings.
        """
        if len(content) <= self.chunk_size:
            return [content]

        chunks = []
        start = 0

        while start < len(content):
            # Calculate end position
            end = start + self.chunk_size

            # If not at the end, try to break at a natural boundary
            if end < len(content):
                # Look for newline to break at
                newline_pos = content.rfind("\n", start, end)
                if newline_pos > start + self.chunk_overlap:
                    end = newline_pos + 1

            chunk = content[start:end]
            chunks.append(chunk)

            # Move start with overlap
            start = end - self.chunk_overlap

            # Avoid infinite loop on small content
            if start >= len(content) or end >= len(content):
                break

        return chunks

    async def query_context(
        self,
        query: str,
        project_root: str,
        top_k: int = 5,
        min_similarity: float = 0.0,
    ) -> list[dict]:
        """Query for relevant code context.

        Args:
            query: User query to find relevant code for.
            project_root: Root directory of the project.
            top_k: Number of results to return.
            min_similarity: Minimum similarity threshold (0-1).

        Returns:
            List of dicts with content, source_path, similarity.
        """
        root_path = Path(project_root).resolve()
        collection_id = f"project-{_hash_path(str(root_path))}"

        # Check if collection exists
        if not await self.chromadb.collection_exists(collection_id):
            return []

        # Generate query embedding
        query_embedding = await self.embedding_manager.embed(query)

        # Query ChromaDB
        results = await self.chromadb.query(
            collection_id,
            query_embedding,
            top_k=top_k,
            min_similarity=min_similarity,
        )

        # Format results
        output = []
        for result in results:
            chunk = result["chunk"]
            output.append(
                {
                    "content": chunk.content,
                    "source_path": chunk.metadata.get("source_path", "unknown"),
                    "language": chunk.metadata.get("language", "text"),
                    "similarity": result["similarity"],
                }
            )

        return output

    def _compute_hash(self, file_path: Path) -> str:
        """Compute MD5 hash of file content for change detection.

        Args:
            file_path: Path to the file.

        Returns:
            Hex digest of the file content hash.
        """
        try:
            content = file_path.read_bytes()
            return hashlib.md5(content).hexdigest()
        except Exception:
            # Return empty hash on error - will trigger re-index
            return ""

    def clear_cache(self) -> None:
        """Clear the file hash cache, forcing full re-index next time."""
        self._file_hashes.clear()

    def get_collection_id(self, project_root: str) -> str:
        """Get the collection ID for a project.

        Args:
            project_root: Root directory of the project.

        Returns:
            Collection ID string.
        """
        root_path = Path(project_root).resolve()
        return f"project-{_hash_path(str(root_path))}"
