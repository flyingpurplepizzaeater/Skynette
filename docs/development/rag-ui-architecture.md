# RAG UI Architecture

## Component Overview

```
AIHubView (5th tab)
└── KnowledgeBasesView
    ├── CollectionCard (grid display)
    ├── CollectionDialog (create/edit)
    ├── UploadDialog (file upload)
    │   └── ProgressTracker (progress display)
    └── QueryDialog (search interface)
```

## Data Flow

### Collection Management
```
User Click → CollectionDialog → RAGService.create_collection()
                                      ↓
                                RAGStorage (SQLite metadata)
                                      ↓
                            KnowledgeBasesView._invalidate_cache()
                                      ↓
                                 Reload & display
```

### Document Upload
```
File Selection → UploadDialog → RAGService.ingest_document() [parallel]
                                      ↓
                        DocumentProcessor.process_file()
                                      ↓
                        EmbeddingManager.embed_batch()
                                      ↓
                ChromaDBClient.add_chunks() + RAGStorage.save_document()
                                      ↓
                         ProgressTracker updates
```

### Query
```
User Query → QueryDialog → RAGService.query()
                                 ↓
                    EmbeddingManager.embed(query)
                                 ↓
                    ChromaDBClient.search()
                                 ↓
                    Convert to QueryResultUI
                                 ↓
                         Display results
```

## State Management

### Caching
- **Collections List**: 60-second cache
- **Query Results**: In-memory per dialog instance

### Cache Invalidation
- Collection create/update → invalidate collections cache
- Document upload → no cache (stats fetched on demand)

## Performance Optimizations

### Parallel Processing
- Upload: Max 5 concurrent files (asyncio.Semaphore)
- Embedding: Batch processing in backend

### UI Throttling
- Progress updates: Max 10/second
- Form validation: 300ms debounce

### Lazy Loading
- Collection stats: Fetched on load (not cached)
- Documents list: Not implemented (future)

## Error Handling

### Upload Errors
- Continue on failure, collect errors
- Classify by type: unsupported, permission, corrupted, embedding_failed
- Display summary at end

### Global Errors
- Network failures → show snack bar, keep cached data
- Validation errors → field-level error messages
- Duplicate names → specific error on name field

## Testing Strategy

### Unit Tests
- Data models: Validation, conversion
- Components: Rendering, state management
- Dialogs: Form validation, error handling

### Integration Tests
- Full workflows: Create → upload → query
- Error scenarios: Unsupported files, permission errors

### E2E Tests
- UI interactions: Click, fill, submit
- Navigation: Tab switching, dialog open/close
- Visual verification: Empty states, error messages

## Future Enhancements

### Sprint 2 Backfill
- Code file support (.py, .js, .ts)
- PDF text extraction
- Office documents (.docx, .xlsx)

### Sprint 3 Backfill
- Auto-indexing with file watchers
- Cloud embedding options (OpenAI, Cohere)
- Multi-collection search

### Future
- Advanced filtering (metadata, date range)
- Query history and saved queries
- Export results to CSV/JSON
- Background job system for large uploads
