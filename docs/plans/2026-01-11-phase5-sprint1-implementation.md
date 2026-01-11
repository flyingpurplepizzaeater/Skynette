# Phase 5 Sprint 1: RAG Core (MVP) Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement basic RAG infrastructure with ChromaDB integration, local embeddings, markdown/text processing, and core workflow nodes for document ingestion and querying.

**Architecture:** Hybrid system with RAG background service managing ChromaDB for vector storage and SQLite for metadata. Workflow nodes (IngestDocument, QueryKnowledge) provide user-facing API. Local sentence-transformers model (all-MiniLM-L6-v2) for embeddings.

**Tech Stack:**
- ChromaDB 0.5.0+ (vector database)
- sentence-transformers (local embeddings)
- SQLite (metadata storage)
- Flet (UI components)
- pytest + pytest-asyncio (testing)

**Reference Design:** `docs/plans/2026-01-11-phase5-rag-integration-design.md`

---

## Task 1: RAG Data Models & Schema

Create Pydantic models and SQLite schema for RAG metadata.

**Files:**
- Create: `src/rag/__init__.py`
- Create: `src/rag/models.py`
- Create: `src/rag/schema.sql`
- Test: `tests/unit/test_rag_models.py`

### Step 1: Write the failing test for Collection model

```python
# tests/unit/test_rag_models.py
import pytest
from datetime import datetime
from src.rag.models import Collection, Document, Chunk


class TestCollection:
    """Test Collection data model."""

    def test_create_collection_with_defaults(self):
        """Collection should create with default values."""
        coll = Collection(
            name="test_collection",
            description="Test collection"
        )

        assert coll.id is not None
        assert coll.name == "test_collection"
        assert coll.embedding_model == "local"
        assert coll.chunk_size == 1024
        assert coll.chunk_overlap == 128
        assert isinstance(coll.created_at, datetime)

    def test_collection_validates_chunk_size(self):
        """Chunk size must be reasonable."""
        with pytest.raises(ValueError):
            Collection(name="test", chunk_size=50)  # Too small

        with pytest.raises(ValueError):
            Collection(name="test", chunk_size=10000)  # Too large


class TestDocument:
    """Test Document data model."""

    def test_create_document(self):
        """Document should store file metadata."""
        doc = Document(
            collection_id="coll-123",
            source_path="/path/to/file.md",
            file_type="markdown",
            file_hash="abc123"
        )

        assert doc.id is not None
        assert doc.status == "queued"
        assert doc.chunk_count == 0


class TestChunk:
    """Test Chunk data model."""

    def test_create_chunk(self):
        """Chunk should store content and metadata."""
        chunk = Chunk(
            document_id="doc-123",
            chunk_index=0,
            content="# Test Document\n\nContent here",
            metadata={"type": "section", "heading": "Test Document"}
        )

        assert chunk.id is not None
        assert chunk.chunk_index == 0
        assert "Test Document" in chunk.content
```

### Step 2: Run test to verify it fails

```bash
cd /c/Users/karlt/OneDrive/Desktop/Claude/skynette-repo/.worktrees/phase5-sprint1-rag-core
python -m pytest tests/unit/test_rag_models.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'src.rag'"

### Step 3: Implement data models

```python
# src/rag/__init__.py
"""RAG (Retrieval Augmented Generation) module."""

from src.rag.models import Collection, Document, Chunk

__all__ = ["Collection", "Document", "Chunk"]
```

```python
# src/rag/models.py
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
```

### Step 4: Run test to verify it passes

```bash
python -m pytest tests/unit/test_rag_models.py -v
```

Expected: PASS (all tests)

### Step 5: Create SQLite schema

```sql
-- src/rag/schema.sql

