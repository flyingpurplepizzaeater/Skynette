"""Knowledge Bases UI models."""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any, Literal


@dataclass
class CollectionCardData:
    """UI representation of a RAG collection."""
    id: str
    name: str
    description: str
    document_count: int
    chunk_count: int
    last_updated: datetime
    storage_size_bytes: int
    embedding_model: str


@dataclass
class UploadProgress:
    """Tracks upload/processing progress."""
    total_files: int
    processed_files: int
    current_file: str
    status: Literal["pending", "processing", "completed", "failed"]
    errors: List['UploadError']

    @property
    def percentage(self) -> float:
        """Calculate completion percentage."""
        return (self.processed_files / self.total_files) * 100 if self.total_files > 0 else 0


@dataclass
class UploadError:
    """Individual file upload error."""
    file_path: str
    error_message: str
    error_type: Literal["unsupported", "permission", "corrupted", "embedding_failed"]


@dataclass
class QueryResultUI:
    """UI representation of a query result."""
    chunk_content: str
    source_file: str
    similarity: float
    metadata: Dict[str, Any]

    @classmethod
    def from_backend_result(cls, result: Dict[str, Any]) -> 'QueryResultUI':
        """Convert backend result to UI model with safe defaults."""
        metadata = result.get("metadata", {})
        return cls(
            chunk_content=result.get("content", ""),
            source_file=metadata.get("source_path", "unknown"),
            similarity=result.get("similarity", 0.0),
            metadata=metadata,
        )
