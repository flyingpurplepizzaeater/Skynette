# Phase 5 Sprint 4: RAG UI & Polish Design

**Date**: 2026-01-12
**Version**: 1.0
**Status**: Design Complete, Awaiting Implementation

---

## Executive Summary

Add Knowledge Bases tab to AI Hub with full UI for RAG collection management, document upload, and query testing. Includes comprehensive error handling, detailed progress feedback, and performance optimizations through parallel processing.

**Key Features**:
- Collection management UI (create, edit, delete collections)
- Multi-method document upload (file picker, drag & drop, folder selection)
- Query testing interface with similarity scoring
- Real-time progress tracking for uploads
- Comprehensive error handling with detailed error messages
- Performance optimizations (parallel processing, batching, caching)

**Scope Decisions**:
- Manual upload only (auto-indexing deferred to Sprint 3 backfill)
- Simple query interface (advanced filtering deferred to future sprints)
- Markdown and text files only (code/PDF/Office deferred to Sprint 2 backfill)
- Detailed progress tracking without background job system

---

## 1. Architecture & Integration

### 1.1 Component Hierarchy

```
AIHubView (existing)
└── Tab 5: Knowledge Bases
    └── KnowledgeBasesView
        ├── Header (title + "New Collection" button)
        ├── Collections Grid
        │   └── CollectionCard (repeated)
        │       ├── Stats display
        │       ├── Query button → QueryDialog
        │       └── Manage button → CollectionDialog
        ├── CollectionDialog (create/edit)
        │   ├── Form fields
        │   ├── Add Documents → UploadDialog
        │   └── Documents list
        ├── UploadDialog
        │   ├── File Picker tab
        │   ├── Drag & Drop tab
        │   ├── Folder Selection tab
        │   └── ProgressTracker
        └── QueryDialog
            ├── Query input
            ├── Options (Top K, Min Similarity)
            └── Results display
```

### 1.2 Backend Integration

**RAG Service Layer** (existing from Sprint 1):
- `RAGService` - Main orchestration (src/rag/service.py)
- `RAGStorage` - Metadata persistence (src/rag/storage.py)
- `ChromaDBClient` - Vector operations (src/rag/chromadb_client.py)
- `EmbeddingManager` - Embedding generation (src/rag/embeddings.py)
- `DocumentProcessor` - Chunking (src/rag/processor.py)

**UI → Backend Flow**:
```python
# Create collection
collection = await rag_service.create_collection(
    name="ProjectDocs",
    embedding_model="local",
    chunk_size=1024,
    chunk_overlap=128
)

# Upload documents
for file_path in selected_files:
    try:
        result = await rag_service.ingest_document(
            file_path=file_path,
            collection_id=collection.id
        )
        # Update progress UI
    except Exception as e:
        # Collect error for summary

# Query collection
results = await rag_service.query(
    query="How does auth work?",
    collection_id=collection.id,
    top_k=5,
    min_similarity=0.5
)
```

### 1.3 State Management

**View-Level State**:
- `collections: List[CollectionCardData]` - Cached list, refresh on mutations
- `selected_collection: Optional[str]` - Currently viewing/editing
- `upload_progress: Optional[UploadProgress]` - Active upload state
- `query_cache: Dict[str, List[QueryResultUI]]` - Recent query results

**Async Patterns**:
- All backend calls use `async/await`
- UI updates via `page.update()` after state changes
- Progress updates throttled (max 10/second)

---

## 2. UI Components

### 2.1 KnowledgeBasesView

**File**: `src/ui/views/knowledge_bases.py`

**Structure**:
```python
class KnowledgeBasesView(ft.Column):
    def __init__(self, page: ft.Page = None):
        super().__init__()
        self._page = page
        self.rag_service = RAGService()
        self.collections: List[CollectionCardData] = []
        self.expand = True

    def build(self):
        return ft.Column(
            controls=[
                self._build_header(),
                self._build_collections_grid(),
            ],
            expand=True,
            spacing=16,
        )

    def _build_header(self):
        return ft.Row(
            controls=[
                ft.Text("Knowledge Bases", size=28, weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                ft.Button(
                    "New Collection",
                    icon=ft.Icons.ADD,
                    on_click=self._on_new_collection,
                ),
            ],
        )

    def _build_collections_grid(self):
        if not self.collections:
            return self._build_empty_state()

        # Grid: 3 cards per row
        return ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        CollectionCard(coll, self._on_query, self._on_manage)
                        for coll in self.collections[i:i+3]
                    ],
                    wrap=True,
                )
                for i in range(0, len(self.collections), 3)
            ],
        )

    def _build_empty_state(self):
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(ft.Icons.FOLDER_OPEN, size=64),
                    ft.Text("No Knowledge Bases Yet", size=24),
                    ft.Text("Create a collection to start indexing documents"),
                    ft.Container(height=16),
                    ft.Button(
                        "Create Your First Collection",
                        icon=ft.Icons.ADD,
                        on_click=self._on_new_collection,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            alignment=ft.alignment.center,
            expand=True,
        )

    async def _load_collections(self):
        collections = await self.rag_service.list_collections()
        self.collections = [
            CollectionCardData.from_collection(c)
            for c in collections
        ]
        if self._page:
            self._page.update()
```