-- Collections table
CREATE TABLE IF NOT EXISTS rag_collections (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    embedding_model TEXT NOT NULL DEFAULT 'local',
    chunk_size INTEGER NOT NULL DEFAULT 1024,
    chunk_overlap INTEGER NOT NULL DEFAULT 128,
    max_chunk_size INTEGER NOT NULL DEFAULT 2048,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- Documents table
CREATE TABLE IF NOT EXISTS rag_documents (
    id TEXT PRIMARY KEY,
    collection_id TEXT NOT NULL,
    source_path TEXT NOT NULL,
    file_type TEXT NOT NULL,
    file_hash TEXT NOT NULL,
    file_size INTEGER DEFAULT 0,
    chunk_count INTEGER DEFAULT 0,
    indexed_at TEXT,
    last_updated TEXT,
    status TEXT NOT NULL DEFAULT 'queued',
    error TEXT,
    FOREIGN KEY (collection_id) REFERENCES rag_collections(id) ON DELETE CASCADE
);

-- Chunks table
CREATE TABLE IF NOT EXISTS rag_chunks (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding_hash TEXT,
    metadata TEXT,  -- JSON
    created_at TEXT NOT NULL,
    FOREIGN KEY (document_id) REFERENCES rag_documents(id) ON DELETE CASCADE
);

-- Indices
CREATE INDEX IF NOT EXISTS idx_documents_collection ON rag_documents(collection_id);
CREATE INDEX IF NOT EXISTS idx_documents_hash ON rag_documents(file_hash);
CREATE INDEX IF NOT EXISTS idx_documents_status ON rag_documents(status);
CREATE INDEX IF NOT EXISTS idx_chunks_document ON rag_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_chunks_embedding_hash ON rag_chunks(embedding_hash);
```

### Step 6: Commit Task 1

```bash
git add src/rag/ tests/unit/test_rag_models.py
git commit -m "feat(rag): add data models and SQLite schema

Implemented:
- Collection, Document, Chunk Pydantic models
- Field validation for chunk sizes
- SQLite schema with indices
- Unit tests for all models

Task 1 complete.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 2: RAG Storage Layer

Implement SQLite storage layer for RAG metadata.

**Files:**
- Create: `src/rag/storage.py`
- Test: `tests/unit/test_rag_storage.py`

### Step 1: Write the failing test for RAGStorage

```python
# tests/unit/test_rag_storage.py
import pytest
from pathlib import Path
from src.rag.storage import RAGStorage
from src.rag.models import Collection, Document, Chunk


class TestRAGStorage:
    """Test RAG metadata storage."""

    @pytest.fixture
    def storage(self, tmp_path):
        """Create temp storage."""
        return RAGStorage(str(tmp_path / "test.db"))

    def test_create_collection(self, storage):
        """Should create and retrieve collection."""
        coll = Collection(name="test", description="Test collection")

        storage.save_collection(coll)

        retrieved = storage.get_collection(coll.id)
        assert retrieved is not None
        assert retrieved.name == "test"

    def test_list_collections(self, storage):
        """Should list all collections."""
        coll1 = Collection(name="coll1")
        coll2 = Collection(name="coll2")

        storage.save_collection(coll1)
        storage.save_collection(coll2)

        collections = storage.list_collections()
        assert len(collections) == 2

    def test_delete_collection(self, storage):
        """Should delete collection and cascade documents."""
        coll = Collection(name="test")
        storage.save_collection(coll)

        doc = Document(
            collection_id=coll.id,
            source_path="/test.md",
            file_type="markdown",
            file_hash="abc123"
        )
        storage.save_document(doc)

        storage.delete_collection(coll.id)

        assert storage.get_collection(coll.id) is None
        assert storage.get_document(doc.id) is None  # Cascaded

    def test_save_document(self, storage):
        """Should save and retrieve document."""
        coll = Collection(name="test")
        storage.save_collection(coll)

        doc = Document(
            collection_id=coll.id,
            source_path="/path/to/file.md",
            file_type="markdown",
            file_hash="abc123def456"
        )

        storage.save_document(doc)

        retrieved = storage.get_document(doc.id)
        assert retrieved is not None
        assert retrieved.source_path == "/path/to/file.md"

    def test_save_chunk(self, storage):
        """Should save and retrieve chunk."""
        coll = Collection(name="test")
        storage.save_collection(coll)

        doc = Document(
            collection_id=coll.id,
            source_path="/test.md",
            file_type="markdown",
            file_hash="abc"
        )
        storage.save_document(doc)

        chunk = Chunk(
            document_id=doc.id,
            chunk_index=0,
            content="# Test\n\nContent here",
            metadata={"type": "section"}
        )

        storage.save_chunk(chunk)

        retrieved = storage.get_chunk(chunk.id)
        assert retrieved is not None
        assert retrieved.content == "# Test\n\nContent here"

    def test_get_document_chunks(self, storage):
        """Should get all chunks for a document."""
        coll = Collection(name="test")
        storage.save_collection(coll)

        doc = Document(
            collection_id=coll.id,
            source_path="/test.md",
            file_type="markdown",
            file_hash="abc"
        )
        storage.save_document(doc)

        # Create 3 chunks
        for i in range(3):
            chunk = Chunk(
                document_id=doc.id,
                chunk_index=i,
                content=f"Chunk {i}",
                metadata={}
            )
            storage.save_chunk(chunk)

        chunks = storage.get_document_chunks(doc.id)
        assert len(chunks) == 3
        assert chunks[0].chunk_index == 0
```

### Step 2: Run test to verify it fails

```bash
python -m pytest tests/unit/test_rag_storage.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'src.rag.storage'"

### Step 3: Implement RAGStorage

```python
# src/rag/storage.py
"""
RAG Storage Layer

SQLite-based storage for RAG metadata (collections, documents, chunks).
ChromaDB handles vector embeddings separately.
"""

import sqlite3
import json
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from src.rag.models import Collection, Document, Chunk


class RAGStorage:
    """SQLite storage for RAG metadata."""

    def __init__(self, db_path: str):
        """Initialize storage with database path."""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize database schema."""
        schema_path = Path(__file__).parent / "schema.sql"
        with open(schema_path, 'r') as f:
            schema = f.read()

        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(schema)

    # Collection methods

    def save_collection(self, collection: Collection) -> None:
        """Save or update collection."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT OR REPLACE INTO rag_collections
                (id, name, description, embedding_model, chunk_size, chunk_overlap,
                 max_chunk_size, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                collection.id,
                collection.name,
                collection.description,
                collection.embedding_model,
                collection.chunk_size,
                collection.chunk_overlap,
                collection.max_chunk_size,
                collection.created_at.isoformat(),
                collection.updated_at.isoformat()
            ))

    def get_collection(self, collection_id: str) -> Optional[Collection]:
        """Get collection by ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, name, description, embedding_model, chunk_size, chunk_overlap,
                       max_chunk_size, created_at, updated_at
                FROM rag_collections
                WHERE id = ?
            """, (collection_id,))

            row = cursor.fetchone()

        if not row:
            return None

        return Collection(
            id=row[0],
            name=row[1],
            description=row[2],
            embedding_model=row[3],
            chunk_size=row[4],
            chunk_overlap=row[5],
            max_chunk_size=row[6],
            created_at=datetime.fromisoformat(row[7]),
            updated_at=datetime.fromisoformat(row[8])
        )

    def list_collections(self) -> List[Collection]:
        """List all collections."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, name, description, embedding_model, chunk_size, chunk_overlap,
                       max_chunk_size, created_at, updated_at
                FROM rag_collections
                ORDER BY created_at DESC
            """)

            rows = cursor.fetchall()

        return [
            Collection(
                id=row[0],
                name=row[1],
                description=row[2],
                embedding_model=row[3],
                chunk_size=row[4],
                chunk_overlap=row[5],
                max_chunk_size=row[6],
                created_at=datetime.fromisoformat(row[7]),
                updated_at=datetime.fromisoformat(row[8])
            )
            for row in rows
        ]

    def delete_collection(self, collection_id: str) -> None:
        """Delete collection (cascades to documents/chunks)."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM rag_collections WHERE id = ?", (collection_id,))

    # Document methods

    def save_document(self, document: Document) -> None:
        """Save or update document."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT OR REPLACE INTO rag_documents
                (id, collection_id, source_path, file_type, file_hash, file_size,
                 chunk_count, indexed_at, last_updated, status, error)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                document.id,
                document.collection_id,
                document.source_path,
                document.file_type,
                document.file_hash,
                document.file_size,
                document.chunk_count,
                document.indexed_at.isoformat() if document.indexed_at else None,
                document.last_updated.isoformat() if document.last_updated else None,
                document.status,
                document.error
            ))

    def get_document(self, document_id: str) -> Optional[Document]:
        """Get document by ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, collection_id, source_path, file_type, file_hash, file_size,
                       chunk_count, indexed_at, last_updated, status, error
                FROM rag_documents
                WHERE id = ?
            """, (document_id,))

            row = cursor.fetchone()

        if not row:
            return None

        return Document(
            id=row[0],
            collection_id=row[1],
            source_path=row[2],
            file_type=row[3],
            file_hash=row[4],
            file_size=row[5],
            chunk_count=row[6],
            indexed_at=datetime.fromisoformat(row[7]) if row[7] else None,
            last_updated=datetime.fromisoformat(row[8]) if row[8] else None,
            status=row[9],
            error=row[10]
        )

    # Chunk methods

    def save_chunk(self, chunk: Chunk) -> None:
        """Save chunk."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT OR REPLACE INTO rag_chunks
                (id, document_id, chunk_index, content, embedding_hash, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                chunk.id,
                chunk.document_id,
                chunk.chunk_index,
                chunk.content,
                chunk.embedding_hash,
                json.dumps(chunk.metadata),
                chunk.created_at.isoformat()
            ))

    def get_chunk(self, chunk_id: str) -> Optional[Chunk]:
        """Get chunk by ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, document_id, chunk_index, content, embedding_hash, metadata, created_at
                FROM rag_chunks
                WHERE id = ?
            """, (chunk_id,))

            row = cursor.fetchone()

        if not row:
            return None

        return Chunk(
            id=row[0],
            document_id=row[1],
            chunk_index=row[2],
            content=row[3],
            embedding_hash=row[4],
            metadata=json.loads(row[5]) if row[5] else {},
            created_at=datetime.fromisoformat(row[6])
        )

    def get_document_chunks(self, document_id: str) -> List[Chunk]:
        """Get all chunks for a document."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, document_id, chunk_index, content, embedding_hash, metadata, created_at
                FROM rag_chunks
                WHERE document_id = ?
                ORDER BY chunk_index
            """, (document_id,))

            rows = cursor.fetchall()

        return [
            Chunk(
                id=row[0],
                document_id=row[1],
                chunk_index=row[2],
                content=row[3],
                embedding_hash=row[4],
                metadata=json.loads(row[5]) if row[5] else {},
                created_at=datetime.fromisoformat(row[6])
            )
            for row in rows
        ]
```

### Step 4: Run test to verify it passes

```bash
python -m pytest tests/unit/test_rag_storage.py -v
```

Expected: PASS (all tests)

### Step 5: Commit Task 2

```bash
git add src/rag/storage.py tests/unit/test_rag_storage.py
git commit -m "feat(rag): implement SQLite storage layer

Implemented:
- RAGStorage class for metadata persistence
- Collection CRUD operations
- Document CRUD operations
- Chunk storage and retrieval
- Cascade deletes for collections
- Full test coverage

Task 2 complete.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 3: Document Processor - Text/Markdown Chunking

Implement basic document processor with markdown/text chunking.

**Files:**
- Create: `src/rag/processor.py`
- Test: `tests/unit/test_rag_processor.py`

### Step 1: Write the failing test for DocumentProcessor

```python
# tests/unit/test_rag_processor.py
import pytest
from src.rag.processor import DocumentProcessor
from src.rag.models import Chunk


class TestDocumentProcessor:
    """Test document processing and chunking."""

    def test_process_markdown_file(self, tmp_path):
        """Should parse markdown file and create chunks."""
        processor = DocumentProcessor()

        # Create test markdown file
        md_file = tmp_path / "test.md"
        md_file.write_text("""# Title

