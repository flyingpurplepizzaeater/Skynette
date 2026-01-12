import pytest
from datetime import datetime, timezone
from src.ui.models.knowledge_bases import CollectionCardData, UploadProgress, UploadError, QueryResultUI


class TestCollectionCardData:
    def test_create_collection_card_data(self):
        """CollectionCardData should store all collection info."""
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

        assert data.id == "coll-123"
        assert data.name == "ProjectDocs"
        assert data.document_count == 45
        assert data.chunk_count == 234
        assert data.embedding_model == "local"


class TestUploadProgress:
    def test_percentage_calculation(self):
        """percentage should calculate correctly."""
        progress = UploadProgress(
            total_files=10,
            processed_files=5,
            current_file="test.md",
            status="processing",
            errors=[],
        )

        assert progress.percentage == 50.0

    def test_percentage_zero_files(self):
        """percentage should handle zero files."""
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
        """UploadError should store error details."""
        error = UploadError(
            file_path="/path/to/file.pdf",
            error_message="PDF support coming in Sprint 2",
            error_type="unsupported",
        )

        assert error.file_path == "/path/to/file.pdf"
        assert error.error_type == "unsupported"
        assert "Sprint 2" in error.error_message


class TestQueryResultUI:
    def test_from_backend_result(self):
        """from_backend_result should convert backend format."""
        backend_result = {
            "content": "Test chunk content",
            "similarity": 0.92,
            "metadata": {
                "source_path": "docs/test.md",
                "chunk_index": 0,
            }
        }

        result = QueryResultUI.from_backend_result(backend_result)

        assert result.chunk_content == "Test chunk content"
        assert result.source_file == "docs/test.md"
        assert result.similarity == 0.92
        assert result.metadata["chunk_index"] == 0

    def test_from_backend_result_with_defaults(self):
        """from_backend_result should handle missing fields gracefully."""
        backend_result = {
            "content": "Test content",
            # Missing similarity and metadata
        }

        result = QueryResultUI.from_backend_result(backend_result)

        assert result.chunk_content == "Test content"
        assert result.source_file == "unknown"
        assert result.similarity == 0.0
        assert result.metadata == {}