### 2.2 CollectionCard

**Reusable Component**:
```python
class CollectionCard(ft.Container):
    def __init__(self, data: CollectionCardData, on_query, on_manage):
        super().__init__()
        self.data = data
        self.on_query = on_query
        self.on_manage = on_manage

        self.content = ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.FOLDER, size=32),
                        ft.Text(data.name, size=20, weight=ft.FontWeight.W_500),
                    ],
                ),
                ft.Container(height=8),
                ft.Text(f"📄 {data.document_count} documents"),
                ft.Text(f"🧩 {data.chunk_count:,} chunks"),
                ft.Text(f"🕐 Last: {self._format_time_ago(data.last_updated)}"),
                ft.Text(f"💾 {self._format_bytes(data.storage_size_bytes)}"),
                ft.Container(height=16),
                ft.Row(
                    controls=[
                        ft.TextButton("Query", on_click=lambda _: on_query(data.id)),
                        ft.TextButton("Manage", on_click=lambda _: on_manage(data.id)),
                    ],
                    spacing=8,
                ),
            ],
        )

        self.width = 280
        self.padding = 16
        self.border = ft.border.all(1, ft.colors.OUTLINE)
        self.border_radius = 8

    def _format_time_ago(self, dt: datetime) -> str:
        delta = datetime.now(timezone.utc) - dt
        if delta.seconds < 60:
            return "just now"
        elif delta.seconds < 3600:
            return f"{delta.seconds // 60}m ago"
        elif delta.days == 0:
            return f"{delta.seconds // 3600}h ago"
        else:
            return f"{delta.days}d ago"

    def _format_bytes(self, bytes: int) -> str:
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes < 1024:
                return f"{bytes:.1f} {unit}"
            bytes /= 1024
        return f"{bytes:.1f} TB"
```

### 2.3 CollectionDialog

**Create/Edit Modal**:
```python
class CollectionDialog(ft.AlertDialog):
    def __init__(self, rag_service: RAGService, collection_id: Optional[str] = None):
        super().__init__()
        self.rag_service = rag_service
        self.collection_id = collection_id
        self.is_edit = collection_id is not None

        # Form fields
        self.name_field = ft.TextField(label="Name", hint_text="e.g., ProjectDocs")
        self.description_field = ft.TextField(
            label="Description (optional)",
            multiline=True,
            min_lines=2,
            max_lines=4,
        )

        # Embedding model selection
        self.embedding_radio = ft.RadioGroup(
            content=ft.Column([
                ft.Radio(value="local", label="Local (all-MiniLM-L6-v2) - Free, private"),
                ft.Radio(value="openai", label="OpenAI (text-embedding-3-small) - Higher quality"),
                ft.Radio(value="cohere", label="Cohere (embed-english-v3.0) - Alternative"),
            ]),
            value="local",
        )

        # Chunking settings
        self.chunk_size_field = ft.TextField(label="Chunk size (tokens)", value="1024")
        self.chunk_overlap_field = ft.TextField(label="Overlap (tokens)", value="128")
        self.max_chunk_field = ft.TextField(label="Max chunk size (tokens)", value="2048")

        self.title = ft.Text("New Collection" if not self.is_edit else "Edit Collection")
        self.content = ft.Column(
            controls=[
                ft.Text("Basic Information", weight=ft.FontWeight.BOLD),
                self.name_field,
                self.description_field,
                ft.Container(height=16),
                ft.Text("Embedding Model", weight=ft.FontWeight.BOLD),
                self.embedding_radio,
                ft.Container(height=16),
                ft.Text("Chunking Settings", weight=ft.FontWeight.BOLD),
                self.chunk_size_field,
                self.chunk_overlap_field,
                self.max_chunk_field,
            ],
            width=500,
            height=600,
            scroll=ft.ScrollMode.AUTO,
        )

        self.actions = [
            ft.TextButton("Cancel", on_click=self._on_cancel),
            ft.Button("Save", on_click=self._on_save),
        ]

    async def _on_save(self, e):
        # Validate
        errors = self._validate_fields()
        if errors:
            # Show errors
            return

        # Create or update
        if self.is_edit:
            await self.rag_service.update_collection(...)
        else:
            await self.rag_service.create_collection(
                name=self.name_field.value,
                description=self.description_field.value,
                embedding_model=self.embedding_radio.value,
                chunk_size=int(self.chunk_size_field.value),
                chunk_overlap=int(self.chunk_overlap_field.value),
                max_chunk_size=int(self.max_chunk_field.value),
            )

        self.open = False
        self.page.update()

    def _validate_fields(self) -> List[str]:
        errors = []

        # Name required, alphanumeric + underscores
        if not self.name_field.value:
            errors.append("Name is required")
        elif not re.match(r'^[a-zA-Z0-9_]+$', self.name_field.value):
            errors.append("Name must be alphanumeric and underscores only")

        # Chunk size validation
        try:
            chunk_size = int(self.chunk_size_field.value)
            if chunk_size < 256 or chunk_size > 4096:
                errors.append("Chunk size must be 256-4096")
        except ValueError:
            errors.append("Chunk size must be a number")

        # Similar for overlap and max_chunk

        return errors
```

### 2.4 UploadDialog