Introduction paragraph.

## Section 1

Content for section 1.

## Section 2

Content for section 2.
""")

        chunks = processor.process_file(str(md_file), "markdown")

        assert len(chunks) > 0
        assert all(isinstance(c, Chunk) for c in chunks)
        assert all(c.content for c in chunks)

    def test_process_text_file(self, tmp_path):
        """Should parse text file and create chunks."""
        processor = DocumentProcessor()

        # Create test text file
        text_file = tmp_path / "test.txt"
        text_file.write_text("Line 1\nLine 2\nLine 3\n" * 100)

        chunks = processor.process_file(str(text_file), "text")

        assert len(chunks) > 0

    def test_chunk_text_by_tokens(self):
        """Should chunk text by token count."""
        processor = DocumentProcessor(chunk_size=50, chunk_overlap=10)

        # Long text
        text = " ".join([f"word{i}" for i in range(200)])

        chunks = processor.chunk_text(text)

        # Should create multiple chunks
        assert len(chunks) > 1

        # Each chunk should be roughly chunk_size tokens
        for chunk in chunks:
            token_count = processor.count_tokens(chunk.content)
            assert token_count <= 100  # max_chunk_size default

    def test_chunk_overlap(self):
        """Adjacent chunks should have overlap."""
        processor = DocumentProcessor(chunk_size=50, chunk_overlap=10)

        text = " ".join([f"word{i}" for i in range(200)])
        chunks = processor.chunk_text(text)

        # Check overlap between consecutive chunks
        for i in range(len(chunks) - 1):
            chunk1_end = chunks[i].content.split()[-10:]
            chunk2_start = chunks[i+1].content.split()[:10:]

            # Should have some word overlap
            overlap = set(chunk1_end) & set(chunk2_start)
            assert len(overlap) > 0

    def test_chunk_markdown_by_sections(self):
        """Should chunk markdown by headers."""
        processor = DocumentProcessor()

        markdown = """# Title

Intro text.

## Section 1

Content 1.

## Section 2

Content 2.
"""

        chunks = processor.chunk_markdown(markdown)

        # Should create chunks per section
        assert len(chunks) >= 2  # At least Title and sections

        # Chunks should contain headers
        assert any("Title" in c.content for c in chunks)
        assert any("Section 1" in c.content for c in chunks)

    def test_count_tokens(self):
        """Should estimate token count."""
        processor = DocumentProcessor()

        text = "This is a test sentence."

        token_count = processor.count_tokens(text)

        # Should be reasonable estimate (5-10 words ≈ 7-12 tokens)
        assert 5 <= token_count <= 15
```

### Step 2: Run test to verify it fails

```bash
python -m pytest tests/unit/test_rag_processor.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'src.rag.processor'"

### Step 3: Implement DocumentProcessor

```python
# src/rag/processor.py
"""
Document Processor

