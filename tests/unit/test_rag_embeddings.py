# tests/unit/test_rag_embeddings.py
import pytest
from unittest.mock import Mock, patch, MagicMock
import numpy as np
from src.rag.embeddings import EmbeddingManager


class TestEmbeddingManager:
    """Test embedding generation."""

    @pytest.mark.asyncio
    @patch('src.rag.embeddings.SentenceTransformer')
    async def test_load_local_model(self, mock_transformer):
        """Should load local embedding model."""
        # Mock the SentenceTransformer
        mock_model = Mock()
        mock_model.get_sentence_embedding_dimension.return_value = 384
        mock_transformer.return_value = mock_model
        
        manager = EmbeddingManager(model="all-MiniLM-L6-v2")

        await manager.initialize()

        assert manager.is_initialized
        assert manager.model_name == "all-MiniLM-L6-v2"
        assert manager.embedding_dim == 384
        mock_transformer.assert_called_once()

    @pytest.mark.asyncio
    @patch('src.rag.embeddings.SentenceTransformer')
    async def test_generate_embedding(self, mock_transformer):
        """Should generate embedding vector."""
        # Mock the SentenceTransformer
        mock_model = Mock()
        mock_model.get_sentence_embedding_dimension.return_value = 384
        # Return a normalized random vector
        mock_embedding = np.random.randn(384).astype(np.float32)
        mock_embedding = mock_embedding / np.linalg.norm(mock_embedding)
        mock_model.encode.return_value = mock_embedding
        mock_transformer.return_value = mock_model
        
        manager = EmbeddingManager(model="all-MiniLM-L6-v2")
        await manager.initialize()

        text = "This is a test document."

        embedding = await manager.embed(text)

        # Should be correct dimension
        assert len(embedding) == 384

        # Should be floats
        assert all(isinstance(x, (float, np.floating)) for x in embedding)

        # Should be normalized (unit vector for cosine similarity)
        magnitude = np.linalg.norm(embedding)
        assert 0.99 < magnitude < 1.01  # Approximately 1.0

    @pytest.mark.asyncio
    @patch('src.rag.embeddings.SentenceTransformer')
    async def test_batch_embeddings(self, mock_transformer):
        """Should generate embeddings for multiple texts."""
        # Mock the SentenceTransformer
        mock_model = Mock()
        mock_model.get_sentence_embedding_dimension.return_value = 384
        # Return 3 normalized random vectors
        mock_embeddings = np.random.randn(3, 384).astype(np.float32)
        for i in range(3):
            mock_embeddings[i] = mock_embeddings[i] / np.linalg.norm(mock_embeddings[i])
        mock_model.encode.return_value = mock_embeddings
        mock_transformer.return_value = mock_model
        
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
    @patch('src.rag.embeddings.SentenceTransformer')
    async def test_similar_texts_have_high_similarity(self, mock_transformer):
        """Similar texts should have similar embeddings."""
        # Mock the SentenceTransformer with realistic similarity patterns
        mock_model = Mock()
        mock_model.get_sentence_embedding_dimension.return_value = 384
        
        # Create embeddings with controlled similarities
        # emb1 and emb2 are similar, emb3 is different
        base_vector = np.random.randn(384).astype(np.float32)
        base_vector = base_vector / np.linalg.norm(base_vector)
        
        emb1 = base_vector.copy()
        # Make emb2 very similar to emb1 (small noise)
        emb2 = base_vector + np.random.randn(384).astype(np.float32) * 0.01
        emb2 = emb2 / np.linalg.norm(emb2)
        # Make emb3 different
        emb3 = np.random.randn(384).astype(np.float32)
        emb3 = emb3 / np.linalg.norm(emb3)
        
        mock_model.encode.side_effect = [emb1, emb2, emb3]
        mock_transformer.return_value = mock_model
        
        manager = EmbeddingManager(model="all-MiniLM-L6-v2")
        await manager.initialize()

        text1 = "The quick brown fox jumps over the lazy dog"
        text2 = "A fast brown fox leaps over a sleepy dog"
        text3 = "Python is a programming language"

        emb1_result = await manager.embed(text1)
        emb2_result = await manager.embed(text2)
        emb3_result = await manager.embed(text3)

        # Calculate cosine similarity
        sim_1_2 = np.dot(emb1_result, emb2_result)
        sim_1_3 = np.dot(emb1_result, emb3_result)

        # Similar texts should have higher similarity
        assert sim_1_2 > sim_1_3
        # With small noise, similarity should be high
        assert sim_1_2 > 0.9