**Multi-Method Upload**:
```python
class UploadDialog(ft.AlertDialog):
    def __init__(self, rag_service: RAGService, collection_id: str, page: ft.Page):
        super().__init__()
        self.rag_service = rag_service
        self.collection_id = collection_id
        self.page = page
        self.selected_files: List[str] = []
        self.upload_progress: Optional[UploadProgress] = None

        # File picker
        self.file_picker = ft.FilePicker(on_result=self._on_files_selected)
        page.overlay.append(self.file_picker)

        # Folder picker
        self.folder_picker = ft.FilePicker(
            on_result=self._on_folder_selected,
            is_directory=True,
        )
        page.overlay.append(self.folder_picker)

        # Drag & drop
        self.drop_target = ft.DragTarget(
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Icon(ft.Icons.UPLOAD_FILE, size=48),
                        ft.Text("Drag files here"),
                        ft.Text("or click to browse", size=12, color=ft.colors.SECONDARY),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=40,
                border=ft.border.all(2, ft.colors.PRIMARY),
                border_radius=8,
            ),
            on_accept=self._on_files_dropped,
        )

        # Upload tabs
        self.upload_tabs = ft.Tabs(
            tabs=[
                ft.Tab(
                    text="File Picker",
                    content=ft.Column(
                        controls=[
                            ft.Button(
                                "Select Files",
                                icon=ft.Icons.FILE_OPEN,
                                on_click=lambda _: self.file_picker.pick_files(
                                    allowed_extensions=["md", "txt"],
                                    allow_multiple=True,
                                ),
                            ),
                        ],
                    ),
                ),
                ft.Tab(
                    text="Drag & Drop",
                    content=self.drop_target,
                ),
                ft.Tab(
                    text="Folder",
                    content=ft.Column(
                        controls=[
                            ft.Button(
                                "Select Folder",
                                icon=ft.Icons.FOLDER_OPEN,
                                on_click=lambda _: self.folder_picker.get_directory_path(),
                            ),
                            ft.Text(
                                "All .md and .txt files will be indexed recursively",
                                size=12,
                                italic=True,
                            ),
                        ],
                    ),
                ),
            ],
        )

        self.files_list = ft.Column()
        self.progress_tracker = ProgressTracker()

        self.title = ft.Text("Add Documents")
        self.content = ft.Column(
            controls=[
                self.upload_tabs,
                ft.Container(height=16),
                ft.Text("Selected Files:", weight=ft.FontWeight.BOLD),
                self.files_list,
                self.progress_tracker,
            ],
            width=600,
            height=500,
            scroll=ft.ScrollMode.AUTO,
        )

        self.actions = [
            ft.TextButton("Cancel", on_click=self._on_cancel),
            ft.Button(
                "Start Upload",
                on_click=self._on_start_upload,
                disabled=True,
            ),
        ]

    def _on_files_selected(self, e: ft.FilePickerResultEvent):
        if e.files:
            self.selected_files.extend([f.path for f in e.files])
            self._update_files_list()

    def _on_folder_selected(self, e: ft.FilePickerResultEvent):
        if e.path:
            # Recursively find .md and .txt files
            for root, dirs, files in os.walk(e.path):
                for file in files:
                    if file.endswith(('.md', '.txt')):
                        self.selected_files.append(os.path.join(root, file))
            self._update_files_list()

    def _update_files_list(self):
        self.files_list.controls = [
            ft.Row(
                controls=[
                    ft.Text(os.path.basename(f)),
                    ft.Container(expand=True),
                    ft.IconButton(
                        icon=ft.Icons.CLOSE,
                        on_click=lambda _, path=f: self._remove_file(path),
                    ),
                ],
            )
            for f in self.selected_files
        ]

        # Enable upload button
        self.actions[1].disabled = len(self.selected_files) == 0
        self.page.update()

    async def _on_start_upload(self, e):
        self.upload_progress = UploadProgress(
            total_files=len(self.selected_files),
            processed_files=0,
            current_file="",
            status="processing",
            errors=[],
        )

        # Process files in parallel (max 5 concurrent)
        semaphore = asyncio.Semaphore(5)

        async def process_file(file_path: str):
            async with semaphore:
                self.upload_progress.current_file = os.path.basename(file_path)
                self.progress_tracker.update(self.upload_progress)

                try:
                    await self.rag_service.ingest_document(
                        file_path=file_path,
                        collection_id=self.collection_id,
                    )
                    self.upload_progress.processed_files += 1
                except Exception as e:
                    self.upload_progress.errors.append(
                        UploadError(
                            file_path=file_path,
                            error_message=str(e),
                            error_type=self._classify_error(e),
                        )
                    )
                finally:
                    self.progress_tracker.update(self.upload_progress)

        # Process all files
        await asyncio.gather(*[process_file(f) for f in self.selected_files])

        # Show completion
        self.upload_progress.status = "completed"
        self.progress_tracker.update(self.upload_progress)
        self._show_completion_summary()
```

### 2.5 ProgressTracker

