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
    FOREIGN KEY (collection_id) REFERENCES rag_collections(id) ON DELETE CASCADE,
    UNIQUE(collection_id, source_path)
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
CREATE INDEX IF NOT EXISTS idx_documents_source_path ON rag_documents(source_path);
CREATE INDEX IF NOT EXISTS idx_chunks_document ON rag_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_chunks_embedding_hash ON rag_chunks(embedding_hash);
