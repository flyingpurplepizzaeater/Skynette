"""
RAG Data Models

Pydantic models for RAG collections, documents, and chunks.
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional
from uuid import uuid4
from pydantic import BaseModel, Field, field_validator


class Collection(BaseModel):
    """Knowledge base collection configuration."""

    id: str = Field(default_factory=lambda: f"coll-{uuid4().hex[:12]}")
    name: str = Field(..., min_length=1, max_length=100)
    description: str = ""
    embedding_model: str = "local"  # "local", "openai", "cohere"
    chunk_size: int = 1024  # Target tokens per chunk
    chunk_overlap: int = 128  # Overlap tokens
    max_chunk_size: int = 2048  # Maximum tokens
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator('chunk_size')
    @classmethod
    def validate_chunk_size(cls, v):
        if not (256 <= v <= 4096):
            raise ValueError("chunk_size must be between 256 and 4096")
        return v

    @field_validator('chunk_overlap')
    @classmethod
    def validate_chunk_overlap(cls, v):
        if v < 0:
            raise ValueError("chunk_overlap must be non-negative")
        return v


class Document(BaseModel):
    """Document metadata for RAG indexing."""

    id: str = Field(default_factory=lambda: f"doc-{uuid4().hex[:12]}")
    collection_id: str
    source_path: str
    file_type: str  # "markdown", "text", "python", etc.
    file_hash: str  # SHA256 for change detection
    file_size: int = 0
    chunk_count: int = 0
    indexed_at: Optional[datetime] = None
    last_updated: Optional[datetime] = None
    status: str = "queued"  # "queued", "processing", "indexed", "failed"
    error: Optional[str] = None


class Chunk(BaseModel):
    """Document chunk with content and metadata."""

    id: str = Field(default_factory=lambda: f"chunk-{uuid4().hex[:12]}")
    document_id: str
    chunk_index: int
    content: str
    embedding_hash: Optional[str] = None  # For cache lookup
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