**Real-Time Progress Display**:
```python
class ProgressTracker(ft.Column):
    def __init__(self):
        super().__init__()
        self.visible = False

        self.overall_progress = ft.ProgressBar(width=500)
        self.current_file_text = ft.Text("")
        self.file_status_list = ft.Column()
        self.error_summary = ft.Column()

        self.controls = [
            ft.Text("Upload Progress", weight=ft.FontWeight.BOLD),
            self.overall_progress,
            self.current_file_text,
            ft.Container(height=8),
            ft.Text("Recent Files:", size=12),
            self.file_status_list,
            self.error_summary,
        ]

    def update(self, progress: UploadProgress):
        self.visible = True

        # Overall progress
        self.overall_progress.value = progress.processed_files / progress.total_files

        # Current file
        self.current_file_text.value = (
            f"Processing {progress.current_file} "
            f"({progress.processed_files}/{progress.total_files})..."
        )

        # Recent files (last 5)
        # Implementation shows ✅/⏳/❌ icons with filenames

        # Error summary
        if progress.errors:
            self.error_summary.controls = [
                ft.Container(height=8),
                ft.Text(f"⚠️ {len(progress.errors)} files failed:", color=ft.colors.ERROR),
                ft.Column(
                    controls=[
                        ft.Text(f"  • {e.file_path}: {e.error_message}", size=12)
                        for e in progress.errors[:5]
                    ],
                ),
            ]

        if self.page:
            self.page.update()
```

### 2.6 QueryDialog

**Search Interface**:
```python
class QueryDialog(ft.AlertDialog):
    def __init__(self, rag_service: RAGService, collection_id: str, collection_name: str):
        super().__init__()
        self.rag_service = rag_service
        self.collection_id = collection_id

        self.query_field = ft.TextField(
            label="Query",
            hint_text="Ask a question about your documents...",
            multiline=True,
            min_lines=2,
            max_lines=4,
        )

        self.top_k_slider = ft.Slider(
            min=1,
            max=10,
            value=5,
            divisions=9,
            label="Top {value} results",
        )

        self.min_similarity_slider = ft.Slider(
            min=0.0,
            max=1.0,
            value=0.5,
            divisions=10,
            label="Min similarity: {value}",
        )

        self.results_column = ft.Column()
        self.query_time_text = ft.Text("")

        self.title = ft.Text(f'Query "{collection_name}"')
        self.content = ft.Column(
            controls=[
                ft.Text("Test Query", weight=ft.FontWeight.BOLD),
                self.query_field,
                ft.Container(height=8),
                ft.Text("Options", weight=ft.FontWeight.BOLD),
                ft.Row([ft.Text("Top K results:"), self.top_k_slider]),
                ft.Row([ft.Text("Min similarity:"), self.min_similarity_slider]),
                ft.Container(height=8),
                ft.Button("Search", on_click=self._on_search),
                ft.Divider(),
                self.query_time_text,
                self.results_column,
            ],
            width=700,
            height=600,
            scroll=ft.ScrollMode.AUTO,
        )

        self.actions = [ft.TextButton("Close", on_click=lambda _: self._close())]

    async def _on_search(self, e):
        if not self.query_field.value:
            return

        start_time = time.time()

        results = await self.rag_service.query(
            query=self.query_field.value,
            collection_id=self.collection_id,
            top_k=int(self.top_k_slider.value),
            min_similarity=self.min_similarity_slider.value,
        )

        query_time_ms = int((time.time() - start_time) * 1000)

        # Display results
        self.query_time_text.value = f"Found {len(results)} results in {query_time_ms}ms"

        if not results:
            self.results_column.controls = [
                ft.Container(
                    content=ft.Text(
                        "No results found. Try a different query or lower min similarity.",
                        italic=True,
                    ),
                    padding=20,
                )
            ]
        else:
            self.results_column.controls = [
                self._build_result_card(i + 1, r)
                for i, r in enumerate(results)
            ]

        self.page.update()

    def _build_result_card(self, index: int, result: QueryResultUI) -> ft.Container:
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text(
                                f"{index}. {result.source_file} (similarity: {result.similarity:.2f})",
                                weight=ft.FontWeight.BOLD,
                            ),
                            ft.Container(expand=True),
                            ft.IconButton(
                                icon=ft.Icons.COPY,
                                tooltip="Copy chunk text",
                                on_click=lambda _, text=result.chunk_content: self._copy_text(text),
                            ),
                        ],
                    ),
                    ft.Container(
                        content=ft.Text(
                            result.chunk_content[:500] + ("..." if len(result.chunk_content) > 500 else ""),
                            font_family="monospace",
                            size=12,
                        ),
                        bgcolor=ft.colors.SURFACE_VARIANT,
                        padding=12,
                        border_radius=4,
                    ),
                ],
            ),
            border=ft.border.all(1, ft.colors.OUTLINE),
            border_radius=8,
            padding=12,
            margin=ft.margin.only(bottom=8),
        )

    def _copy_text(self, text: str):
        self.page.set_clipboard(text)
        self.page.show_snack_bar(ft.SnackBar(content=ft.Text("Copied to clipboard")))
```

---

## 3. Data Models

### 3.1 UI Data Structures

