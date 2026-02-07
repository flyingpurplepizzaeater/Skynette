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
            # Allow small floating point error (1e-10)
            assert -1e-10 <= result["similarity"] <= 1 + 1e-10

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
