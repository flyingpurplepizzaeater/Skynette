# Phase 5: RAG Integration Design

**Date**: 2026-01-11
**Version**: 1.0
**Status**: Design Complete, Awaiting Implementation

---

## Executive Summary

Add Retrieval Augmented Generation (RAG) capabilities to Skynette workflow platform with ChromaDB integration. Enables document ingestion, semantic search, and context-enhanced AI responses through a hybrid architecture combining background indexing service with workflow node integration.

**Key Features**:
- Flexible RAG system supporting multiple use cases (document Q&A, codebase understanding, knowledge management)
- Hybrid architecture: background service for indexing + workflow nodes for user operations
- Comprehensive document support: text, markdown, code, PDFs, Office documents (Phase 1), media (Phase 2)
- Smart embedding strategy: local models by default, optional cloud providers
- Adaptive chunking: content-aware splitting optimized per file type
- Full UI integration with AI Hub "Knowledge Bases" tab

**Target Users**:
- Developers: Index codebases, query implementations
- Knowledge workers: Build searchable document repositories
- Researchers: Organize and retrieve research materials
- Teams: Share and query collective knowledge

---

## 1. High-Level Architecture

### Core Concept
Hybrid RAG system with background indexing service and workflow node integration.

### Three Main Components

#### 1.1 RAG Service (`src/rag/service.py`)
Background service running alongside Skynette:
- Manages ChromaDB collections
- Handles document indexing, chunking, embedding
- Watches configured folders for auto-indexing
- Exposes internal API for nodes to query
- Runs as separate thread within main process

#### 1.2 Workflow Nodes (`src/core/nodes/rag/`)
Five core nodes for workflow integration:
- `CreateCollectionNode` - Create/manage knowledge bases
- `IngestDocumentNode` - Add documents to collections
- `QueryKnowledgeNode` - Semantic search across collections
- `GetContextNode` - Retrieve relevant context for AI prompts
- `DeleteDocumentNode` - Remove documents from index

#### 1.3 Storage Layer (`src/rag/storage.py`)
Dual storage approach:
- **ChromaDB**: Vector database for embeddings and semantic search
- **SQLite**: Metadata tracking (document sources, chunk mappings, indexing status)
- **Embedding Cache**: Avoid re-embedding same content

### Data Flow

```
Ingestion Flow:
User drops file → IngestDocumentNode → RAG Service
  → Parse & chunk (adaptive) → Generate embeddings (local/cloud)
  → Store in ChromaDB + metadata in SQLite

Query Flow:
User runs QueryKnowledgeNode → RAG Service
  → Embed query → Semantic search ChromaDB
  → Return top-k relevant chunks → Pass to AI nodes
```

### Service Lifecycle
1. **Startup**: Load ChromaDB, initialize embedding model, start file watchers
2. **Running**: Process indexing queue, handle node requests, watch files
3. **Shutdown**: Flush queue, close ChromaDB, stop watchers

---

## 2. Document Processing Pipeline

### Adaptive Chunking Strategy

Content-aware splitting optimized per file type for best retrieval quality.

#### Code Files (`.py`, `.js`, `.ts`, `.java`, `.go`, etc.)
- Parse with AST (Abstract Syntax Tree)
- Split by functions, classes, methods
- Preserve docstrings with code
- Include imports/dependencies in chunk metadata
- **Example**: Python function becomes one chunk with its docstring and signature

**Implementation**:
```python
# Use ast module for Python, tree-sitter for other languages
def chunk_code(file_content: str, language: str) -> List[Chunk]:
    ast_tree = parse_with_ast(file_content, language)
    chunks = []
    for node in ast_tree.functions + ast_tree.classes:
        chunk = Chunk(
            content=node.text,
            metadata={
                "type": "function" if node.is_function else "class",
                "name": node.name,
                "line_range": [node.start_line, node.end_line],
                "docstring": node.docstring,
            }
        )
        chunks.append(chunk)
    return chunks
```