```python
from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any, Optional, Literal

@dataclass
class CollectionCardData:
    """UI representation of a collection."""
    id: str
    name: str
    description: str
    document_count: int
    chunk_count: int
    last_updated: datetime
    storage_size_bytes: int
    embedding_model: str

    @classmethod
    def from_collection(cls, collection: Collection) -> 'CollectionCardData':
        # Convert backend Collection model to UI model
        # Fetch stats from storage
        pass

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
        return (self.processed_files / self.total_files) * 100 if self.total_files > 0 else 0

@dataclass
class UploadError:
    """Individual file error."""
    file_path: str
    error_message: str
    error_type: str  # "unsupported", "permission", "corrupted", "embedding_failed"

@dataclass
class QueryResultUI:
    """UI representation of query result."""
    chunk_content: str
    source_file: str
    similarity: float
    metadata: Dict[str, Any]

    @classmethod
    def from_backend_result(cls, result: Dict[str, Any]) -> 'QueryResultUI':
        return cls(
            chunk_content=result["content"],
            source_file=result["metadata"]["source_path"],
            similarity=result["similarity"],
            metadata=result["metadata"],
        )
```

---

## 4. Performance Optimizations

### 4.1 Parallel Processing

**Upload Processing**:
```python
# Limit concurrent file processing
semaphore = asyncio.Semaphore(5)

async def process_file_with_limit(file_path: str):
    async with semaphore:
        return await rag_service.ingest_document(file_path, collection_id)

# Process all files in parallel (max 5 at once)
results = await asyncio.gather(
    *[process_file_with_limit(f) for f in selected_files],
    return_exceptions=True
)
```

**Embedding Batching** (already implemented in EmbeddingManager):
```python
# Backend automatically batches embeddings
# UI just calls ingest_document, backend handles batching
chunks = processor.process_file(file_path)
embeddings = await embedding_manager.embed_batch([c.content for c in chunks])
```

### 4.2 UI Optimizations

**Progress Update Throttling**:
```python
class ProgressTracker:
    def __init__(self):
        self.last_update = 0
        self.update_interval = 0.1  # Max 10 updates/second

    def update(self, progress: UploadProgress):
        now = time.time()
        if now - self.last_update < self.update_interval:
            return  # Skip update

        self.last_update = now
        # Update UI
```

**Collection List Caching**:
```python
class KnowledgeBasesView:
    def __init__(self):
        self.collections_cache: Optional[List[CollectionCardData]] = None
        self.cache_timestamp: Optional[datetime] = None
        self.cache_ttl = 60  # seconds

    async def _load_collections(self):
        now = datetime.now()
        if self.collections_cache and self.cache_timestamp:
            if (now - self.cache_timestamp).seconds < self.cache_ttl:
                return self.collections_cache  # Use cache

        # Refresh from backend
        self.collections_cache = await self._fetch_collections()
        self.cache_timestamp = now
        return self.collections_cache
```

**Query Result Caching**:
```python
class QueryDialog:
    def __init__(self):
        self.query_cache: Dict[str, List[QueryResultUI]] = {}
        self.max_cache_size = 50

    async def _on_search(self, e):
        cache_key = f"{self.query_field.value}:{self.top_k_slider.value}:{self.min_similarity_slider.value}"

        if cache_key in self.query_cache:
            results = self.query_cache[cache_key]
        else:
            results = await self.rag_service.query(...)

            # Add to cache (LRU eviction)
            if len(self.query_cache) >= self.max_cache_size:
                self.query_cache.pop(next(iter(self.query_cache)))
            self.query_cache[cache_key] = results

        self._display_results(results)
```

### 4.3 Memory Management

**Chunk Preview Truncation**:
```python
def _build_result_card(self, result: QueryResultUI):
    # Show first 500 chars + ellipsis
    preview = result.chunk_content[:500]
    if len(result.chunk_content) > 500:
        preview += "..."

    # Full text available on copy
    return ft.Container(
        content=ft.Text(preview, font_family="monospace"),
        # ...
    )
```

**File Streaming** (in DocumentProcessor):
```python
def process_file(self, file_path: str) -> List[Chunk]:
    # Don't load entire file into memory
    with open(file_path, 'r', encoding='utf-8') as f:
        # Process in chunks
        for line in f:
            # Chunk logic
            pass
```

---

## 5. Error Handling

### 5.1 Upload Error Scenarios

**Unsupported File Type**:
```python
try:
    chunks = processor.process_file(file_path)
except UnsupportedFileTypeError as e:
    return UploadError(
        file_path=file_path,
        error_message="PDF support coming in Sprint 2",
        error_type="unsupported"
    )
```

**File Access Errors**:
```python
try:
    with open(file_path, 'r') as f:
        content = f.read()
except FileNotFoundError:
    return UploadError(
        file_path=file_path,
        error_message="File not found",
        error_type="permission"
    )
except PermissionError:
    return UploadError(
        file_path=file_path,
        error_message="Permission denied",
        error_type="permission"
    )
```

**Parsing Errors**:
```python
try:
    chunks = processor.chunk_markdown(content)
except Exception as e:
    return UploadError(
        file_path=file_path,
        error_message=f"Failed to parse: {str(e)}",
        error_type="corrupted"
    )
```

**Embedding Failures**:
```python
try:
    embeddings = await embedding_manager.embed_batch(chunk_texts)
except Exception as e:
    # Retry once
    try:
        await asyncio.sleep(1)
        embeddings = await embedding_manager.embed_batch(chunk_texts)
    except Exception as retry_e:
        return UploadError(
            file_path=file_path,
            error_message=f"Embedding failed: {str(retry_e)}",
            error_type="embedding_failed"
        )
```