Handles file parsing and chunking for RAG indexing.
Sprint 1: Markdown and text files only.
"""

import re
from pathlib import Path
from typing import List
from src.rag.models import Chunk


class DocumentProcessor:
    """Process documents and create chunks."""

    def __init__(
        self,
        chunk_size: int = 1024,
        chunk_overlap: int = 128,
        max_chunk_size: int = 2048
    ):
        """Initialize processor with chunking parameters."""
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.max_chunk_size = max_chunk_size

    def process_file(self, file_path: str, file_type: str) -> List[Chunk]:
        """Process file and return chunks."""
        content = Path(file_path).read_text(encoding='utf-8')

        if file_type == "markdown":
            return self.chunk_markdown(content)
        elif file_type == "text":
            return self.chunk_text(content)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

    def chunk_markdown(self, content: str) -> List[Chunk]:
        """
        Chunk markdown by sections (headers).

        Strategy: Split on headers (## ) while preserving hierarchy.
        """
        chunks = []

        # Split by headers
        sections = re.split(r'(^#{1,6}\s+.+$)', content, flags=re.MULTILINE)

        current_section = []
        chunk_index = 0

        for i, section in enumerate(sections):
            if section.strip():
                current_section.append(section)

                # Check if we should create a chunk
                section_text = '\n'.join(current_section)
                token_count = self.count_tokens(section_text)

                if token_count >= self.chunk_size:
                    # Create chunk
                    chunk = Chunk(
                        document_id="",  # Will be set by caller
                        chunk_index=chunk_index,
                        content=section_text.strip(),
                        metadata={"type": "section"}
                    )
                    chunks.append(chunk)
                    chunk_index += 1

                    # Start new section with overlap
                    current_section = [section]

        # Add remaining content
        if current_section:
            section_text = '\n'.join(current_section)
            if section_text.strip():
                chunk = Chunk(
                    document_id="",
                    chunk_index=chunk_index,
                    content=section_text.strip(),
                    metadata={"type": "section"}
                )
                chunks.append(chunk)

        # If no chunks created (small document), create one
        if not chunks and content.strip():
            chunk = Chunk(
                document_id="",
                chunk_index=0,
                content=content.strip(),
                metadata={"type": "document"}
            )
            chunks.append(chunk)

        return chunks

    def chunk_text(self, content: str) -> List[Chunk]:
        """
        Chunk plain text by token count with overlap.

        Strategy: Split on sentences/paragraphs, group by token count.
        """
        # Split into sentences (simple regex)
        sentences = re.split(r'(?<=[.!?])\s+', content)

        chunks = []
        current_chunk = []
        current_tokens = 0
        chunk_index = 0

        for sentence in sentences:
            sentence_tokens = self.count_tokens(sentence)

            # Check if adding this sentence exceeds chunk size
            if current_tokens + sentence_tokens > self.chunk_size and current_chunk:
                # Create chunk
                chunk_text = ' '.join(current_chunk)
                chunk = Chunk(
                    document_id="",
                    chunk_index=chunk_index,
                    content=chunk_text,
                    metadata={"type": "text"}
                )
                chunks.append(chunk)
                chunk_index += 1

                # Start new chunk with overlap
                overlap_tokens = self.chunk_overlap
                overlap_sentences = []
                for s in reversed(current_chunk):
                    overlap_tokens -= self.count_tokens(s)
                    if overlap_tokens < 0:
                        break
                    overlap_sentences.insert(0, s)

                current_chunk = overlap_sentences
                current_tokens = sum(self.count_tokens(s) for s in current_chunk)

            current_chunk.append(sentence)
            current_tokens += sentence_tokens

            # Enforce max chunk size
            if current_tokens >= self.max_chunk_size:
                chunk_text = ' '.join(current_chunk)
                chunk = Chunk(
                    document_id="",
                    chunk_index=chunk_index,
                    content=chunk_text,
                    metadata={"type": "text"}
                )
                chunks.append(chunk)
                chunk_index += 1

                current_chunk = []
                current_tokens = 0

        # Add remaining content
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunk = Chunk(
                document_id="",
                chunk_index=chunk_index,
                content=chunk_text,
                metadata={"type": "text"}
            )
            chunks.append(chunk)

        return chunks

    def count_tokens(self, text: str) -> int:
        """
        Estimate token count.

        Sprint 1: Simple word-based estimation.
        Future: Use tiktoken for accurate counts.
        """
        # Simple estimation: ~1.3 tokens per word
        words = len(text.split())
        return int(words * 1.3)
```

### Step 4: Run test to verify it passes

```bash
python -m pytest tests/unit/test_rag_processor.py -v
```

Expected: PASS (all tests)

### Step 5: Commit Task 3

```bash
git add src/rag/processor.py tests/unit/test_rag_processor.py
git commit -m "feat(rag): implement document processor for text/markdown

Implemented:
- DocumentProcessor class with configurable chunking
- Markdown chunking by headers/sections
- Text chunking by sentences with token limits
- Overlap between chunks for context preservation
- Simple token counting (word-based estimation)
- Full test coverage

Task 3 complete.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 4: Embedding Manager - Local Model

Implement embedding manager with local sentence-transformers model.

**Files:**
- Create: `src/rag/embeddings.py`
- Test: `tests/unit/test_rag_embeddings.py`

### Step 1: Write the failing test for EmbeddingManager

```python
# tests/unit/test_rag_embeddings.py
import pytest
from src.rag.embeddings import EmbeddingManager


class TestEmbeddingManager:
    """Test embedding generation."""

    @pytest.mark.asyncio
    async def test_load_local_model(self):
        """Should load local embedding model."""
        manager = EmbeddingManager(model="all-MiniLM-L6-v2")

        await manager.initialize()

        assert manager.is_initialized
        assert manager.model_name == "all-MiniLM-L6-v2"
        assert manager.embedding_dim == 384

    @pytest.mark.asyncio
    async def test_generate_embedding(self):
        """Should generate embedding vector."""
        manager = EmbeddingManager(model="all-MiniLM-L6-v2")
        await manager.initialize()

        text = "This is a test document."

        embedding = await manager.embed(text)

        # Should be correct dimension
        assert len(embedding) == 384

        # Should be floats
        assert all(isinstance(x, float) for x in embedding)

        # Should be normalized (unit vector for cosine similarity)
        import numpy as np
        magnitude = np.linalg.norm(embedding)
        assert 0.99 < magnitude < 1.01  # Approximately 1.0

    @pytest.mark.asyncio
    async def test_batch_embeddings(self):
        """Should generate embeddings for multiple texts."""
        manager = EmbeddingManager(model="all-MiniLM-L6-v2")
        await manager.initialize()

        texts = [
            "First document",
            "Second document",
            "Third document"
        ]

        embeddings = await manager.embed_batch(texts)

        assert len(embeddings) == 3
        assert all(len(emb) == 384 for emb in embeddings)

    @pytest.mark.asyncio
    async def test_similar_texts_have_high_similarity(self):
        """Similar texts should have similar embeddings."""
        manager = EmbeddingManager(model="all-MiniLM-L6-v2")
        await manager.initialize()

        text1 = "The quick brown fox jumps over the lazy dog"
        text2 = "A fast brown fox leaps over a sleepy dog"
        text3 = "Python is a programming language"

        emb1 = await manager.embed(text1)
        emb2 = await manager.embed(text2)
        emb3 = await manager.embed(text3)

        # Calculate cosine similarity
        import numpy as np
        sim_1_2 = np.dot(emb1, emb2)
        sim_1_3 = np.dot(emb1, emb3)

        # Similar texts should have higher similarity
        assert sim_1_2 > sim_1_3
        assert sim_1_2 > 0.7  # High similarity
```

### Step 2: Run test to verify it fails

```bash
python -m pytest tests/unit/test_rag_embeddings.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'src.rag.embeddings'"

### Step 3: Implement EmbeddingManager

```python
# src/rag/embeddings.py
"""
Embedding Manager

Manages embedding generation using local sentence-transformers model.
Sprint 1: Local model only (all-MiniLM-L6-v2).
"""

import asyncio
from typing import List
from sentence_transformers import SentenceTransformer


class EmbeddingManager:
    """Manage embedding generation."""

    def __init__(self, model: str = "all-MiniLM-L6-v2"):
        """Initialize embedding manager."""
        self.model_name = model
        self.model = None
        self.is_initialized = False
        self.embedding_dim = 384  # For all-MiniLM-L6-v2

    async def initialize(self):
        """Load embedding model."""
        if self.is_initialized:
            return

        # Load model in thread pool (blocking I/O)
        loop = asyncio.get_event_loop()
        self.model = await loop.run_in_executor(
            None,
            lambda: SentenceTransformer(self.model_name)
        )

        self.is_initialized = True

    async def embed(self, text: str) -> List[float]:
        """
        Generate embedding for single text.

        Returns:
            List[float]: Embedding vector (384 dimensions for all-MiniLM-L6-v2)
        """
        if not self.is_initialized:
            await self.initialize()

        # Run in thread pool (CPU-bound)
        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(
            None,
            lambda: self.model.encode(text, normalize_embeddings=True)
        )

        return embedding.tolist()

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.

        More efficient than calling embed() multiple times.

        Args:
            texts: List of text strings

        Returns:
            List[List[float]]: List of embedding vectors
        """
        if not self.is_initialized:
            await self.initialize()

        # Run in thread pool
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            None,
            lambda: self.model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        )

        return [emb.tolist() for emb in embeddings]

    def shutdown(self):
        """Cleanup resources."""
        self.model = None
        self.is_initialized = False
```

### Step 4: Run test to verify it passes

```bash
python -m pytest tests/unit/test_rag_embeddings.py -v
```

Expected: PASS (all tests) - Note: This will download the model (~80MB) on first run

### Step 5: Commit Task 4

```bash
git add src/rag/embeddings.py tests/unit/test_rag_embeddings.py
git commit -m "feat(rag): implement embedding manager with local model

