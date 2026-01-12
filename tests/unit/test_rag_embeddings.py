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