### 5.2 Query Error Scenarios

**No Results**:
```python
results = await rag_service.query(...)
if not results:
    # Show empty state
    self.results_column.controls = [
        ft.Text(
            "No results found. Try:\n"
            "• Different keywords\n"
            "• Lower min similarity threshold\n"
            "• Adding more documents to this collection",
            italic=True
        )
    ]
```

**Collection Not Found**:
```python
try:
    results = await rag_service.query(query, collection_id, ...)
except CollectionNotFoundError:
    self.page.show_snack_bar(
        ft.SnackBar(
            content=ft.Text("Collection no longer exists. Refreshing..."),
            bgcolor=ft.colors.ERROR
        )
    )
    await self.parent_view._load_collections()
    self.open = False
```

**Embedding Error**:
```python
try:
    results = await rag_service.query(...)
except EmbeddingError as e:
    self.page.show_snack_bar(
        ft.SnackBar(
            content=ft.Text(f"Failed to process query: {str(e)}"),
            bgcolor=ft.colors.ERROR
        )
    )
```

### 5.3 Collection Management Errors

**Duplicate Name**:
```python
try:
    await rag_service.create_collection(name=name, ...)
except DuplicateCollectionError:
    self.name_field.error_text = "Collection name already exists"
    self.page.update()
```

**Validation Errors**:
```python
def _validate_fields(self) -> Dict[str, str]:
    errors = {}

    if not self.name_field.value:
        errors['name'] = "Name is required"
    elif not re.match(r'^[a-zA-Z0-9_]+$', self.name_field.value):
        errors['name'] = "Name must be alphanumeric and underscores only"

    try:
        chunk_size = int(self.chunk_size_field.value)
        if chunk_size < 256 or chunk_size > 4096:
            errors['chunk_size'] = "Must be 256-4096"
    except ValueError:
        errors['chunk_size'] = "Must be a number"

    # Show errors on fields
    for field_name, error_msg in errors.items():
        field = getattr(self, f"{field_name}_field")
        field.error_text = error_msg

    return errors
```

**Delete Confirmation**:
```python
def _on_delete_collection(self, e):
    # Show confirmation dialog
    confirm_dialog = ft.AlertDialog(
        title=ft.Text("Delete Collection?"),
        content=ft.Text(
            f"This will delete {self.document_count} documents and "
            f"{self.chunk_count} chunks. This cannot be undone."
        ),
        actions=[
            ft.TextButton("Cancel", on_click=lambda _: self._close_confirm()),
            ft.Button(
                "Delete",
                bgcolor=ft.colors.ERROR,
                on_click=self._confirm_delete,
            ),
        ],
    )
    self.page.dialog = confirm_dialog
    confirm_dialog.open = True
    self.page.update()
```

### 5.4 Global Error Handling

**Database Connection Lost**:
```python
# In main view
try:
    await rag_service.list_collections()
except DatabaseConnectionError:
    self.page.show_snack_bar(
        ft.SnackBar(
            content=ft.Text("Database connection lost. Reconnecting..."),
            bgcolor=ft.colors.ERROR,
            duration=5000,
        )
    )
    # Auto-retry
    await asyncio.sleep(2)
    await self._load_collections()
```

**Disk Full**:
```python
try:
    await rag_service.ingest_document(file_path, collection_id)
except DiskFullError:
    return UploadError(
        file_path=file_path,
        error_message="Storage full. Free up space and try again.",
        error_type="storage_full"
    )
```

**Embedding Model Unavailable**:
```python
try:
    embedding_manager = EmbeddingManager(model="all-MiniLM-L6-v2")
except ModelNotFoundError:
    # Show setup instructions
    self.page.show_snack_bar(
        ft.SnackBar(
            content=ft.Text(
                "Local embedding model not found. "
                "It will download automatically (80MB). "
                "Or choose a cloud embedding option."
            ),
            duration=10000,
        )
    )
```

---

## 6. Testing Strategy

### 6.1 Unit Tests

**File**: `tests/unit/test_knowledge_bases_view.py`

```python
import pytest
from src.ui.views.knowledge_bases import CollectionCardData, UploadProgress, UploadError

class TestCollectionCardData:
    def test_create_collection_card_data(self):
        data = CollectionCardData(
            id="coll-123",
            name="ProjectDocs",
            description="Technical documentation",
            document_count=45,
            chunk_count=234,
            last_updated=datetime.now(timezone.utc),
            storage_size_bytes=1024 * 1024 * 12,  # 12 MB
            embedding_model="local",
        )

        assert data.name == "ProjectDocs"
        assert data.document_count == 45

class TestUploadProgress:
    def test_percentage_calculation(self):
        progress = UploadProgress(
            total_files=10,
            processed_files=5,
            current_file="test.md",
            status="processing",
            errors=[],
        )

        assert progress.percentage == 50.0

    def test_percentage_zero_files(self):
        progress = UploadProgress(
            total_files=0,
            processed_files=0,
            current_file="",
            status="pending",
            errors=[],
        )

        assert progress.percentage == 0.0

class TestUploadError:
    def test_create_upload_error(self):
        error = UploadError(
            file_path="/path/to/file.pdf",
            error_message="PDF support coming in Sprint 2",
            error_type="unsupported",
        )

        assert error.error_type == "unsupported"
        assert "Sprint 2" in error.error_message

class TestValidation:
    def test_validate_collection_name(self):
        # Valid names
        assert validate_collection_name("ProjectDocs") == True
        assert validate_collection_name("test_123") == True

        # Invalid names
        assert validate_collection_name("") == False
        assert validate_collection_name("my-collection") == False  # hyphen
        assert validate_collection_name("my collection") == False  # space

    def test_validate_chunk_size(self):
        assert validate_chunk_size(1024) == True
        assert validate_chunk_size(256) == True
        assert validate_chunk_size(4096) == True

        assert validate_chunk_size(100) == False  # too small
        assert validate_chunk_size(5000) == False  # too large
```