Implemented:
- EmbeddingManager class using sentence-transformers
- Local model support (all-MiniLM-L6-v2)
- Async embedding generation with thread pool
- Batch embedding for efficiency
- Normalized embeddings for cosine similarity
- Full test coverage

Task 4 complete.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 5: ChromaDB Client

Implement ChromaDB client for vector storage and retrieval.

**Files:**
- Create: `src/rag/chromadb_client.py`
- Test: `tests/unit/test_chromadb_client.py`

### Step 1: Write the failing test for ChromaDBClient

```python
# tests/unit/test_chromadb_client.py
import pytest
from src.rag.chromadb_client import ChromaDBClient
from src.rag.models import Chunk


class TestChromaDBClient:
    """Test ChromaDB vector database operations."""

    @pytest.fixture
    def client(self, tmp_path):
        """Create temp ChromaDB client."""
        return ChromaDBClient(str(tmp_path / "chromadb"))

    @pytest.mark.asyncio
    async def test_create_collection(self, client):
        """Should create ChromaDB collection."""
        await client.initialize()

        collection_id = "test-collection"
        await client.create_collection(collection_id, embedding_dim=384)

        assert await client.collection_exists(collection_id)

    @pytest.mark.asyncio
    async def test_add_chunks(self, client):
        """Should add chunks with embeddings."""
        await client.initialize()

        collection_id = "test-collection"
        await client.create_collection(collection_id, embedding_dim=384)

        # Create test chunks with embeddings
        chunks = [
            Chunk(
                id="chunk-1",
                document_id="doc-1",
                chunk_index=0,
                content="Python is a programming language",
                metadata={"type": "text"}
            ),
            Chunk(
                id="chunk-2",
                document_id="doc-1",
                chunk_index=1,
                content="JavaScript is also a programming language",
                metadata={"type": "text"}
            )
        ]

        # Mock embeddings
        embeddings = [
            [0.1] * 384,
            [0.2] * 384
        ]

        await client.add_chunks(collection_id, chunks, embeddings)

        # Verify count
        count = await client.get_count(collection_id)
        assert count == 2

    @pytest.mark.asyncio
    async def test_query_similar(self, client):
        """Should query for similar chunks."""
        await client.initialize()

        collection_id = "test-collection"
        await client.create_collection(collection_id, embedding_dim=384)

        # Add chunks
        chunks = [
            Chunk(id=f"chunk-{i}", document_id="doc-1", chunk_index=i, content=f"Text {i}")
            for i in range(5)
        ]
        embeddings = [[i * 0.1] * 384 for i in range(5)]

        await client.add_chunks(collection_id, chunks, embeddings)

        # Query
        query_embedding = [0.2] * 384
        results = await client.query(collection_id, query_embedding, top_k=3)

        # Should return top 3
        assert len(results) == 3

        # Each result should have chunk and similarity
        for result in results:
            assert "chunk" in result
            assert "similarity" in result
            assert 0 <= result["similarity"] <= 1

    @pytest.mark.asyncio
    async def test_delete_collection(self, client):
        """Should delete collection."""
        await client.initialize()

        collection_id = "test-collection"
        await client.create_collection(collection_id, embedding_dim=384)

        assert await client.collection_exists(collection_id)

        await client.delete_collection(collection_id)

        assert not await client.collection_exists(collection_id)

    @pytest.mark.asyncio
    async def test_delete_chunks_by_document(self, client):
        """Should delete all chunks for a document."""
        await client.initialize()

        collection_id = "test-collection"
        await client.create_collection(collection_id, embedding_dim=384)

        # Add chunks from 2 documents
        chunks = [
            Chunk(id="chunk-1", document_id="doc-1", chunk_index=0, content="Text 1"),
            Chunk(id="chunk-2", document_id="doc-1", chunk_index=1, content="Text 2"),
            Chunk(id="chunk-3", document_id="doc-2", chunk_index=0, content="Text 3"),
        ]
        embeddings = [[0.1] * 384, [0.2] * 384, [0.3] * 384]

        await client.add_chunks(collection_id, chunks, embeddings)

        # Delete doc-1 chunks
        await client.delete_chunks_by_document(collection_id, "doc-1")

        # Should only have doc-2 chunk
        count = await client.get_count(collection_id)
        assert count == 1
```

### Step 2: Run test to verify it fails

```bash
python -m pytest tests/unit/test_chromadb_client.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'src.rag.chromadb_client'"

### Step 3: Implement ChromaDBClient

```python
# src/rag/chromadb_client.py
"""
ChromaDB Client

Wrapper for ChromaDB vector database operations.
"""

import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any
from pathlib import Path

from src.rag.models import Chunk