#### Markdown/Text (`.md`, `.txt`, `.rst`)
- Split by headers (## creates new chunk)
- Keep paragraphs intact
- Preserve code blocks
- Maintain hierarchy in metadata (H1 → H2 → H3)
- **Example**: Each markdown section = one chunk

#### PDFs (`.pdf`)
- Extract text with pypdf (already in dependencies)
- Split by pages or detected sections
- OCR for image-based PDFs (Phase 2 - requires tesseract)
- Preserve table structures where possible

#### Office Documents (`.docx`, `.xlsx`)
- Extract text with python-docx/openpyxl (new dependencies)
- Docx: Split by headings/paragraphs like markdown
- Excel: Each sheet or logical table = chunk
- Preserve formatting metadata (bold, italic) in chunk metadata

### Chunk Size Parameters

**Defaults**:
- **Target**: 512-1024 tokens per chunk
- **Overlap**: 128 tokens between adjacent chunks
- **Max**: 2048 tokens (prevents overly large chunks)
- **Adjustable**: Per collection for power users

**Rationale**:
- 512-1024 tokens balances context vs. precision
- Overlap ensures no information loss at boundaries
- Max prevents memory issues and poor retrieval

### Embedding Generation

#### Local Embeddings (Default)
- **Model**: `all-MiniLM-L6-v2` from sentence-transformers
- **Dimensions**: 384
- **Size**: ~80MB download
- **Speed**: ~100 docs/sec on CPU
- **Pros**: Free, private, no API keys needed
- **Cons**: Lower quality than cloud, CPU/memory overhead

#### Cloud Embeddings (Optional)
- **OpenAI**: `text-embedding-3-small` (1536 dimensions)
- **Cohere**: `embed-english-v3.0` (1024 dimensions)
- **Pros**: Higher quality, no local compute
- **Cons**: Cost per document, API keys required, privacy concerns

#### Hybrid Strategy (Recommended)
- Default to local for immediate functionality
- Users can upgrade to cloud per collection
- Cache embeddings by content hash (avoid duplicates)
- Automatic fallback to local if cloud fails

**Embedding Cache**:
```python
# Cache structure in SQLite
embedding_cache:
  content_hash: sha256 of text
  embedding: serialized vector
  model: "all-MiniLM-L6-v2" or "openai-small"
  created_at: timestamp

# Cache hit rate target: >80% for typical workflows
```

---

## 3. ChromaDB Collections & Metadata

### Collection Structure

Collections are isolated knowledge bases (like databases in a traditional DB).

#### Collection Types
1. **Project Collections** - Code repositories, project documentation
2. **Document Collections** - PDFs, office files, general knowledge
3. **Conversation Collections** - Chat histories for retrieval (future enhancement)

#### Collection Configuration
```python
Collection:
  id: uuid
  name: "ProjectDocs"
  description: "Technical documentation for the project"
  embedding_model: "local" | "openai" | "cohere"
  chunk_size: 1024
  chunk_overlap: 128
  auto_watch_folders: ["/docs/", "/README.md"]
  file_patterns: ["*.md", "*.pdf", "*.txt"]
  auto_update: True
  created_at: timestamp
  updated_at: timestamp
```

### SQLite Metadata Schema

#### Documents Table
```sql
CREATE TABLE documents (
    id TEXT PRIMARY KEY,
    collection_id TEXT NOT NULL,
    source_path TEXT NOT NULL,
    file_type TEXT NOT NULL,  -- "python", "markdown", "pdf", etc.
    file_hash TEXT NOT NULL,  -- sha256 for change detection
    file_size INTEGER,
    chunk_count INTEGER,
    indexed_at TIMESTAMP,
    last_updated TIMESTAMP,
    status TEXT NOT NULL,  -- "indexed", "processing", "failed"
    error TEXT,  -- Error message if status="failed"
    FOREIGN KEY (collection_id) REFERENCES collections(id)
);

CREATE INDEX idx_documents_collection ON documents(collection_id);
CREATE INDEX idx_documents_hash ON documents(file_hash);
CREATE INDEX idx_documents_status ON documents(status);
```

#### Chunks Table
```sql
CREATE TABLE chunks (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding_hash TEXT,  -- For cache lookup
    metadata JSON,  -- Flexible metadata storage
    created_at TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
);

CREATE INDEX idx_chunks_document ON chunks(document_id);
CREATE INDEX idx_chunks_embedding_hash ON chunks(embedding_hash);
```

#### Chunk Metadata Examples
```json
// Python function chunk
{
    "type": "function",
    "language": "python",
    "line_range": [10, 45],
    "function_name": "process_data",
    "class_name": "DataProcessor",
    "docstring": "Process input data and return results",
    "file_path": "src/core/processor.py"
}

// Markdown section chunk
{
    "type": "section",
    "language": "markdown",
    "heading": "Authentication",
    "heading_level": 2,
    "parent_section": "Security",
    "file_path": "docs/api.md"
}

// PDF page chunk
{
    "type": "page",
    "page_number": 5,
    "section_title": "Chapter 2: Architecture",
    "file_path": "docs/manual.pdf"
}
```

#### Embedding Cache Table
```sql
CREATE TABLE embedding_cache (
    content_hash TEXT PRIMARY KEY,
    embedding BLOB NOT NULL,  -- Serialized numpy array
    model TEXT NOT NULL,
    dimensions INTEGER,
    created_at TIMESTAMP,
    last_used TIMESTAMP,
    use_count INTEGER DEFAULT 1
);

CREATE INDEX idx_embedding_cache_model ON embedding_cache(model);
CREATE INDEX idx_embedding_cache_last_used ON embedding_cache(last_used);
```

### ChromaDB Storage

**Persistent Storage**:
- Location: `~/.skynette/rag/chromadb/`
- One collection per knowledge base
- Stores: embeddings + chunk text + metadata
- Index: HNSW (Hierarchical Navigable Small World) for efficient similarity search

**Query Performance**:
- Similarity search: O(log n) with HNSW
- Target: <500ms for top-5 results from 10k documents
- Filters: Support metadata filtering during search

### Auto-Indexing System

**File Watcher**:
- Uses `watchdog` library (already in dependencies)
- Monitors configured folders for changes
- Debounces rapid changes (wait 2s)
- Filters by file patterns (*.py, *.md, etc.)

**Auto-Indexing Flow**:
```
1. FileWatcher detects change (create/modify/delete)
2. Debounce timer (2 seconds)
3. Check if file matches collection patterns
4. Add IndexJob to queue
5. RAG Service processes job in background
6. Update ChromaDB + SQLite
7. Emit event for UI updates
```

**Change Detection**:
```python
def should_reindex(file_path: str, collection_id: str) -> bool:
    current_hash = compute_file_hash(file_path)
    stored_doc = get_document_by_path(file_path, collection_id)

    if not stored_doc:
        return True  # New file

    if stored_doc.file_hash != current_hash:
        return True  # File changed

    return False  # No changes
```

---

## 4. Workflow Nodes

Five core RAG nodes for user-facing workflow integration.

### 4.1 CreateCollectionNode

**Purpose**: Create and configure knowledge bases

**Inputs**:
- `collection_name` (string, required) - Unique name for collection
- `description` (text, optional) - Human-readable description
- `embedding_model` (choice, default: "local")
  - Options: "local", "openai", "cohere"
- `chunk_size` (number, default: 1024) - Target tokens per chunk
- `chunk_overlap` (number, default: 128) - Overlap between chunks

**Outputs**:
- `collection_id` (string) - UUID for the collection
- `status` (string) - "success" or "error"
- `error` (string, optional) - Error message if failed

**Example Workflow**:
```
ManualTrigger → CreateCollection(name="ProjectDocs") → IngestDocument(...)
```

### 4.2 IngestDocumentNode

**Purpose**: Add documents to knowledge base

**Inputs**:
- `file_path` (file/folder, required) - Single file or directory path
- `collection_id` (string, required) - Target collection UUID
- `recursive` (boolean, default: false) - Process subdirectories
- `file_patterns` (string, optional) - Filter patterns: "*.py,*.md"
- `auto_update` (boolean, default: false) - Watch for future changes

**Outputs**:
- `documents_added` (number) - Count of documents indexed
- `chunks_created` (number) - Total chunks generated
- `errors` (list) - Failed files with error messages
- `job_id` (string) - For tracking long-running jobs

**Example Workflow**:
```
ManualTrigger → IngestDocument(
    file_path="/src/",
    collection_id="{{coll_id}}",
    recursive=true,
    file_patterns="*.py"
) → LogDebug("Indexed {{chunks_created}} chunks")
```

**Progress Tracking**:
- For large ingestion jobs, emit progress events
- UI shows real-time progress bar
- Node waits for completion or timeout (5 min default)

### 4.3 QueryKnowledgeNode

**Purpose**: Semantic search across knowledge base

**Inputs**:
- `query` (text, required) - Search query: "How does authentication work?"
- `collection_id` (string, required) - Collection to search
- `top_k` (number, default: 5) - Number of results to return
- `min_similarity` (number, default: 0.5) - Threshold 0-1 (cosine similarity)
- `metadata_filters` (JSON, optional) - Filter by chunk metadata

**Outputs**:
- `results` (list) - Array of chunk objects with scores
- `context` (text) - Concatenated chunk text (ready for AI)
- `sources` (list) - List of source file paths
- `similarities` (list) - Similarity scores for each result

**Result Format**:
```json
{
  "results": [
    {
      "chunk_id": "uuid",
      "content": "class AuthManager:\n    def authenticate(user)...",
      "similarity": 0.92,
      "metadata": {
        "type": "class",
        "file_path": "src/auth/manager.py",
        "line_range": [10, 45]
      }
    }
  ],
  "context": "class AuthManager:\n    def authenticate(user)...\n\n...",
  "sources": ["src/auth/manager.py", "src/auth/tokens.py"],
  "similarities": [0.92, 0.87, 0.84]
}
```

**Example Workflow**:
```
ManualTrigger → SetVariable(query="How does auth work?")
  → QueryKnowledge(query="{{query}}", collection_id="{{coll_id}}")
  → ChatNode(prompt="Based on this code:\n{{context}}\n\nExplain: {{query}}")
```

### 4.4 GetContextNode

**Purpose**: Smart retrieval optimized for AI context windows

**Inputs**:
- `query` (text, required) - What context to retrieve
- `collection_ids` (list, required) - Search multiple collections
- `max_tokens` (number, default: 2000) - Fit in AI context window
- `deduplicate` (boolean, default: true) - Remove duplicate chunks
- `prioritize` (choice, default: "similarity") - "similarity" or "recency"

**Outputs**:
- `context` (text) - Optimized text for AI prompts
- `sources` (list) - Source files used
- `token_count` (number) - Actual token count
- `chunks_included` (number) - Number of chunks

**Smart Features**:
- Multi-collection search with result merging
- Token-aware truncation (fits context window)
- Deduplication (same chunk from multiple collections)
- Prioritization (most relevant or most recent)

**Example Workflow**:
```
ManualTrigger
  → GetContext(
      query="Code review guidelines",
      collection_ids=["docs", "codebase"],
      max_tokens=1500
    )
  → ChatNode(
      system_prompt="You are a code reviewer. Use this context:\n{{context}}",
      message="Review this PR..."
    )
```

### 4.5 DeleteDocumentNode

**Purpose**: Remove documents from knowledge base

**Inputs**:
- `document_id` (string, optional) - UUID of document
- `file_path` (string, optional) - Path of document (alternative to ID)
- `collection_id` (string, required) - Collection containing document
- `confirm` (boolean, default: false) - Safety check

**Outputs**:
- `deleted` (boolean) - Success status
- `chunks_removed` (number) - Count of deleted chunks
- `error` (string, optional) - Error if failed

**Example Workflow**:
```
ManualTrigger → DeleteDocument(
    file_path="/docs/outdated.md",
    collection_id="{{coll_id}}",
    confirm=true
) → LogDebug("Removed {{chunks_removed}} chunks")
```

### Node Design Guidelines

**Visual Design**:
- **Category**: New "RAG" category in node palette
- **Color**: Purple/indigo (#7C3AED) - distinct from AI nodes (#8B5CF6)
- **Icons**:
  - CreateCollection: 📚
  - IngestDocument: 📥
  - QueryKnowledge: 🔍
  - GetContext: 🧩
  - DeleteDocument: 🗑️

**Error Handling**:
- All nodes wrap operations in try/except
- Return error outputs (not crash workflow)
- Log errors to workflow execution history
- Emit error events for UI notifications

**Performance**:
- Async/await for all I/O operations
- Progress tracking for long operations
- Timeout handling (default: 5 min for ingestion)
- Resource limits (max file size: 100MB per file)

---

## 5. RAG Background Service

### Service Architecture

**RAGService** runs as separate thread within Skynette's main process.

#### Components

```python
class RAGService:
    """Background service managing RAG operations."""

    def __init__(self):
        self.document_processor = DocumentProcessor()
        self.embedding_manager = EmbeddingManager()
        self.chromadb_client = ChromaDBClient()
        self.file_watcher = FileWatcher()
        self.index_queue = IndexQueue()
        self.is_running = False
```

**DocumentProcessor**:
- Parses files by type
- Creates adaptive chunks
- Extracts metadata
- Handles parsing errors gracefully

**EmbeddingManager**:
- Manages local embedding models
- Handles cloud API calls
- Implements embedding cache
- Falls back on failures

**ChromaDBClient**:
- Wraps ChromaDB operations
- Manages collections
- Executes queries
- Handles persistence

**FileWatcher**:
- Monitors configured folders
- Debounces rapid changes
- Filters by patterns
- Emits file events

**IndexQueue**:
- Priority queue for indexing jobs
- Async processing
- Progress tracking
- Job persistence (survives restarts)

### Service Lifecycle

#### 1. Startup Sequence
```python
async def start(self):
    # 1. Load ChromaDB
    await self.chromadb_client.connect("~/.skynette/rag/chromadb")

    # 2. Initialize embedding model (download if needed)
    await self.embedding_manager.load_model("all-MiniLM-L6-v2")

    # 3. Start file watchers for auto-indexed collections
    collections = await self.get_auto_indexed_collections()
    for coll in collections:
        self.file_watcher.watch(coll.folders, coll.id)

    # 4. Start index queue processor
    self.index_queue.start()

    # 5. Resume interrupted jobs (from previous session)
    await self.resume_interrupted_jobs()

    self.is_running = True
```

#### 2. Running State
- Process indexing queue continuously
- Handle node API requests (synchronous response)
- Watch files for changes (async events)
- Update UI with progress events

#### 3. Shutdown Sequence
```python
async def shutdown(self):
    # 1. Stop accepting new jobs
    self.is_running = False

    # 2. Flush indexing queue (finish current jobs)
    await self.index_queue.flush(timeout=30)

    # 3. Stop file watchers
    self.file_watcher.stop()

    # 4. Close ChromaDB connection
    await self.chromadb_client.disconnect()

    # 5. Persist queue state
    await self.index_queue.save_state()
```

### Async Job Queue

**IndexJob Schema**:
```python
@dataclass
class IndexJob:
    id: str  # UUID
    priority: str  # "high", "normal", "low"
    job_type: str  # "index_file", "index_folder", "reindex", "delete"
    collection_id: str
    file_path: str
    options: dict  # recursive, file_patterns, etc.
    status: str  # "queued", "processing", "completed", "failed"
    progress: float  # 0.0-1.0
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error: Optional[str]
```

**Queue Processing**:
```python
async def process_queue(self):
    while self.is_running:
        job = await self.queue.get_next()

        if not job:
            await asyncio.sleep(1)
            continue

        try:
            job.status = "processing"
            job.started_at = datetime.now()
            await self.emit_job_update(job)

            if job.job_type == "index_file":
                await self.process_file(job)
            elif job.job_type == "index_folder":
                await self.process_folder(job)
            elif job.job_type == "reindex":
                await self.reindex_document(job)
            elif job.job_type == "delete":
                await self.delete_document(job)

            job.status = "completed"
            job.completed_at = datetime.now()
            job.progress = 1.0

        except Exception as e:
            job.status = "failed"
            job.error = str(e)
            await self.emit_job_error(job, e)

        finally:
            await self.emit_job_update(job)
```

**Priority Handling**:
- High: User-initiated ingestion (UI or workflow node)
- Normal: Auto-indexing from file watcher
- Low: Background re-indexing

### Performance Optimizations

#### Batching
```python
# Process multiple files in single ChromaDB transaction
async def batch_index(self, files: List[str], collection_id: str):
    chunks_batch = []

    for file in files:
        chunks = await self.document_processor.process(file)
        chunks_batch.extend(chunks)

        # Batch size limit
        if len(chunks_batch) >= 100:
            await self.chromadb_client.add_batch(chunks_batch, collection_id)
            chunks_batch = []

    # Flush remaining
    if chunks_batch:
        await self.chromadb_client.add_batch(chunks_batch, collection_id)
```

#### Parallel Processing
```python
# Use thread pool for CPU-bound file parsing
from concurrent.futures import ThreadPoolExecutor

async def process_folder(self, folder: str, collection_id: str):
    files = list_files(folder, recursive=True)

    with ThreadPoolExecutor(max_workers=4) as executor:
        # Parse files in parallel
        parse_tasks = [
            executor.submit(self.document_processor.parse, file)
            for file in files
        ]

        # Collect results
        for future in as_completed(parse_tasks):
            chunks = await future.result()
            # Index chunks (I/O-bound, can be async)
            await self.index_chunks(chunks, collection_id)
```

#### Rate Limiting (Cloud Embeddings)
```python
from asyncio import Semaphore

class EmbeddingManager:
    def __init__(self):
        # Limit concurrent API calls
        self.openai_semaphore = Semaphore(5)  # Max 5 concurrent
        self.rate_limiter = RateLimiter(max_per_minute=500)

    async def embed_with_openai(self, texts: List[str]):
        async with self.openai_semaphore:
            await self.rate_limiter.acquire()
            return await openai.embed(texts)
```

#### Progress Tracking
```python
class IndexJob:
    async def update_progress(self, current: int, total: int):
        self.progress = current / total
        await self.emit_event("progress", {
            "job_id": self.id,
            "progress": self.progress,
            "current": current,
            "total": total
        })

# Usage
async def process_folder(self, job: IndexJob):
    files = list_files(job.file_path)
    total = len(files)

    for i, file in enumerate(files):
        await self.process_file(file, job.collection_id)
        await job.update_progress(i + 1, total)
```

### Auto-Indexing Flow

```
1. FileWatcher detects change
   ↓
2. Debounce timer (2 seconds)
   - Prevents duplicate events for rapid changes
   - Batches multiple changes
   ↓
3. Check if file matches collection patterns
   - File extension in allowed patterns?
   - Path matches watched folders?
   ↓
4. Compute file hash
   ↓
5. Compare with stored hash (if exists)
   - No change? Skip
   - Changed? Continue
   ↓
6. Create IndexJob with priority="normal"
   ↓
7. Add to queue
   ↓
8. RAG Service processes job
   ↓
9. Update ChromaDB + SQLite
   ↓
10. Emit event for UI update
```

### Internal API for Nodes

Nodes call service methods directly (not HTTP):

```python
# RAG Service exposes sync API for workflow execution
class RAGService:

    # Collection management
    def create_collection(self, name: str, config: dict) -> str:
        """Returns collection_id"""

    def delete_collection(self, collection_id: str) -> bool:
        """Returns success"""

    # Document ingestion
    def ingest_document(self, file_path: str, collection_id: str,
                       options: dict) -> dict:
        """Returns {documents_added, chunks_created, job_id}"""

    # Querying
    def query(self, query_text: str, collection_id: str,
             top_k: int, min_similarity: float) -> dict:
        """Returns {results, context, sources, similarities}"""

    def get_context(self, query_text: str, collection_ids: List[str],
                   max_tokens: int) -> dict:
        """Returns {context, sources, token_count}"""

    # Status tracking
    def get_job_status(self, job_id: str) -> dict:
        """Returns {status, progress, error}"""

    def get_collection_stats(self, collection_id: str) -> dict:
        """Returns {document_count, chunk_count, last_updated}"""
```

**Thread Safety**:
- Service methods use async locks for shared state
- ChromaDB client is thread-safe
- Job queue uses async-safe data structures

---

## 6. UI Integration & Settings

### New AI Hub Tab: "Knowledge Bases"

Fifth tab in AI Hub (after Overview, Providers, Models, Usage).

#### Main View Layout

```
┌─────────────────────────────────────────────────────────────┐
│ 🗂️  Knowledge Bases                      [+ New Collection]  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ ┌────────────────────┐  ┌────────────────────┐             │
│ │ ProjectDocs        │  │ Codebase           │             │
│ │ 📄 245 documents   │  │ 📄 1,234 documents │             │
│ │ 🧩 3,421 chunks    │  │ 🧩 18,901 chunks   │             │
│ │ 🕐 Last: 2h ago    │  │ 🕐 Last: 5m ago    │             │
│ │ 💾 12.3 MB         │  │ 💾 156.7 MB        │             │
│ │                    │  │                    │             │
│ │ [Query] [Manage]   │  │ [Query] [Manage]   │             │
│ └────────────────────┘  └────────────────────┘             │
│                                                              │
│ ┌────────────────────┐                                      │
│ │ Research Papers    │                                      │
│ │ 📄 89 documents    │                                      │
│ │ 🧩 1,567 chunks    │                                      │
│ │ 🕐 Last: 1d ago    │                                      │
│ │ 💾 45.2 MB         │                                      │
│ │                    │                                      │
│ │ [Query] [Manage]   │                                      │
│ └────────────────────┘                                      │
│                                                              │
│ Active Indexing Jobs:                                       │
│ ├─ 📥 /docs/api.md → ProjectDocs [████████░░] 80%          │
│ └─ 📥 /src/core/ → Codebase [████░░░░░░] 40% (12/30 files) │
│                                                              │
│ Recent Activity:                                            │
│ ├─ ✅ Indexed report.pdf to Research Papers (2 minutes ago) │
│ ├─ ✅ Updated auth.py in Codebase (5 minutes ago)          │
│ └─ ❌ Failed to parse corrupted.docx (10 minutes ago)      │
└─────────────────────────────────────────────────────────────┘
```

**Collection Card Components**:
- Name and emoji icon
- Document/chunk counts with icons
- Last indexed timestamp (relative: "2h ago")
- Storage size
- Action buttons: Query (open query dialog), Manage (open settings)

**Empty State** (no collections):
```
┌─────────────────────────────────────────────────────────────┐
│                                                              │
│                    📚 No Knowledge Bases Yet                 │
│                                                              │
│         Create a collection to start indexing documents      │
│                                                              │
│                   [+ Create Your First Collection]           │
│                                                              │
│  Need inspiration? Check out example workflows →            │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Collection Management Dialog

Opened when clicking "Manage" on a collection card.

```
┌─────────────────────────────────────────────────────────────┐
│ Settings for "ProjectDocs"                            [×]    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ Basic Information                                           │
│ ├─ Name: [ProjectDocs                         ]            │
│ └─ Description: [Technical documentation for...] (optional) │
│                                                              │
│ Auto-Indexing                                               │
│ ├─ ☑ Enable auto-indexing                                  │
│ ├─ Watch folders:                                           │
│ │   • /home/user/project/docs/              [×] [+ Add]    │
│ │   • /home/user/project/README.md          [×]            │
│ └─ File patterns: [*.md, *.pdf, *.txt          ]           │
│                                                              │
│ Embedding Configuration                                     │
│ ├─ Model:                                                   │
│ │   ⦿ Local (all-MiniLM-L6-v2) - Free, private             │
│ │   ○ OpenAI (text-embedding-3-small) - Higher quality     │
│ │   ○ Cohere (embed-english-v3.0) - Alternative cloud      │
│ └─ Status: ✅ Local model loaded (80MB)                     │
│                                                              │
│ Chunking Settings                                           │
│ ├─ Chunk size: [1024    ] tokens                           │
│ ├─ Overlap:    [128     ] tokens                           │
│ └─ Max size:   [2048    ] tokens                           │
│                                                              │
│ Advanced                                                    │
│ ├─ [Show metadata filters]                                 │
│ └─ [Show performance settings]                             │
│                                                              │
│ Danger Zone                                                 │
│ ├─ [Reindex All Documents]                                 │
│ └─ [Delete Collection]  ⚠️  Cannot be undone               │
│                                                              │
│              [Cancel]  [Save Changes]                       │
└─────────────────────────────────────────────────────────────┘
```

**Validation**:
- Collection name: required, alphanumeric + underscores
- Chunk size: 256-4096 tokens
- Overlap: 0 to chunk_size/2
- Max size: >= chunk_size
- Watch folders: must exist on filesystem

**Error Feedback**:
- Real-time validation (red border on invalid fields)
- Error messages below fields
- Cannot save until valid

### Query Testing Interface

Opened when clicking "Query" on a collection card.

```
┌─────────────────────────────────────────────────────────────┐
│ Query "ProjectDocs"                                    [×]   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ Test Query                                                  │
│ ┌──────────────────────────────────────────────────────────┐│
│ │ How does authentication work?                           ││
│ └──────────────────────────────────────────────────────────┘│
│                                                              │
│ Options:                                                    │
│ ├─ Top K results: [5     ] ▼                               │
│ └─ Min similarity: [0.5   ] (0.0 = any, 1.0 = exact)       │
│                                                              │
│                           [Search]                           │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│ Results (5 found in 234ms)                                  │
│                                                              │
│ ┌────────────────────────────────────────────────────────┐  │
│ │ 1. auth.py:45-78 (similarity: 0.92) 📄                 │  │
│ │                                                         │  │
│ │ class AuthManager:                                     │  │
│ │     """Handles user authentication with JWT tokens.    │  │
│ │                                                         │  │
│ │     Features:                                          │  │
│ │     - Login with username/password                     │  │
│ │     - Token generation and validation                  │  │
│ │     - Session management                               │  │
│ │     """                                                 │  │
│ │     ...                                                 │  │
│ │                                                         │  │
│ │ [Copy Text] [View in Editor] [Use in Workflow]        │  │
│ └────────────────────────────────────────────────────────┘  │
│                                                              │
│ ┌────────────────────────────────────────────────────────┐  │
│ │ 2. README.md:Authentication (similarity: 0.87) 📄      │  │
│ │                                                         │  │
│ │ ## Authentication                                       │  │
│ │                                                         │  │
│ │ The system uses JWT bearer tokens for authentication.  │  │
│ │ Users authenticate with username and password to       │  │
│ │ receive a token valid for 24 hours.                    │  │
│ │                                                         │  │
│ │ [Copy Text] [View in Editor] [Use in Workflow]        │  │
│ └────────────────────────────────────────────────────────┘  │
│                                                              │
│ [Show 3 more results...]                                    │
│                                                              │
│ Combined Context (523 tokens):                              │
│ [View Full Context]  [Copy to Clipboard]                    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Features**:
- Real-time search with configurable parameters
- Results with similarity scores and source info
- Code syntax highlighting
- Actions: Copy, view in editor, use in workflow
- Combined context view (ready for AI prompts)

### Global RAG Settings

In main Settings/Preferences dialog, new "RAG" section.

```
┌─────────────────────────────────────────────────────────────┐
│ Settings > RAG                                               │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ Storage                                                     │
│ ├─ Data location: [~/.skynette/rag/              ] [Browse]│
│ │   Current size: 234.5 MB (12,345 documents)              │
│ └─ [Clean up cache] [Export all collections]               │
│                                                              │
│ Default Embedding Model                                     │
│ ├─ ⦿ Local (all-MiniLM-L6-v2)                               │
│ │   Status: ✅ Downloaded (80MB)                            │
│ ├─ ○ OpenAI (text-embedding-3-small)                        │
│ │   API Key: [sk-.....................] [Set]              │
│ │   Status: ⚠️  API key not configured                     │
│ └─ ○ Cohere (embed-english-v3.0)                            │
│     API Key: [Not set               ] [Set]                │
│     Status: ❌ API key not configured                       │
│                                                              │
│ Performance                                                 │
│ ├─ Max concurrent indexing jobs: [3     ] ▼                │
│ ├─ Enable auto-indexing: ☑                                 │
│ ├─ Indexing priority: ○ Speed  ⦿ Quality  ○ Balanced       │
│ └─ Memory limit: [500   ] MB                               │
│                                                              │
│ Advanced Settings                                           │
│ ├─ Default chunk size: [1024 ] tokens                      │
│ ├─ Default overlap: [128  ] tokens                         │
│ ├─ Embedding cache: ☑ Enabled (saves 80% re-indexing time) │
│ └─ Debug logging: ☐ Enable verbose RAG logs                │
│                                                              │
│ Cloud Embedding Costs (This Month)                         │
│ ├─ OpenAI: $0.00 (0 documents)                             │
│ └─ Cohere: $0.00 (0 documents)                             │
│                                                              │
│                    [Reset to Defaults]  [Save]              │
└─────────────────────────────────────────────────────────────┘
```

### Usage Dashboard Integration

Extend existing Usage Dashboard (Phase 4 Sprint 3) with RAG metrics.

**New Metrics Card**:
```
┌────────────────────┐
│ RAG Embeddings     │
│ $0.42 this month   │
│ 1,234 documents    │
│ 89% cache hit rate │
└────────────────────┘
```

**RAG Section in Provider Breakdown**:
```
Embedding Costs by Provider:
├─ Local (all-MiniLM-L6): $0.00 (1,100 docs, 100% cache)
├─ OpenAI: $0.35 (120 docs, 78% cache)
└─ Cohere: $0.07 (14 docs, 85% cache)
```

**Indexing Statistics**:
```
Documents Indexed (Last 30 Days):
├─ Daily average: 42 documents
├─ Peak day: 156 documents (Jan 5)
├─ Total chunks: 18,901
└─ Storage used: 234.5 MB
```

---

## 7. Error Handling & Edge Cases

Comprehensive error handling for production reliability.

### Common Failure Scenarios

#### 1. Document Parsing Failures

**Scenario**: Corrupted or unsupported file

```python
Error: "Failed to parse corrupted.pdf: Invalid PDF structure"

Handling:
- Log error with full stack trace
- Mark document status as "failed" in SQLite
- Store error message for user visibility
- Continue processing other files (don't block queue)
- Show in UI with retry option
- Emit error event for workflow error handling

# Implementation
try:
    chunks = await self.parse_pdf(file_path)
except PDFError as e:
    await self.db.update_document_status(
        file_path=file_path,
        status="failed",
        error=f"PDF parsing failed: {str(e)}"
    )
    logger.error(f"Failed to parse {file_path}: {e}")
    # Don't raise - continue with next file
    return []
```

**User Experience**:
- UI shows red error icon on collection card
- Hover/click shows error details
- "Retry" button to attempt re-indexing
- Option to skip file permanently

#### 2. Embedding Generation Failures

**Scenario**: Cloud API rate limit or timeout

```python
Error: "OpenAI API rate limit exceeded (429)"

Handling:
1. Automatic fallback to local embeddings
2. Show warning notification in UI
3. Queue failed documents for retry with exponential backoff
4. Log API error for debugging
5. Update collection settings to suggest local model

# Implementation
async def generate_embedding(self, text: str, model: str):
    try:
        if model == "openai":
            return await self.openai_embed(text)
    except RateLimitError:
        logger.warning("OpenAI rate limit, falling back to local")
        self.show_notification(
            "OpenAI rate limit exceeded. Using local embeddings for now.",
            level="warning"
        )
        return await self.local_embed(text)
    except APIError as e:
        # Retry with backoff
        await asyncio.sleep(2 ** self.retry_count)
        return await self.generate_embedding(text, model)
```

**User Options**:
- Pause indexing until rate limit resets
- Switch to local embeddings permanently
- Batch and retry later
- Increase rate limit (upgrade API plan)

#### 3. ChromaDB Storage Issues

**Scenario**: Disk full or database corruption

```python
Error: "No space left on device" or "ChromaDB connection failed"

Handling:
- Immediately pause all indexing jobs
- Save job queue state to resume later
- Alert user with high-priority notification
- Show storage usage and cleanup options
- Graceful degradation: serve cached query results
- Prevent data loss: flush pending writes

# Implementation
try:
    await self.chromadb.add_documents(chunks)
except DiskFullError:
    await self.index_queue.pause()
    await self.save_queue_state()
    self.show_alert(
        "Storage full! RAG indexing paused.",
        actions=["Clean up cache", "Change storage location", "Resume"]
    )
except ChromaDBError as e:
    logger.critical(f"ChromaDB error: {e}")
    # Try to recover
    await self.chromadb.reconnect()
```

**Recovery Actions**:
- Clean up embedding cache
- Move storage to different location
- Delete old/unused collections
- Increase disk space

#### 4. Large Files

**Scenario**: 500MB PDF or 100k-line code file

```python
Issue: Memory overflow or timeout

Handling:
- Stream processing (don't load entire file in memory)
- Progress tracking for large files
- Timeout after 5 minutes, warn user
- Suggest splitting large files
- Chunk processing in batches

# Implementation
async def process_large_file(self, file_path: str):
    file_size = os.path.getsize(file_path)

    if file_size > 100 * 1024 * 1024:  # 100MB
        logger.warning(f"Large file detected: {file_size / 1024 / 1024:.1f}MB")

    # Stream processing
    async with aiofiles.open(file_path, 'r') as f:
        buffer = []
        async for line in f:
            buffer.append(line)

            # Process in 10k line batches
            if len(buffer) >= 10000:
                chunks = await self.chunk_text(''.join(buffer))
                await self.index_chunks(chunks)
                buffer = []

                # Check timeout
                if time.time() - start_time > 300:  # 5 min
                    raise TimeoutError("File processing timeout")
```

**User Feedback**:
- Show file size before indexing
- Estimate processing time
- Real-time progress bar
- Option to cancel

#### 5. Duplicate Content

**Scenario**: Same document indexed multiple times

```python
Issue: Wasted storage and duplicate search results

Handling:
- Check file hash before indexing
- Update existing document instead of creating duplicate
- Detect content changes (hash comparison)
- Offer "Force reindex" option
- Deduplicate search results

# Implementation
async def ingest_document(self, file_path: str, collection_id: str):
    # Compute hash
    file_hash = await compute_file_hash(file_path)

    # Check if exists
    existing = await self.db.get_document_by_hash(file_hash, collection_id)

    if existing:
        logger.info(f"Document already indexed: {file_path}")

        if existing.source_path != file_path:
            # Same content, different path - create reference
            await self.db.create_document_reference(existing.id, file_path)

        return {"status": "skipped", "reason": "duplicate"}

    # New document - proceed with indexing
    await self.index_new_document(file_path, file_hash, collection_id)
```

#### 6. Query Returns No Results

**Scenario**: User query finds nothing (similarity < threshold)

```python
Issue: Empty search results, user frustration

Handling:
- Return empty results with helpful message
- Suggest lowering min_similarity threshold
- Show query embedding for debugging (advanced users)
- Offer to search across all collections
- Check if collection is empty

# Implementation
async def query(self, query: str, collection_id: str,
                top_k: int, min_similarity: float):
    results = await self.chromadb.query(query, collection_id, top_k)

    # Filter by similarity
    filtered = [r for r in results if r.similarity >= min_similarity]

    if not filtered:
        # Provide helpful response
        collection = await self.db.get_collection(collection_id)

        if collection.document_count == 0:
            message = "Collection is empty. Add documents first."
        elif results:
            # Results exist but below threshold
            best_match = results[0]
            message = f"No matches above {min_similarity:.0%} threshold. Best match: {best_match.similarity:.0%}"
            suggestion = f"Try lowering min_similarity to {best_match.similarity:.1f}"
        else:
            message = "No results found. Try different search terms."
            suggestion = "Search across all collections?"

        return {
            "results": [],
            "message": message,
            "suggestion": suggestion
        }

    return {"results": filtered}
```

**UI Response**:
```
No results found for "quantum computing"

Suggestions:
├─ Lower similarity threshold to 0.3 [Apply]
├─ Search all collections [Search]
└─ Try different search terms
```

#### 7. Embedding Model Download Failures

**Scenario**: Cannot download model (network issue, disk full)

```python
Error: "Failed to download all-MiniLM-L6-v2: Connection timeout"

Handling:
- Cache model in ~/.skynette/rag/models/
- Retry with different mirror (Hugging Face has multiple CDNs)
- Fall back to cloud embeddings if API keys available
- Clear error message with manual download instructions
- Resume downloads (don't restart from scratch)

# Implementation
async def load_embedding_model(self, model_name: str):
    model_path = self.get_model_cache_path(model_name)

    if model_path.exists():
        logger.info(f"Loading cached model: {model_name}")
        return SentenceTransformer(str(model_path))

    try:
        logger.info(f"Downloading model: {model_name}")
        model = SentenceTransformer(model_name, cache_folder=str(model_path.parent))
        return model

    except ConnectionError as e:
        logger.error(f"Download failed: {e}")

        # Try alternative mirror
        for mirror in self.huggingface_mirrors:
            try:
                return SentenceTransformer(model_name, cache_folder=str(model_path.parent))
            except:
                continue

        # All mirrors failed
        self.show_error(
            title="Model download failed",
            message=f"Could not download {model_name}. Please check your internet connection.",
            actions=[
                ("Use cloud embeddings", self.switch_to_cloud),
                ("Manual download", self.show_manual_download_instructions),
                ("Retry", lambda: self.load_embedding_model(model_name))
            ]
        )

        raise ModelDownloadError(f"Failed to download {model_name}")
```

### Node Execution Errors

All RAG nodes wrap operations in try/except and return structured errors:

```python
class QueryKnowledgeNode(BaseNode):
    async def execute(self, inputs: dict) -> dict:
        try:
            results = await self.rag_service.query(
                query=inputs["query"],
                collection_id=inputs["collection_id"],
                top_k=inputs.get("top_k", 5),
                min_similarity=inputs.get("min_similarity", 0.5)
            )

            return {
                "results": results["results"],
                "context": results["context"],
                "sources": results["sources"],
                "error": None
            }

        except CollectionNotFoundError as e:
            return {
                "results": [],
                "context": "",
                "sources": [],
                "error": f"Collection not found: {inputs['collection_id']}"
            }

        except Exception as e:
            logger.exception(f"Query failed: {e}")
            return {
                "results": [],
                "context": "",
                "sources": [],
                "error": f"Query failed: {str(e)}"
            }
```

**Workflow Error Handling**:
- Nodes don't crash workflows - return error outputs
- Workflows can check `error` output and branch accordingly
- All errors logged to workflow execution history
- UI shows error notifications

**Example Workflow with Error Handling**:
```
QueryKnowledge → IfElse(condition="{{error}} == null")
  ├─ True → ChatNode(use results)
  └─ False → LogDebug(show error message)
```

### System-Level Safeguards

**Resource Limits**:
```python
# Configuration
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB per file
MAX_MEMORY_USAGE = 500 * 1024 * 1024  # 500MB for service
MAX_CONCURRENT_JOBS = 3
INDEXING_TIMEOUT = 300  # 5 minutes per file
QUERY_TIMEOUT = 30  # 30 seconds per query
```

**Graceful Degradation**:
- If ChromaDB fails: Serve cached results, disable indexing
- If embedding model fails: Fall back to keyword search
- If disk full: Pause indexing, alert user
- If memory high: Reduce concurrent jobs, clear caches

**Data Integrity**:
- Atomic operations (document + chunks added together)
- Transaction rollback on failures
- Periodic health checks
- Backup before destructive operations

---

## 8. Testing Strategy & Performance

### Unit Tests

Located in `tests/unit/test_rag/`

#### test_document_processor.py
```python
class TestDocumentProcessor:
    """Test adaptive document parsing and chunking."""

    def test_parse_python_file_creates_chunks(self):
        """Python files should be chunked by functions/classes."""
        processor = DocumentProcessor()
        source = '''
        def hello():
            """Say hello."""
            return "Hello"

        class Greeter:
            """Greet people."""
            def greet(self):
                return "Hi"
        '''

        chunks = processor.parse(source, language="python")

        assert len(chunks) == 2  # function + class
        assert chunks[0].metadata["type"] == "function"
        assert chunks[0].metadata["name"] == "hello"
        assert chunks[1].metadata["type"] == "class"
        assert chunks[1].metadata["name"] == "Greeter"

    def test_parse_markdown_splits_by_headers(self):
        """Markdown should be chunked by header sections."""
        processor = DocumentProcessor()
        markdown = '''
        # Title

        Introduction text.

        ## Section 1

        Section 1 content.

        ## Section 2

        Section 2 content.
        '''

        chunks = processor.parse(markdown, language="markdown")

        assert len(chunks) == 3  # Title + 2 sections
        assert chunks[0].metadata["heading"] == "Title"
        assert chunks[1].metadata["heading"] == "Section 1"
        assert chunks[2].metadata["heading"] == "Section 2"

    def test_parse_pdf_extracts_text(self):
        """PDFs should extract text from pages."""
        processor = DocumentProcessor()
        # Use sample PDF
        pdf_path = "tests/fixtures/sample.pdf"

        chunks = processor.parse_file(pdf_path)

        assert len(chunks) > 0
        assert all(chunk.content for chunk in chunks)
        assert all(chunk.metadata["type"] == "page" for chunk in chunks)

    def test_adaptive_chunking_respects_token_limits(self):
        """Chunks should not exceed max token limit."""
        processor = DocumentProcessor(
            chunk_size=512,
            max_size=1024
        )

        # Very long text
        long_text = " ".join(["word"] * 5000)

        chunks = processor.chunk_text(long_text)

        for chunk in chunks:
            token_count = processor.count_tokens(chunk.content)
            assert token_count <= 1024

    def test_chunk_overlap_calculation(self):
        """Adjacent chunks should have configured overlap."""
        processor = DocumentProcessor(
            chunk_size=100,
            overlap=20
        )

        text = " ".join([f"word{i}" for i in range(500)])
        chunks = processor.chunk_text(text)

        # Check overlap between consecutive chunks
        for i in range(len(chunks) - 1):
            chunk1_end = chunks[i].content[-50:]  # Last 50 chars
            chunk2_start = chunks[i+1].content[:50]  # First 50 chars

            # Should have some overlap
            assert any(word in chunk2_start for word in chunk1_end.split())
```

#### test_embedding_manager.py
```python
class TestEmbeddingManager:
    """Test embedding generation and caching."""

    async def test_local_embedding_generation(self):
        """Local model should generate embeddings."""
        manager = EmbeddingManager(model="all-MiniLM-L6-v2")

        embedding = await manager.embed("Hello world")

        assert len(embedding) == 384  # Model dimension
        assert all(isinstance(x, float) for x in embedding)

    async def test_cloud_embedding_with_openai(self):
        """OpenAI API should generate embeddings."""
        manager = EmbeddingManager(model="openai")

        embedding = await manager.embed("Hello world")

        assert len(embedding) == 1536  # OpenAI dimension

    async def test_embedding_cache_hit(self):
        """Cache should return stored embeddings."""
        manager = EmbeddingManager()
        text = "Hello world"

        # First call - cache miss
        emb1 = await manager.embed(text)

        # Second call - cache hit
        emb2 = await manager.embed(text)

        assert emb1 == emb2
        assert manager.cache_hits == 1

    async def test_embedding_cache_miss(self):
        """Different text should miss cache."""
        manager = EmbeddingManager()

        emb1 = await manager.embed("Hello")
        emb2 = await manager.embed("World")

        assert emb1 != emb2
        assert manager.cache_misses == 2

    async def test_fallback_to_local_on_api_failure(self):
        """Should fallback to local on API error."""
        manager = EmbeddingManager(
            primary_model="openai",
            fallback_model="all-MiniLM-L6-v2"
        )

        # Simulate API failure
        with patch.object(manager, 'openai_embed', side_effect=APIError("Rate limit")):
            embedding = await manager.embed("Hello")

        # Should use local fallback
        assert len(embedding) == 384  # Local model dimension
```

#### test_chromadb_client.py
```python
class TestChromaDBClient:
    """Test ChromaDB operations."""

    async def test_create_collection(self, tmp_path):
        """Should create new collection."""
        client = ChromaDBClient(str(tmp_path))

        collection_id = await client.create_collection("test_collection")

        assert collection_id is not None
        assert await client.collection_exists("test_collection")

    async def test_add_documents_to_collection(self, tmp_path):
        """Should add documents to collection."""
        client = ChromaDBClient(str(tmp_path))
        collection_id = await client.create_collection("test")

        chunks = [
            Chunk(id="1", content="Python is great", embedding=[0.1, 0.2]),
            Chunk(id="2", content="JavaScript is fun", embedding=[0.3, 0.4])
        ]

        await client.add_documents(chunks, collection_id)

        count = await client.get_collection_count(collection_id)
        assert count == 2

    async def test_query_returns_top_k_results(self, tmp_path):
        """Query should return top K similar results."""
        client = ChromaDBClient(str(tmp_path))
        collection_id = await client.create_collection("test")

        # Add documents
        chunks = [
            Chunk(id=str(i), content=f"Document {i}", embedding=[i * 0.1] * 384)
            for i in range(10)
        ]
        await client.add_documents(chunks, collection_id)

        # Query
        query_embedding = [0.5] * 384
        results = await client.query(query_embedding, collection_id, top_k=3)

        assert len(results) == 3
        assert all(r.similarity >= 0 for r in results)

    async def test_similarity_threshold_filtering(self, tmp_path):
        """Should filter results below threshold."""
        client = ChromaDBClient(str(tmp_path))
        collection_id = await client.create_collection("test")

        # Add documents
        chunks = [
            Chunk(id="1", content="Very similar", embedding=[1.0] * 384),
            Chunk(id="2", content="Somewhat similar", embedding=[0.5] * 384),
            Chunk(id="3", content="Not similar", embedding=[0.0] * 384)
        ]
        await client.add_documents(chunks, collection_id)

        # Query with threshold
        query_embedding = [1.0] * 384
        results = await client.query(
            query_embedding,
            collection_id,
            top_k=10,
            min_similarity=0.7
        )

        # Should only return high-similarity results
        assert len(results) <= 2
        assert all(r.similarity >= 0.7 for r in results)

    async def test_delete_document_from_collection(self, tmp_path):
        """Should delete document and all chunks."""
        client = ChromaDBClient(str(tmp_path))
        collection_id = await client.create_collection("test")

        # Add documents
        chunks = [Chunk(id="1", content="Test", embedding=[0.1] * 384)]
        await client.add_documents(chunks, collection_id)

        # Delete
        await client.delete_document("1", collection_id)

        # Verify
        count = await client.get_collection_count(collection_id)
        assert count == 0
```

#### test_file_watcher.py
```python
class TestFileWatcher:
    """Test auto-indexing file watcher."""

    async def test_detect_file_creation(self, tmp_path):
        """Should detect new files."""
        watcher = FileWatcher()
        events = []

        watcher.on_file_change = lambda e: events.append(e)
        watcher.watch(str(tmp_path), patterns=["*.md"])

        # Create file
        (tmp_path / "test.md").write_text("# Test")

        await asyncio.sleep(0.5)  # Wait for event

        assert len(events) == 1
        assert events[0].event_type == "created"
        assert events[0].file_path.endswith("test.md")

    async def test_detect_file_modification(self, tmp_path):
        """Should detect file changes."""
        watcher = FileWatcher()
        events = []

        # Create file first
        test_file = tmp_path / "test.md"
        test_file.write_text("# Original")

        watcher.on_file_change = lambda e: events.append(e)
        watcher.watch(str(tmp_path), patterns=["*.md"])

        # Modify file
        test_file.write_text("# Modified")

        await asyncio.sleep(0.5)

        assert any(e.event_type == "modified" for e in events)

    async def test_debounce_rapid_changes(self, tmp_path):
        """Should debounce rapid file changes."""
        watcher = FileWatcher(debounce_seconds=1.0)
        events = []

        watcher.on_file_change = lambda e: events.append(e)
        watcher.watch(str(tmp_path), patterns=["*.md"])

        test_file = tmp_path / "test.md"

        # Rapid changes
        for i in range(10):
            test_file.write_text(f"# Version {i}")
            await asyncio.sleep(0.1)

        await asyncio.sleep(1.5)  # Wait for debounce

        # Should only fire once (debounced)
        assert len(events) <= 2  # create + modify (debounced)

    async def test_file_pattern_filtering(self, tmp_path):
        """Should only watch files matching patterns."""
        watcher = FileWatcher()
        events = []

        watcher.on_file_change = lambda e: events.append(e)
        watcher.watch(str(tmp_path), patterns=["*.py"])

        # Create matching file
        (tmp_path / "test.py").write_text("print('hello')")

        # Create non-matching file
        (tmp_path / "test.txt").write_text("hello")

        await asyncio.sleep(0.5)

        # Should only detect .py file
        assert len(events) == 1
        assert events[0].file_path.endswith(".py")
```

### Integration Tests

Located in `tests/integration/test_rag/`

#### test_rag_service.py
```python
class TestRAGService:
    """Test full RAG service integration."""

    async def test_full_indexing_pipeline(self, tmp_path):
        """Test complete flow: file → chunks → embeddings → storage."""
        service = RAGService(storage_path=str(tmp_path))
        await service.start()

        # Create test file
        test_file = tmp_path / "test.py"
        test_file.write_text('''
        def hello():
            """Say hello."""
            return "Hello"
        ''')

        # Create collection and ingest
        coll_id = await service.create_collection("test")
        result = await service.ingest_document(str(test_file), coll_id)

        # Verify
        assert result["documents_added"] == 1
        assert result["chunks_created"] >= 1

        # Query
        query_result = await service.query("hello function", coll_id)
        assert len(query_result["results"]) > 0
        assert "hello" in query_result["context"].lower()

    async def test_query_workflow(self, tmp_path):
        """Test query → embedding → search → results."""
        service = RAGService(storage_path=str(tmp_path))
        await service.start()

        # Setup collection with documents
        coll_id = await service.create_collection("test")

        # Add multiple documents
        for i in range(5):
            file_path = tmp_path / f"doc{i}.md"
            file_path.write_text(f"# Document {i}\n\nContent about topic {i}")
            await service.ingest_document(str(file_path), coll_id)

        # Query
        results = await service.query("topic 2", coll_id, top_k=2)

        # Verify
        assert len(results["results"]) == 2
        assert "topic 2" in results["results"][0].content.lower()
        assert results["results"][0].similarity > results["results"][1].similarity

    async def test_auto_indexing_on_file_change(self, tmp_path):
        """Test file watcher triggers auto-indexing."""
        service = RAGService(storage_path=str(tmp_path))
        await service.start()

        watch_folder = tmp_path / "watched"
        watch_folder.mkdir()

        # Create collection with auto-indexing
        coll_id = await service.create_collection(
            "test",
            config={"auto_watch_folders": [str(watch_folder)]}
        )

        # Create file in watched folder
        test_file = watch_folder / "auto.md"
        test_file.write_text("# Auto-indexed content")

        # Wait for auto-indexing
        await asyncio.sleep(3)

        # Verify indexed
        stats = await service.get_collection_stats(coll_id)
        assert stats["document_count"] == 1

    async def test_concurrent_indexing_jobs(self, tmp_path):
        """Test multiple files indexed concurrently."""
        service = RAGService(
            storage_path=str(tmp_path),
            max_concurrent_jobs=3
        )
        await service.start()

        coll_id = await service.create_collection("test")

        # Create many files
        files = []
        for i in range(20):
            file_path = tmp_path / f"file{i}.md"
            file_path.write_text(f"# File {i}\n\n" + "Content " * 100)
            files.append(str(file_path))

        # Ingest folder
        start_time = time.time()
        await service.ingest_folder(str(tmp_path), coll_id, recursive=False)
        duration = time.time() - start_time

        # Verify all indexed
        stats = await service.get_collection_stats(coll_id)
        assert stats["document_count"] == 20

        # Should be faster than sequential (rough check)
        # Sequential would be ~20 seconds, concurrent should be ~7 seconds
        assert duration < 15

    async def test_collection_management_lifecycle(self, tmp_path):
        """Test create, update, delete collection."""
        service = RAGService(storage_path=str(tmp_path))
        await service.start()

        # Create
        coll_id = await service.create_collection("test", config={
            "chunk_size": 512,
            "embedding_model": "local"
        })

        # Verify
        coll = await service.get_collection(coll_id)
        assert coll.name == "test"
        assert coll.config["chunk_size"] == 512

        # Update
        await service.update_collection(coll_id, config={
            "chunk_size": 1024
        })

        coll = await service.get_collection(coll_id)
        assert coll.config["chunk_size"] == 1024

        # Delete
        await service.delete_collection(coll_id)

        with pytest.raises(CollectionNotFoundError):
            await service.get_collection(coll_id)
```

#### test_rag_nodes.py
```python
class TestRAGNodes:
    """Test workflow node execution."""

    async def test_ingest_document_node_execution(self, tmp_path):
        """IngestDocumentNode should index files."""
        service = RAGService(storage_path=str(tmp_path))
        await service.start()

        coll_id = await service.create_collection("test")

        # Create test file
        test_file = tmp_path / "test.md"
        test_file.write_text("# Test Document")

        # Execute node
        node = IngestDocumentNode(rag_service=service)
        result = await node.execute({
            "file_path": str(test_file),
            "collection_id": coll_id
        })

        # Verify
        assert result["documents_added"] == 1
        assert result["chunks_created"] >= 1
        assert result["error"] is None

    async def test_query_knowledge_node_returns_context(self, tmp_path):
        """QueryKnowledgeNode should return search results."""
        service = RAGService(storage_path=str(tmp_path))
        await service.start()

        # Setup
        coll_id = await service.create_collection("test")
        test_file = tmp_path / "test.md"
        test_file.write_text("# Authentication\n\nJWT tokens are used.")
        await service.ingest_document(str(test_file), coll_id)

        # Execute node
        node = QueryKnowledgeNode(rag_service=service)
        result = await node.execute({
            "query": "How does auth work?",
            "collection_id": coll_id,
            "top_k": 5
        })

        # Verify
        assert len(result["results"]) > 0
        assert "JWT" in result["context"]
        assert result["error"] is None

    async def test_get_context_node_fits_token_limit(self, tmp_path):
        """GetContextNode should respect max_tokens."""
        service = RAGService(storage_path=str(tmp_path))
        await service.start()

        # Setup with long documents
        coll_id = await service.create_collection("test")
        for i in range(10):
            file_path = tmp_path / f"doc{i}.md"
            file_path.write_text("# Document\n\n" + " ".join(["word"] * 500))
            await service.ingest_document(str(file_path), coll_id)

        # Execute node
        node = GetContextNode(rag_service=service)
        result = await node.execute({
            "query": "document",
            "collection_ids": [coll_id],
            "max_tokens": 500
        })

        # Verify token limit respected
        assert result["token_count"] <= 500
        assert len(result["context"]) > 0

    async def test_node_error_handling(self, tmp_path):
        """Nodes should handle errors gracefully."""
        service = RAGService(storage_path=str(tmp_path))
        await service.start()

        # Query non-existent collection
        node = QueryKnowledgeNode(rag_service=service)
        result = await node.execute({
            "query": "test",
            "collection_id": "nonexistent",
            "top_k": 5
        })

        # Should not crash, return error
        assert result["results"] == []
        assert result["error"] is not None
        assert "not found" in result["error"].lower()
```

### E2E Tests

Located in `tests/e2e/test_rag_workflow.py`

```python
class TestRAGWorkflow:
    """Test complete user workflows."""

    async def test_create_collection_ingest_query_use_in_chat(self, page: Page):
        """Full workflow: Create → Ingest → Query → ChatNode."""
        # Navigate to Knowledge Bases
        page.click("text=AI")
        page.click("text=Knowledge Bases")

        # Create collection
        page.click("text=New Collection")
        page.fill("input[name=collection_name]", "TestDocs")
        page.click("button:has-text('Create')")

        # Wait for creation
        page.wait_for_selector("text=TestDocs")

        # Open workflow editor
        page.click("text=Workflows")
        page.click("text=New Workflow")

        # Add IngestDocument node
        page.click("text=RAG")
        page.drag_and_drop("text=Ingest Document", ".workflow-canvas")

        # Configure node
        page.click("text=Ingest Document")
        page.fill("input[name=file_path]", "tests/fixtures/sample.md")
        page.select_option("select[name=collection_id]", label="TestDocs")

        # Add QueryKnowledge node
        page.drag_and_drop("text=Query Knowledge", ".workflow-canvas")
        page.click("text=Query Knowledge")
        page.fill("input[name=query]", "What is this about?")

        # Add ChatNode
        page.drag_and_drop("text=AI Chat", ".workflow-canvas")
        page.click("text=AI Chat")
        page.fill("textarea[name=message]", "Based on: {{context}}")

        # Execute workflow
        page.click("button:has-text('Run')")

        # Verify results
        page.wait_for_selector("text=Workflow completed")
        chat_output = page.text_content(".node-output")
        assert len(chat_output) > 0

    async def test_auto_index_folder_query_updated_content(self, tmp_path, page: Page):
        """Auto-indexing detects changes and updates index."""
        watch_folder = tmp_path / "watched"
        watch_folder.mkdir()

        # Create collection with auto-indexing
        page.click("text=Knowledge Bases")
        page.click("text=New Collection")
        page.fill("input[name=collection_name]", "AutoIndexed")
        page.check("input[name=auto_update]")
        page.click("button:has-text('Add Folder')")
        page.fill("input[name=watch_folder]", str(watch_folder))
        page.click("button:has-text('Create')")

        # Create file in watched folder
        (watch_folder / "doc.md").write_text("# Original Content")

        # Wait for indexing
        await asyncio.sleep(3)

        # Query
        page.click("text=AutoIndexed")
        page.click("button:has-text('Query')")
        page.fill("input[name=query]", "content")
        page.click("button:has-text('Search')")

        # Verify original content found
        page.wait_for_selector("text=Original Content")

        # Modify file
        (watch_folder / "doc.md").write_text("# Updated Content")

        # Wait for re-indexing
        await asyncio.sleep(3)

        # Query again
        page.fill("input[name=query]", "updated")
        page.click("button:has-text('Search')")

        # Verify updated content found
        page.wait_for_selector("text=Updated Content")

    async def test_multi_collection_search_combine_results(self, page: Page):
        """GetContextNode searches multiple collections."""
        # Create two collections
        for name in ["Docs", "Code"]:
            page.click("text=New Collection")
            page.fill("input[name=collection_name]", name)
            page.click("button:has-text('Create')")

        # Ingest different content to each
        # (Workflow execution via UI - detailed steps omitted for brevity)

        # Use GetContext node with both collections
        page.click("text=Workflows")
        page.click("text=New Workflow")
        page.drag_and_drop("text=Get Context", ".workflow-canvas")

        # Configure multi-collection search
        page.click("text=Get Context")
        page.fill("input[name=query]", "authentication")
        page.check("input[value=Docs]")
        page.check("input[value=Code]")
        page.fill("input[name=max_tokens]", "1000")

        # Execute
        page.click("button:has-text('Run')")

        # Verify results from both collections
        output = page.text_content(".node-output")
        assert "Docs" in output or "Code" in output  # Source attribution

    async def test_large_document_ingestion_progress_tracking(self, tmp_path, page: Page):
        """Large ingestion shows real-time progress."""
        # Create large file
        large_file = tmp_path / "large.md"
        content = "# Large Document\n\n" + "\n\n".join([
            f"## Section {i}\n\nContent for section {i}"
            for i in range(1000)
        ])
        large_file.write_text(content)

        # Create collection
        page.click("text=New Collection")
        page.fill("input[name=collection_name]", "Large")
        page.click("button:has-text('Create')")

        # Ingest via UI
        page.click("text=Large")
        page.click("button:has-text('Add Documents')")
        page.set_input_files("input[type=file]", str(large_file))
        page.click("button:has-text('Upload')")

        # Verify progress bar appears
        page.wait_for_selector(".progress-bar")

        # Wait for completion
        page.wait_for_selector("text=Indexing complete", timeout=60000)

        # Verify stats updated
        stats_text = page.text_content(".collection-stats")
        assert "1000" in stats_text or "chunks" in stats_text
```

### Performance Benchmarks

#### Benchmark Suite (`tests/benchmarks/test_rag_performance.py`)

```python
class TestRAGPerformance:
    """Performance benchmarks for RAG operations."""

    @pytest.mark.benchmark
    async def test_index_100_markdown_files(self, benchmark, tmp_path):
        """Benchmark: Index 100 markdown files (1MB total)."""
        service = RAGService(storage_path=str(tmp_path))
        await service.start()

        # Create 100 files (~10KB each)
        files = []
        for i in range(100):
            file_path = tmp_path / f"doc{i}.md"
            content = f"# Document {i}\n\n" + " ".join(["word"] * 1000)
            file_path.write_text(content)
            files.append(str(file_path))

        coll_id = await service.create_collection("test")

        # Benchmark
        duration = benchmark(lambda: service.ingest_folder(str(tmp_path), coll_id))

        # Target: < 30 seconds
        assert duration < 30

    @pytest.mark.benchmark
    async def test_index_1000_python_files(self, benchmark, tmp_path):
        """Benchmark: Index 1000 Python files (10MB)."""
        service = RAGService(storage_path=str(tmp_path))
        await service.start()

        # Create 1000 files (~10KB each)
        for i in range(1000):
            file_path = tmp_path / f"module{i}.py"
            content = f'''
            def function_{i}():
                """Function {i}."""
                return {i}

            class Class_{i}:
                """Class {i}."""
                def method(self):
                    return {i}
            '''
            file_path.write_text(content)

        coll_id = await service.create_collection("test")

        # Benchmark
        duration = benchmark(lambda: service.ingest_folder(str(tmp_path), coll_id))

        # Target: < 3 minutes (180 seconds)
        assert duration < 180

    @pytest.mark.benchmark
    async def test_query_response_time(self, benchmark, tmp_path):
        """Benchmark: Query response time."""
        service = RAGService(storage_path=str(tmp_path))
        await service.start()

        # Setup: Index 1000 documents
        coll_id = await service.create_collection("test")
        for i in range(1000):
            file_path = tmp_path / f"doc{i}.md"
            file_path.write_text(f"# Document {i}\n\nContent about topic {i % 10}")
            await service.ingest_document(str(file_path), coll_id)

        # Benchmark query
        duration = benchmark(
            lambda: service.query("topic 5", coll_id, top_k=5)
        )

        # Target: < 500ms
        assert duration < 0.5

    @pytest.mark.benchmark
    async def test_embedding_cache_hit_rate(self, tmp_path):
        """Benchmark: Embedding cache effectiveness."""
        service = RAGService(storage_path=str(tmp_path))
        await service.start()

        coll_id = await service.create_collection("test")

        # Index same content multiple times (should hit cache)
        content = "# Repeated Content\n\n" + " ".join(["word"] * 100)

        for i in range(100):
            file_path = tmp_path / f"doc{i}.md"
            file_path.write_text(content)  # Same content
            await service.ingest_document(str(file_path), coll_id)

        # Check cache metrics
        cache_stats = await service.embedding_manager.get_cache_stats()
        hit_rate = cache_stats["hits"] / (cache_stats["hits"] + cache_stats["misses"])

        # Target: > 80% cache hit rate
        assert hit_rate > 0.8

    @pytest.mark.benchmark
    async def test_memory_usage(self, tmp_path):
        """Benchmark: Memory usage during indexing."""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        service = RAGService(storage_path=str(tmp_path))
        await service.start()

        # Index 1000 files
        coll_id = await service.create_collection("test")
        for i in range(1000):
            file_path = tmp_path / f"doc{i}.md"
            file_path.write_text("# Document\n\n" + " ".join(["word"] * 500))
            await service.ingest_document(str(file_path), coll_id)

        peak_memory = process.memory_info().rss
        memory_increase = (peak_memory - initial_memory) / 1024 / 1024  # MB

        # Target: < 500MB increase
        assert memory_increase < 500

    @pytest.mark.benchmark
    async def test_disk_usage(self, tmp_path):
        """Benchmark: Disk usage for indexed data."""
        import shutil

        service = RAGService(storage_path=str(tmp_path))
        await service.start()

        # Create 100MB of source files
        source_size = 0
        for i in range(100):
            file_path = tmp_path / "source" / f"doc{i}.md"
            file_path.parent.mkdir(exist_ok=True)
            content = "# Document\n\n" + " ".join(["word"] * 10000)
            file_path.write_text(content)
            source_size += len(content)

        # Index
        coll_id = await service.create_collection("test")
        await service.ingest_folder(str(tmp_path / "source"), coll_id)

        # Measure storage
        storage_size = shutil.disk_usage(str(tmp_path)).used
        ratio = storage_size / source_size

        # Target: < 2x source file size
        assert ratio < 2.0
```

#### Load Testing (`tests/load/test_rag_load.py`)

```python
class TestRAGLoad:
    """Load testing for RAG system."""

    @pytest.mark.load
    async def test_10000_documents_indexed(self, tmp_path):
        """Load test: 10,000 documents."""
        service = RAGService(storage_path=str(tmp_path))
        await service.start()

        coll_id = await service.create_collection("load_test")

        # Index 10,000 documents
        for i in range(10000):
            if i % 1000 == 0:
                print(f"Indexed {i}/10000 documents")

            file_path = tmp_path / f"doc{i}.md"
            file_path.write_text(f"# Document {i}\n\nContent {i}")
            await service.ingest_document(str(file_path), coll_id)

        # Verify
        stats = await service.get_collection_stats(coll_id)
        assert stats["document_count"] == 10000

        # Test query performance at scale
        start = time.time()
        results = await service.query("content", coll_id, top_k=10)
        query_time = time.time() - start

        assert len(results["results"]) == 10
        assert query_time < 1.0  # Still fast at scale

    @pytest.mark.load
    async def test_1000_concurrent_queries(self, tmp_path):
        """Load test: 1000 concurrent queries."""
        service = RAGService(storage_path=str(tmp_path))
        await service.start()

        # Setup: Index 1000 documents
        coll_id = await service.create_collection("load_test")
        for i in range(1000):
            file_path = tmp_path / f"doc{i}.md"
            file_path.write_text(f"# Topic {i % 10}\n\nContent {i}")
            await service.ingest_document(str(file_path), coll_id)

        # Concurrent queries
        async def query_task():
            return await service.query(f"topic {random.randint(0, 9)}", coll_id)

        start = time.time()
        results = await asyncio.gather(*[query_task() for _ in range(1000)])
        duration = time.time() - start

        # Verify all succeeded
        assert len(results) == 1000
        assert all(len(r["results"]) > 0 for r in results)

        # Reasonable throughput
        queries_per_second = 1000 / duration
        assert queries_per_second > 100  # At least 100 QPS

    @pytest.mark.load
    async def test_100_collections(self, tmp_path):
        """Load test: 100 collections."""
        service = RAGService(storage_path=str(tmp_path))
        await service.start()

        # Create 100 collections
        collection_ids = []
        for i in range(100):
            coll_id = await service.create_collection(f"collection_{i}")
            collection_ids.append(coll_id)

            # Add a few documents to each
            for j in range(10):
                file_path = tmp_path / f"coll{i}_doc{j}.md"
                file_path.write_text(f"# Doc {j} in Collection {i}")
                await service.ingest_document(str(file_path), coll_id)

        # Verify all collections
        for coll_id in collection_ids:
            stats = await service.get_collection_stats(coll_id)
            assert stats["document_count"] == 10

        # Test cross-collection query
        results = await service.query_multi_collections(
            "doc",
            collection_ids[:10],  # Query first 10 collections
            top_k=5
        )
        assert len(results["results"]) > 0
```

### Migration & Upgrade Testing

```python
class TestRAGMigrations:
    """Test database schema upgrades."""

    async def test_v1_to_v2_migration(self, tmp_path):
        """Test migrating from v1 schema to v2."""
        # Create v1 database
        v1_storage = RAGStorage(str(tmp_path), schema_version=1)
        # ... create v1 data

        # Run migration
        migrator = RAGMigrator(str(tmp_path))
        await migrator.migrate_to_v2()

        # Verify v2 schema
        v2_storage = RAGStorage(str(tmp_path))
        assert v2_storage.get_schema_version() == 2
        # ... verify data integrity

    async def test_backward_compatibility(self, tmp_path):
        """Test nodes work with older collection versions."""
        # Create old collection
        old_service = RAGService(version="1.0")
        coll_id = await old_service.create_collection("old")

        # New service should still work
        new_service = RAGService(version="2.0")
        results = await new_service.query("test", coll_id)
        assert results is not None
```

### Performance Targets Summary

| Metric | Target | Measurement |
|--------|--------|-------------|
| Index 100 markdown files (1MB) | < 30 seconds | Benchmark |
| Index 1000 Python files (10MB) | < 3 minutes | Benchmark |
| Query response (10k docs) | < 500ms | Benchmark |
| Embedding cache hit rate | > 80% | Production metric |
| Memory usage | < 500MB | Resource monitor |
| Disk usage | ~2x source size | Disk usage |
| Concurrent queries | > 100 QPS | Load test |
| Max collections | 100+ | Load test |
| Max documents per collection | 10,000+ | Load test |

---

## Dependencies

### New Dependencies to Add

```toml
# Add to pyproject.toml [project.optional-dependencies.ai]

[project.optional-dependencies]
ai = [
    # ... existing AI dependencies ...

    # RAG - Phase 5
    "sentence-transformers>=2.2.0",  # Local embedding models
    "tree-sitter>=0.21.0",  # Code parsing (multi-language AST)
    "tree-sitter-python>=0.21.0",  # Python AST
    "tree-sitter-javascript>=0.21.0",  # JS/TS AST
    "python-docx>=1.1.0",  # Word document parsing
    "openpyxl>=3.1.0",  # Already in main deps - Excel parsing
]
```

### Dependency Rationale

- **sentence-transformers**: Local embedding generation (all-MiniLM-L6-v2)
- **tree-sitter**: Multi-language code parsing with AST for adaptive chunking
- **python-docx**: Parse .docx files for office document support
- **chromadb**: Already in optional-dependencies.ai - vector database
- **pypdf**: Already in main dependencies - PDF parsing
- **openpyxl**: Already in main dependencies - Excel parsing

---

## Implementation Phases

### Phase 5.1: Core RAG Infrastructure (MVP)
**Goal**: Basic RAG working end-to-end

**Tasks**:
1. RAG Service skeleton with ChromaDB integration
2. DocumentProcessor with markdown/text chunking
3. EmbeddingManager with local model (all-MiniLM-L6-v2)
4. Basic SQLite metadata schema
5. IngestDocumentNode + QueryKnowledgeNode
6. Simple UI in Knowledge Bases tab

**Deliverables**:
- Can create collections
- Can ingest markdown/text files
- Can query and get results
- Basic UI for testing

**Timeline**: Sprint 1

### Phase 5.2: Advanced Document Types & Chunking
**Goal**: Support code, PDFs, Office docs with adaptive chunking

**Tasks**:
1. Implement code parsers (Python, JavaScript, TypeScript)
2. Add PDF text extraction
3. Add Office document parsing (.docx, .xlsx)
4. Adaptive chunking strategies per file type
5. Enhanced metadata extraction

**Deliverables**:
- Code-aware chunking (functions/classes)
- PDF and Office document support
- Improved retrieval quality

**Timeline**: Sprint 2

### Phase 5.3: Auto-Indexing & Cloud Embeddings
**Goal**: Production-ready with auto-indexing and cloud options

**Tasks**:
1. FileWatcher implementation
2. Auto-indexing queue and debouncing
3. Cloud embedding support (OpenAI, Cohere)
4. Embedding cache optimization
5. GetContextNode for multi-collection search

**Deliverables**:
- Automatic folder watching
- Cloud embedding options
- Smart context retrieval
- Complete node set

**Timeline**: Sprint 3

### Phase 5.4: Polish & Performance
**Goal**: Production-grade performance and UX

**Tasks**:
1. Performance optimizations (batching, parallel processing)
2. Comprehensive error handling
3. Complete UI implementation
4. Usage dashboard integration
5. Full test coverage
6. Documentation

**Deliverables**:
- Meets all performance targets
- Complete UI with query testing
- Production-ready error handling
- Full documentation

**Timeline**: Sprint 4

---

## Success Metrics

### Technical Metrics
- ✅ Index 100 markdown files in < 30 seconds
- ✅ Query response < 500ms for 10k documents
- ✅ Embedding cache hit rate > 80%
- ✅ Memory usage < 500MB during operation
- ✅ Support 10,000+ documents per collection
- ✅ 100+ concurrent queries per second

### User Metrics
- ✅ Users can create and query collections in < 2 minutes
- ✅ Auto-indexing detects changes within 5 seconds
- ✅ Query relevance > 80% (user feedback)
- ✅ Zero-config local embeddings work out-of-box

### Quality Metrics
- ✅ 100% test coverage for core RAG operations
- ✅ All error scenarios have graceful degradation
- ✅ Documentation complete for all features
- ✅ E2E tests cover primary user workflows

---

## Open Questions & Future Enhancements

### Open Questions (To Resolve During Implementation)

1. **Token Counting**: Which tokenizer to use?
   - Option A: tiktoken (OpenAI's tokenizer) - accurate but OpenAI-specific
   - Option B: sentence-transformers tokenizer - model-specific
   - Option C: Simple word count estimation - fast but inaccurate
   - **Recommendation**: Use tiktoken as default, with fallback to word estimation

2. **ChromaDB Persistence**: Local vs. Client-Server mode?
   - Local: Simpler, embedded in process
   - Client-Server: Scalable, but more complex setup
   - **Recommendation**: Start with local, add client-server option later

3. **Large File Handling**: Stream vs. Load?
   - Stream: Memory-efficient but complex
   - Load with pagination: Simpler but memory-intensive
   - **Recommendation**: Stream for files > 10MB

### Future Enhancements (Phase 6+)

**Phase 6: Media Support**
- Image OCR (tesseract)
- Audio transcription (whisper)
- Video frame extraction + transcription
- Multi-modal embeddings (CLIP)

**Conversation History RAG**
- Index chat histories
- Retrieve past conversations
- Continuation from history

**Advanced Features**
- Hybrid search (semantic + keyword)
- Re-ranking models
- Query expansion
- Federated search across multiple RAG systems

**Enterprise Features**
- Multi-tenancy support
- Access control per collection
- Audit logging
- Backup/restore collections

**Performance Enhancements**
- GPU acceleration for embeddings
- Distributed indexing
- Query result caching
- Incremental indexing (only changed chunks)

---

## Conclusion

This design provides a comprehensive RAG integration for Skynette that:

✅ **Fits the existing architecture**: Hybrid approach with background service + workflow nodes
✅ **Supports multiple use cases**: Document Q&A, codebase understanding, knowledge management
✅ **Scales gracefully**: From small personal projects to large enterprise collections
✅ **Works out-of-box**: Local embeddings require no configuration
✅ **Extensible**: Cloud embeddings, custom chunking, plugin architecture
✅ **Production-ready**: Comprehensive error handling, testing, performance targets

The phased implementation approach allows us to ship value early (Phase 5.1 MVP in Sprint 1) while building toward a complete, production-grade RAG system over 4 sprints.

**Ready to proceed with implementation planning?**