### 6.2 Integration Tests

**File**: `tests/integration/test_knowledge_bases_flow.py`

```python
import pytest
from src.rag.service import RAGService
from src.ui.views.knowledge_bases import KnowledgeBasesView

@pytest.mark.asyncio
class TestKnowledgeBasesFlow:
    async def test_create_collection_upload_query(self, tmp_path):
        """Full workflow: create → upload → query."""
        rag_service = RAGService(storage_path=str(tmp_path / "test.db"))

        # Create collection
        collection = await rag_service.create_collection(
            name="TestCollection",
            embedding_model="local",
            chunk_size=1024,
            chunk_overlap=128,
        )

        assert collection.name == "TestCollection"

        # Create test file
        test_file = tmp_path / "test.md"
        test_file.write_text("# Test Document\n\nThis is a test document for RAG.")

        # Upload document
        result = await rag_service.ingest_document(
            file_path=str(test_file),
            collection_id=collection.id,
        )

        assert result["status"] == "success"
        assert result["chunks_created"] > 0

        # Query collection
        results = await rag_service.query(
            query="test document",
            collection_id=collection.id,
            top_k=5,
            min_similarity=0.3,
        )

        assert len(results) > 0
        assert results[0]["similarity"] > 0.5
        assert "test document" in results[0]["content"].lower()

    async def test_upload_multiple_files_with_errors(self, tmp_path):
        """Upload multiple files, some succeed, some fail."""
        rag_service = RAGService(storage_path=str(tmp_path / "test.db"))
        collection = await rag_service.create_collection(name="Test")

        # Create valid files
        valid1 = tmp_path / "valid1.md"
        valid1.write_text("Valid document 1")

        valid2 = tmp_path / "valid2.txt"
        valid2.write_text("Valid document 2")

        # Create unsupported file
        invalid = tmp_path / "invalid.pdf"
        invalid.write_text("PDF content")

        # Upload all files
        files = [str(valid1), str(valid2), str(invalid)]
        results = []
        errors = []

        for file_path in files:
            try:
                result = await rag_service.ingest_document(file_path, collection.id)
                results.append(result)
            except Exception as e:
                errors.append(UploadError(file_path, str(e), "unsupported"))

        assert len(results) == 2  # 2 succeeded
        assert len(errors) == 1  # 1 failed
        assert "invalid.pdf" in errors[0].file_path

    async def test_delete_collection(self, tmp_path):
        """Delete collection removes all data."""
        rag_service = RAGService(storage_path=str(tmp_path / "test.db"))

        collection = await rag_service.create_collection(name="ToDelete")
        collection_id = collection.id

        # Add document
        test_file = tmp_path / "test.md"
        test_file.write_text("Test content")
        await rag_service.ingest_document(str(test_file), collection_id)

        # Verify exists
        collections = await rag_service.list_collections()
        assert any(c.id == collection_id for c in collections)

        # Delete
        await rag_service.delete_collection(collection_id)

        # Verify deleted
        collections = await rag_service.list_collections()
        assert not any(c.id == collection_id for c in collections)
```

### 6.3 E2E Tests

**File**: `tests/e2e/test_knowledge_bases_ui.py`