class ChromaDBClient:
    """ChromaDB client for vector storage."""

    def __init__(self, storage_path: str):
        """Initialize ChromaDB client."""
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.client = None
        self.collections = {}  # Cache of collection objects

    async def initialize(self):
        """Initialize ChromaDB client."""
        if self.client:
            return

        # Create persistent client
        self.client = chromadb.PersistentClient(
            path=str(self.storage_path),
            settings=Settings(anonymized_telemetry=False)
        )

    async def create_collection(
        self,
        collection_id: str,
        embedding_dim: int = 384
    ):
        """Create new collection."""
        if not self.client:
            await self.initialize()

        # Create or get collection
        collection = self.client.get_or_create_collection(
            name=collection_id,
            metadata={"embedding_dim": embedding_dim}
        )

        self.collections[collection_id] = collection

    async def collection_exists(self, collection_id: str) -> bool:
        """Check if collection exists."""
        if not self.client:
            await self.initialize()

        try:
            self.client.get_collection(collection_id)
            return True
        except Exception:
            return False

    async def delete_collection(self, collection_id: str):
        """Delete collection."""
        if not self.client:
            await self.initialize()

        self.client.delete_collection(collection_id)

        if collection_id in self.collections:
            del self.collections[collection_id]

    async def add_chunks(
        self,
        collection_id: str,
        chunks: List[Chunk],
        embeddings: List[List[float]]
    ):
        """Add chunks with embeddings to collection."""
        if collection_id not in self.collections:
            collection = self.client.get_collection(collection_id)
            self.collections[collection_id] = collection
        else:
            collection = self.collections[collection_id]

        # Prepare data
        ids = [chunk.id for chunk in chunks]
        documents = [chunk.content for chunk in chunks]
        metadatas = [
            {
                "document_id": chunk.document_id,
                "chunk_index": chunk.chunk_index,
                **chunk.metadata
            }
            for chunk in chunks
        ]

        # Add to collection
        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )

    async def query(
        self,
        collection_id: str,
        query_embedding: List[float],
        top_k: int = 5,
        min_similarity: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Query for similar chunks.

        Returns:
            List of dicts with 'chunk' (Chunk object) and 'similarity' (float)
        """
        if collection_id not in self.collections:
            collection = self.client.get_collection(collection_id)
            self.collections[collection_id] = collection
        else:
            collection = self.collections[collection_id]

        # Query collection
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )

        # Parse results
        output = []
        if results and results['ids'] and results['ids'][0]:
            for i, chunk_id in enumerate(results['ids'][0]):
                # Calculate similarity from distance
                # ChromaDB returns L2 distance, convert to cosine similarity
                distance = results['distances'][0][i]
                similarity = 1 / (1 + distance)  # Simple conversion

                # Filter by min_similarity
                if similarity < min_similarity:
                    continue

                # Reconstruct chunk
                chunk = Chunk(
                    id=chunk_id,
                    document_id=results['metadatas'][0][i]['document_id'],
                    chunk_index=results['metadatas'][0][i]['chunk_index'],
                    content=results['documents'][0][i],
                    metadata=results['metadatas'][0][i]
                )

                output.append({
                    "chunk": chunk,
                    "similarity": similarity
                })

        return output

    async def get_count(self, collection_id: str) -> int:
        """Get number of chunks in collection."""
        if collection_id not in self.collections:
            collection = self.client.get_collection(collection_id)
            self.collections[collection_id] = collection
        else:
            collection = self.collections[collection_id]

        return collection.count()

    async def delete_chunks_by_document(
        self,
        collection_id: str,
        document_id: str
    ):
        """Delete all chunks for a document."""
        if collection_id not in self.collections:
            collection = self.client.get_collection(collection_id)
            self.collections[collection_id] = collection
        else:
            collection = self.collections[collection_id]

        # Query for all chunks from this document
        results = collection.get(
            where={"document_id": document_id}
        )

        if results and results['ids']:
            # Delete by IDs
            collection.delete(ids=results['ids'])
```

### Step 4: Run test to verify it passes

```bash
python -m pytest tests/unit/test_chromadb_client.py -v
```

Expected: PASS (all tests)

### Step 5: Commit Task 5

```bash
git add src/rag/chromadb_client.py tests/unit/test_chromadb_client.py
git commit -m "feat(rag): implement ChromaDB client for vector storage

Implemented:
- ChromaDBClient wrapper for ChromaDB operations
- Collection management (create, delete, exists)
- Chunk storage with embeddings
- Similarity search with configurable top_k
- Document-based chunk deletion
- Full test coverage

Task 5 complete.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 6: RAG Service - Core Integration

Implement RAG service that orchestrates storage, processing, embeddings, and ChromaDB.

**Files:**
- Create: `src/rag/service.py`
- Test: `tests/unit/test_rag_service.py`

### Step 1: Write the failing test for RAGService

```python
# tests/unit/test_rag_service.py
import pytest
from pathlib import Path
from src.rag.service import RAGService
from src.rag.models import Collection


class TestRAGService:
    """Test RAG service integration."""

    @pytest.fixture
    async def service(self, tmp_path):
        """Create temp RAG service."""
        service = RAGService(storage_path=str(tmp_path))
        await service.initialize()
        return service

    @pytest.mark.asyncio
    async def test_create_collection(self, service):
        """Should create collection."""
        coll_id = await service.create_collection(
            name="test_collection",
            description="Test"
        )

        assert coll_id is not None

        coll = service.storage.get_collection(coll_id)
        assert coll.name == "test_collection"

    @pytest.mark.asyncio
    async def test_ingest_document(self, service, tmp_path):
        """Should ingest markdown document."""
        # Create collection
        coll_id = await service.create_collection(name="test")

        # Create test file
        md_file = tmp_path / "test.md"
        md_file.write_text("""# Test Document

This is a test document for ingestion.

## Section 1

Content for section 1.
""")

        # Ingest
        result = await service.ingest_document(
            file_path=str(md_file),
            collection_id=coll_id
        )

        assert result["status"] == "success"
        assert result["chunks_created"] > 0

        # Verify document saved
        doc = service.storage.get_document(result["document_id"])
        assert doc is not None
        assert doc.status == "indexed"

    @pytest.mark.asyncio
    async def test_query_collection(self, service, tmp_path):
        """Should query and return similar chunks."""
        # Create collection
        coll_id = await service.create_collection(name="test")

        # Ingest document
        md_file = tmp_path / "test.md"
        md_file.write_text("""# Python Programming

Python is a high-level programming language.

## Features

Python supports multiple programming paradigms.
""")

        await service.ingest_document(str(md_file), coll_id)

        # Query
        results = await service.query(
            query="What is Python?",
            collection_id=coll_id,
            top_k=3
        )

        assert len(results) > 0
        assert "Python" in results[0]["content"]
        assert "similarity" in results[0]

    @pytest.mark.asyncio
    async def test_delete_document(self, service, tmp_path):
        """Should delete document and chunks."""
        # Create collection
        coll_id = await service.create_collection(name="test")

        # Ingest document
        md_file = tmp_path / "test.md"
        md_file.write_text("# Test\n\nContent")

        result = await service.ingest_document(str(md_file), coll_id)
        doc_id = result["document_id"]

        # Delete
        await service.delete_document(doc_id, coll_id)

        # Verify deleted
        doc = service.storage.get_document(doc_id)
        assert doc is None

    @pytest.mark.asyncio
    async def test_get_collection_stats(self, service, tmp_path):
        """Should return collection statistics."""
        # Create collection
        coll_id = await service.create_collection(name="test")

        # Ingest document
        md_file = tmp_path / "test.md"
        md_file.write_text("# Test\n\nContent " * 100)

        await service.ingest_document(str(md_file), coll_id)

        # Get stats
        stats = await service.get_collection_stats(coll_id)

        assert stats["document_count"] == 1
        assert stats["chunk_count"] > 0
```

### Step 2: Run test to verify it fails

```bash
python -m pytest tests/unit/test_rag_service.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'src.rag.service'"

### Step 3: Implement RAGService

```python
# src/rag/service.py
"""
RAG Service

Main service orchestrating RAG operations:
- Document ingestion with chunking and embedding
- Semantic search
- Collection management
"""

import hashlib
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime, timezone

from src.rag.storage import RAGStorage
from src.rag.processor import DocumentProcessor
from src.rag.embeddings import EmbeddingManager
from src.rag.chromadb_client import ChromaDBClient
from src.rag.models import Collection, Document


class RAGService:
    """Main RAG service."""

    def __init__(self, storage_path: str):
        """Initialize RAG service."""
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Initialize components
        db_path = self.storage_path / "rag.db"
        chroma_path = self.storage_path / "chromadb"

        self.storage = RAGStorage(str(db_path))
        self.processor = DocumentProcessor()
        self.embedding_manager = EmbeddingManager()
        self.chromadb = ChromaDBClient(str(chroma_path))

        self.is_initialized = False

    async def initialize(self):
        """Initialize service components."""
        if self.is_initialized:
            return

        await self.chromadb.initialize()
        await self.embedding_manager.initialize()

        self.is_initialized = True

    async def create_collection(
        self,
        name: str,
        description: str = "",
        chunk_size: int = 1024,
        chunk_overlap: int = 128
    ) -> str:
        """
        Create new collection.

        Returns:
            str: Collection ID
        """
        collection = Collection(
            name=name,
            description=description,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )

        # Save to metadata storage
        self.storage.save_collection(collection)

        # Create ChromaDB collection
        await self.chromadb.create_collection(
            collection.id,
            embedding_dim=self.embedding_manager.embedding_dim
        )

        return collection.id

    async def ingest_document(
        self,
        file_path: str,
        collection_id: str
    ) -> Dict[str, Any]:
        """
        Ingest document into collection.

        Args:
            file_path: Path to document
            collection_id: Target collection ID

        Returns:
            Dict with status, document_id, chunks_created
        """
        try:
            # Get collection config
            collection = self.storage.get_collection(collection_id)
            if not collection:
                raise ValueError(f"Collection not found: {collection_id}")

            # Compute file hash
            file_path_obj = Path(file_path)
            file_hash = self._compute_file_hash(file_path)

            # Determine file type
            file_type = self._detect_file_type(file_path)

            # Create document record
            document = Document(
                collection_id=collection_id,
                source_path=str(file_path_obj),
                file_type=file_type,
                file_hash=file_hash,
                file_size=file_path_obj.stat().st_size,
                status="processing"
            )
            self.storage.save_document(document)

            # Process file into chunks
            self.processor.chunk_size = collection.chunk_size
            self.processor.chunk_overlap = collection.chunk_overlap

            chunks = self.processor.process_file(file_path, file_type)

            # Set document_id on chunks
            for chunk in chunks:
                chunk.document_id = document.id

            # Generate embeddings
            chunk_texts = [chunk.content for chunk in chunks]
            embeddings = await self.embedding_manager.embed_batch(chunk_texts)

            # Store in ChromaDB
            await self.chromadb.add_chunks(collection_id, chunks, embeddings)

            # Save chunks to metadata storage
            for chunk in chunks:
                self.storage.save_chunk(chunk)

            # Update document status
            document.status = "indexed"
            document.chunk_count = len(chunks)
            document.indexed_at = datetime.now(timezone.utc)
            document.last_updated = datetime.now(timezone.utc)
            self.storage.save_document(document)

            return {
                "status": "success",
                "document_id": document.id,
                "chunks_created": len(chunks)
            }

        except Exception as e:
            # Update document status to failed
            if 'document' in locals():
                document.status = "failed"
                document.error = str(e)
                self.storage.save_document(document)

            return {
                "status": "error",
                "error": str(e)
            }

    async def query(
        self,
        query: str,
        collection_id: str,
        top_k: int = 5,
        min_similarity: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Query collection for similar chunks.

        Args:
            query: Query text
            collection_id: Collection to search
            top_k: Number of results to return
            min_similarity: Minimum similarity threshold

        Returns:
            List of dicts with 'content', 'similarity', 'metadata'
        """
        # Generate query embedding
        query_embedding = await self.embedding_manager.embed(query)

        # Query ChromaDB
        results = await self.chromadb.query(
            collection_id,
            query_embedding,
            top_k=top_k,
            min_similarity=min_similarity
        )

        # Format results
        output = []
        for result in results:
            chunk = result["chunk"]
            output.append({
                "chunk_id": chunk.id,
                "content": chunk.content,
                "similarity": result["similarity"],
                "metadata": chunk.metadata
            })

        return output

    async def delete_document(
        self,
        document_id: str,
        collection_id: str
    ):
        """Delete document and all its chunks."""
        # Delete from ChromaDB
        await self.chromadb.delete_chunks_by_document(collection_id, document_id)

        # Delete from metadata storage (chunks cascade)
        doc = self.storage.get_document(document_id)
        if doc:
            # Delete chunks first
            chunks = self.storage.get_document_chunks(document_id)
            # Note: SQLite cascade should handle this, but explicit is safer

            # Delete document
            with self.storage.db_path.parent.joinpath(self.storage.db_path).open() as conn:
                import sqlite3
                cursor = sqlite3.connect(str(self.storage.db_path)).cursor()
                cursor.execute("DELETE FROM rag_documents WHERE id = ?", (document_id,))
                cursor.connection.commit()

    async def get_collection_stats(self, collection_id: str) -> Dict[str, Any]:
        """Get collection statistics."""
        # Get documents
        import sqlite3
        with sqlite3.connect(str(self.storage.db_path)) as conn:
            cursor = conn.cursor()

            # Count documents
            cursor.execute(
                "SELECT COUNT(*) FROM rag_documents WHERE collection_id = ?",
                (collection_id,)
            )
            doc_count = cursor.fetchone()[0]

            # Count chunks
            cursor.execute(
                "SELECT SUM(chunk_count) FROM rag_documents WHERE collection_id = ?",
                (collection_id,)
            )
            chunk_count = cursor.fetchone()[0] or 0

        return {
            "document_count": doc_count,
            "chunk_count": chunk_count
        }

    def _compute_file_hash(self, file_path: str) -> str:
        """Compute SHA256 hash of file."""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def _detect_file_type(self, file_path: str) -> str:
        """Detect file type from extension."""
        ext = Path(file_path).suffix.lower()

        type_map = {
            ".md": "markdown",
            ".markdown": "markdown",
            ".txt": "text",
        }

        return type_map.get(ext, "text")
```

### Step 4: Run test to verify it passes

```bash
python -m pytest tests/unit/test_rag_service.py -v
```

Expected: PASS (all tests)

### Step 5: Commit Task 6

```bash
git add src/rag/service.py tests/unit/test_rag_service.py
git commit -m "feat(rag): implement RAG service core integration

Implemented:
- RAGService orchestrating all RAG components
- Collection management (create, stats)
- Document ingestion pipeline (parse, chunk, embed, store)
- Semantic search with embeddings
- Document deletion
- File hash computation for change detection
- Error handling with status tracking
- Full test coverage

Task 6 complete.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 7: IngestDocumentNode - Workflow Integration

Implement IngestDocument workflow node.

**Files:**
- Create: `src/core/nodes/rag/__init__.py`
- Create: `src/core/nodes/rag/ingest.py`
- Test: `tests/unit/test_rag_ingest_node.py`

### Step 1: Write the failing test for IngestDocumentNode

```python
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
```

### Step 2: Run test to verify it fails

```bash
python -m pytest tests/unit/test_rag_ingest_node.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'src.core.nodes.rag'"

### Step 3: Implement IngestDocumentNode

```python
# src/core/nodes/rag/__init__.py
"""RAG workflow nodes."""

from src.core.nodes.rag.ingest import IngestDocumentNode

__all__ = ["IngestDocumentNode"]
```

```python
# src/core/nodes/rag/ingest.py
"""
Ingest Document Node

Workflow node for ingesting documents into RAG collections.
"""

from typing import Any, Dict
from src.core.nodes.base import BaseNode, NodeField, FieldType


class IngestDocumentNode(BaseNode):
    """
    Ingest document into RAG collection.

    Parses document, creates chunks, generates embeddings, and stores in ChromaDB.
    """

    type = "rag-ingest-document"
    name = "Ingest Document"
    category = "RAG"
    description = "Index document for semantic search"
    icon = "upload_file"
    color = "#7C3AED"  # Purple (RAG category color)

    inputs = [
        NodeField(
            name="file_path",
            label="File Path",
            type=FieldType.FILE,
            required=True,
            description="Path to document to ingest (markdown, text)"
        ),
        NodeField(
            name="collection_id",
            label="Collection ID",
            type=FieldType.STRING,
            required=True,
            description="Target collection ID"
        ),
    ]

    outputs = [
        NodeField(
            name="document_id",
            label="Document ID",
            type=FieldType.STRING,
            description="ID of ingested document"
        ),
        NodeField(
            name="chunks_created",
            label="Chunks Created",
            type=FieldType.NUMBER,
            description="Number of chunks created"
        ),
        NodeField(
            name="status",
            label="Status",
            type=FieldType.STRING,
            description="Ingestion status (success/error)"
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
        """Execute document ingestion."""
        try:
            file_path = inputs["file_path"]
            collection_id = inputs["collection_id"]

            # Ingest document
            result = await self.rag_service.ingest_document(
                file_path=file_path,
                collection_id=collection_id
            )

            if result["status"] == "success":
                return {
                    "document_id": result["document_id"],
                    "chunks_created": result["chunks_created"],
                    "status": "success",
                    "error": None
                }
            else:
                return {
                    "document_id": None,
                    "chunks_created": 0,
                    "status": "error",
                    "error": result.get("error", "Unknown error")
                }

        except Exception as e:
            return {
                "document_id": None,
                "chunks_created": 0,
                "status": "error",
                "error": str(e)
            }
```

### Step 4: Run test to verify it passes

```bash
python -m pytest tests/unit/test_rag_ingest_node.py -v
```

Expected: PASS (all tests)

### Step 5: Commit Task 7

```bash
git add src/core/nodes/rag/ tests/unit/test_rag_ingest_node.py
git commit -m "feat(rag): implement IngestDocument workflow node

Implemented:
- IngestDocumentNode for workflow integration
- File path and collection ID inputs
- Document ID, chunks count, status outputs
- Error handling with user-friendly messages
- Full test coverage including error cases

Task 7 complete.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 8: QueryKnowledgeNode - Semantic Search Node

Implement QueryKnowledge workflow node for semantic search.

**Files:**
- Create: `src/core/nodes/rag/query.py`
- Modify: `src/core/nodes/rag/__init__.py`
- Test: `tests/unit/test_rag_query_node.py`

### Step 1: Write the failing test for QueryKnowledgeNode

```python
# tests/unit/test_rag_query_node.py
import pytest
from pathlib import Path
from src.core.nodes.rag.query import QueryKnowledgeNode
from src.rag.service import RAGService


class TestQueryKnowledgeNode:
    """Test QueryKnowledge workflow node."""

    @pytest.fixture
    async def rag_service(self, tmp_path):
        """Create temp RAG service with test data."""
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
        service, coll_id = await rag_service
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
        service, coll_id = await rag_service
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
        service, _ = await rag_service
        node = QueryKnowledgeNode(rag_service=service)

        result = await node.execute({
            "query": "test",
            "collection_id": "nonexistent",
            "top_k": 3
        })

        assert result["error"] is not None
        assert result["results"] == []
```

### Step 2: Run test to verify it fails

```bash
python -m pytest tests/unit/test_rag_query_node.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'src.core.nodes.rag.query'"

### Step 3: Implement QueryKnowledgeNode

```python
# src/core/nodes/rag/query.py
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
```

Update `__init__.py`:

```python
# src/core/nodes/rag/__init__.py
"""RAG workflow nodes."""

from src.core.nodes.rag.ingest import IngestDocumentNode
from src.core.nodes.rag.query import QueryKnowledgeNode

__all__ = ["IngestDocumentNode", "QueryKnowledgeNode"]
```

### Step 4: Run test to verify it passes

```bash
python -m pytest tests/unit/test_rag_query_node.py -v
```

Expected: PASS (all tests)

### Step 5: Commit Task 8

```bash
git add src/core/nodes/rag/ tests/unit/test_rag_query_node.py
git commit -m "feat(rag): implement QueryKnowledge workflow node

Implemented:
- QueryKnowledgeNode for semantic search
- Query, collection ID, top_k, min_similarity inputs
- Results list and context text outputs
- Error handling
- Full test coverage including edge cases

Task 8 complete.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 9: Integration Tests

Create integration tests for complete RAG workflow.

**Files:**
- Create: `tests/integration/test_rag_workflow.py`

### Step 1: Write integration tests

```python
# tests/integration/test_rag_workflow.py
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
```

### Step 2: Run integration tests

```bash
python -m pytest tests/integration/test_rag_workflow.py -v -m integration
```

Expected: PASS (all integration tests)

### Step 3: Commit Task 9

```bash
git add tests/integration/test_rag_workflow.py
git commit -m "test(rag): add integration tests for complete workflows

Implemented:
- End-to-end workflow test (create → ingest → query)
- Multiple collections test
- Large document chunking test
- Real semantic search validation

Task 9 complete.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 10: Update Dependencies

Add RAG dependencies to pyproject.toml.

**Files:**
- Modify: `pyproject.toml`

### Step 1: Update pyproject.toml

Edit the `[project.optional-dependencies]` section:

```toml
# In pyproject.toml, under [project.optional-dependencies]

ai = [
    # Existing AI dependencies
    "llama-cpp-python>=0.2.0",
    "openai>=1.0.0",
    "anthropic>=0.25.0",
    "google-generativeai>=0.5.0",
    "groq>=0.5.0",
    "huggingface-hub>=0.20.0",
    "chromadb>=0.5.0",  # Already present

    # RAG dependencies (Phase 5 Sprint 1)
    "sentence-transformers>=2.2.0",  # Local embeddings
]
```

### Step 2: Test installation

```bash
cd /c/Users/karlt/OneDrive/Desktop/Claude/skynette-repo/.worktrees/phase5-sprint1-rag-core
python -m pip install -e ".[ai,dev]" --quiet
```

Expected: SUCCESS (chromadb and sentence-transformers installed)

### Step 3: Verify imports work

```bash
python -c "from sentence_transformers import SentenceTransformer; import chromadb; print('RAG dependencies OK')"
```

Expected: "RAG dependencies OK"

### Step 4: Commit Task 10

```bash
git add pyproject.toml
git commit -m "build: add RAG dependencies to pyproject.toml

Added:
- sentence-transformers>=2.2.0 for local embeddings
- chromadb>=0.5.0 already present

Task 10 complete. Phase 5 Sprint 1 MVP ready.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Sprint 1 Complete

All 10 tasks completed! Phase 5 Sprint 1 (RAG Core MVP) is ready.

**Deliverables:**
- ✅ SQLite metadata storage for collections, documents, chunks
- ✅ ChromaDB vector database integration
- ✅ Local embedding model (all-MiniLM-L6-v2)
- ✅ Document processor for markdown/text with smart chunking
- ✅ RAG service orchestrating all components
- ✅ IngestDocument workflow node
- ✅ QueryKnowledge workflow node
- ✅ Full test coverage (unit + integration)
- ✅ Dependencies added to pyproject.toml

**What Works:**
- Create collections
- Ingest markdown/text documents
- Semantic search with configurable top_k
- Multiple independent collections
- Large document chunking

**Next Steps (Future Sprints):**
- Sprint 2: Code/PDF/Office document support with adaptive chunking
- Sprint 3: Auto-indexing, cloud embeddings, GetContextNode
- Sprint 4: UI integration, performance optimization, polish

---