```python
import pytest
from playwright.sync_api import Page, expect

@pytest.mark.e2e
class TestKnowledgeBasesUI:
    def test_create_collection_and_upload(self, page: Page, app_url: str):
        """Full UI workflow: navigate, create, upload, query."""
        page.goto(app_url)

        # Navigate to Knowledge Bases tab
        page.click("text=Knowledge Bases")

        # Empty state should show
        expect(page.locator("text=No Knowledge Bases Yet")).to_be_visible()

        # Create collection
        page.click("text=Create Your First Collection")
        page.fill("input[label='Name']", "TestCollection")
        page.click("text=Save")

        # Collection card should appear
        expect(page.locator("text=TestCollection")).to_be_visible()

        # Open manage dialog
        page.click("text=Manage")

        # Add documents (would need file picker interaction)
        # This is simplified - actual test would use FilePicker

        # Close dialog
        page.click("text=Cancel")

    def test_query_collection(self, page: Page, app_url: str, test_collection_id: str):
        """Test query interface."""
        page.goto(app_url)
        page.click("text=Knowledge Bases")

        # Click Query on test collection
        page.click(f"[data-collection-id='{test_collection_id}'] >> text=Query")

        # Enter query
        page.fill("textarea[label='Query']", "test query")

        # Adjust options
        page.locator("input[type='range'][label*='Top']").fill("3")

        # Search
        page.click("text=Search")

        # Results should appear
        expect(page.locator("text=Found")).to_be_visible()
        expect(page.locator("text=similarity:")).to_be_visible()

    def test_drag_and_drop_upload(self, page: Page, app_url: str, test_collection_id: str):
        """Test drag & drop file upload."""
        page.goto(app_url)
        page.click("text=Knowledge Bases")

        # Open manage → Add documents → Drag & Drop tab
        page.click(f"[data-collection-id='{test_collection_id}'] >> text=Manage")
        page.click("text=Add Documents")
        page.click("text=Drag & Drop")

        # Simulate drag & drop
        # (Playwright supports file upload simulation)
        with page.expect_file_chooser() as fc_info:
            page.click("[data-testid='drop-target']")

        file_chooser = fc_info.value
        file_chooser.set_files("tests/fixtures/test_document.md")

        # Verify file appears in list
        expect(page.locator("text=test_document.md")).to_be_visible()

        # Start upload
        page.click("text=Start Upload")

        # Progress should show
        expect(page.locator("text=Upload Progress")).to_be_visible()
```

---

## 7. Implementation Plan Reference

This design document serves as the foundation for the implementation plan. Key implementation tasks:

1. **Setup** - Create KnowledgeBasesView skeleton, integrate into AI Hub
2. **Collection Management** - CollectionCard, CollectionDialog (create/edit/delete)
3. **Upload Flow** - UploadDialog with 3 methods, ProgressTracker
4. **Query Interface** - QueryDialog with results display
5. **Error Handling** - Comprehensive error scenarios
6. **Performance** - Parallel processing, caching, throttling
7. **Testing** - Unit, integration, E2E tests
8. **Polish** - UI refinements, accessibility, documentation

---

## 8. Success Criteria

### 8.1 Functional Requirements

- ✅ Users can create/edit/delete collections via UI
- ✅ Users can upload documents via file picker, drag & drop, or folder selection
- ✅ Users can query collections and see results with similarity scores
- ✅ Upload progress shows file-by-file status
- ✅ Errors are collected and displayed with specific messages
- ✅ All operations work with markdown and text files

### 8.2 Performance Requirements

- ✅ Upload 50 markdown files (total 5MB) in < 30 seconds
- ✅ Query response < 500ms for collections with 1000+ chunks
- ✅ UI remains responsive during uploads (progress updates throttled)
- ✅ Collection list loads in < 1 second

### 8.3 Usability Requirements

- ✅ Empty states guide users to first actions
- ✅ Form validation provides clear, immediate feedback
- ✅ Error messages are specific and actionable
- ✅ Progress indicators show what's happening
- ✅ Confirmation dialogs prevent accidental data loss

### 8.4 Quality Requirements

- ✅ 100% unit test coverage for data models and validation
- ✅ Integration tests cover create → upload → query flow
- ✅ E2E tests verify UI interactions work end-to-end
- ✅ No memory leaks during large uploads
- ✅ Graceful degradation when backend unavailable

---

## 9. Future Enhancements (Deferred)

**Auto-Indexing** (Sprint 3 backfill):
- File watchers monitoring configured directories
- Auto-update collections when files change
- Debouncing to avoid excessive reindexing

**Advanced Document Types** (Sprint 2 backfill):
- Code parsing (Python, JavaScript, TypeScript)
- PDF text extraction
- Office document support (.docx, .xlsx)

**Advanced Query Features** (Future):
- Multi-collection search (GetContextNode)
- Metadata filtering (file type, date range, custom tags)
- Query history and saved queries
- Export results to CSV/JSON

**Performance Enhancements** (Future):
- Background job system for large uploads
- Incremental indexing (only changed portions)
- Query result pagination
- Compression for stored chunks

**UI Polish** (Future):
- Dark mode support
- Keyboard shortcuts
- Accessibility improvements (screen reader support, keyboard navigation)
- Mobile responsive design

---

## Appendix A: File Structure

```
src/
├── ui/
│   └── views/
│       ├── knowledge_bases.py          # Main view
│       └── components/
│           ├── collection_card.py      # Collection card component
│           ├── collection_dialog.py    # Create/edit dialog
│           ├── upload_dialog.py        # Upload interface
│           ├── progress_tracker.py     # Progress display
│           └── query_dialog.py         # Query interface
│
├── rag/                                # Backend (existing from Sprint 1)
│   ├── service.py
│   ├── storage.py
│   ├── chromadb_client.py
│   ├── embeddings.py
│   ├── processor.py
│   └── models.py
│
tests/
├── unit/
│   ├── test_knowledge_bases_view.py
│   └── test_knowledge_bases_components.py
├── integration/
│   └── test_knowledge_bases_flow.py
└── e2e/
    └── test_knowledge_bases_ui.py
```

---

## Appendix B: Design Mockups

See Section 6 of the Phase 5 RAG Integration Design document for detailed UI mockups:
- Main view with collection cards
- Empty state
- Collection management dialog
- Query testing interface
- Upload progress display

---

**End of Design Document**
