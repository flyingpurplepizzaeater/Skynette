"""
Quick installation and functionality test script.

Run this to verify core components work before GUI testing.
"""

import sys
from pathlib import Path

def test_imports():
    """Test that all critical modules can be imported."""
    print("Testing module imports...")

    tests = [
        ("Main entry point", "src.main"),
        ("UI App", "src.ui.app"),
        ("AI Hub", "src.ui.views.ai_hub"),
        ("Knowledge Bases", "src.ui.views.knowledge_bases"),
        ("Usage Dashboard", "src.ui.views.usage_dashboard"),
        ("RAG Service", "src.rag.service"),
        ("ChromaDB Client", "src.rag.chromadb_client"),
        ("Embeddings", "src.rag.embeddings"),
        ("Document Processor", "src.rag.processor"),
        ("RAG Storage", "src.rag.storage"),
        ("AI Gateway", "src.ai.gateway"),
        ("AI Security", "src.ai.security"),
        ("Workflow Models", "src.core.workflow.models"),
    ]

    failed = []
    for name, module in tests:
        try:
            __import__(module)
            print(f"  [OK] {name}")
        except Exception as e:
            print(f"  [FAIL] {name}: {e}")
            failed.append((name, module, str(e)))

    return len(failed) == 0, failed


def test_rag_components():
    """Test RAG components work correctly."""
    print("\nTesting RAG components...")

    try:
        from src.rag.embeddings import EmbeddingManager
        from src.rag.processor import DocumentProcessor
        from src.rag.models import Document, Chunk
        from datetime import datetime, timezone

        # Test embedding manager initialization
        print("  [OK] EmbeddingManager can be imported")

        # Test document processor
        processor = DocumentProcessor()
        print("  [OK] DocumentProcessor initialized")

        # Test document model
        doc = Document(
            id="test-123",
            collection_id="test-collection",
            source_path="test.md",
            file_type="markdown",
            file_hash="abc123def456",
            status="queued",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        print("  [OK] Document model created")

        # Test chunk model
        chunk = Chunk(
            id="chunk-123",
            document_id="test-123",
            collection_id="test-collection",
            chunk_index=0,
            content="Test content",
            embedding=[0.1] * 384,  # all-MiniLM-L6-v2 dimension
        )
        print("  [OK] Chunk model created")

        return True, None

    except Exception as e:
        return False, str(e)


def test_ui_models():
    """Test UI data models."""
    print("\nTesting UI models...")

    try:
        from src.ui.models.knowledge_bases import (
            CollectionCardData,
            UploadProgress,
            QueryResultUI,
            UploadError
        )
        from datetime import datetime, timezone

        # Test CollectionCardData
        card = CollectionCardData(
            id="test-123",
            name="Test Collection",
            description="Test description",
            document_count=0,
            chunk_count=0,
            last_updated=datetime.now(timezone.utc),
            storage_size_bytes=0,
            embedding_model="all-MiniLM-L6-v2",
        )
        print("  [OK] CollectionCardData created")

        # Test UploadProgress
        progress = UploadProgress(
            total_files=10,
            processed_files=5,
            current_file="test.md",
            status="processing",
            errors=[],
        )
        assert progress.percentage == 50.0
        print("  [OK] UploadProgress created (50% calculation works)")

        # Test QueryResultUI
        result = QueryResultUI.from_backend_result({
            "content": "Test content",
            "similarity": 0.85,
            "metadata": {"source_path": "test.md"}
        })
        assert result.chunk_content == "Test content"
        assert result.similarity == 0.85
        assert result.source_file == "test.md"
        print("  [OK] QueryResultUI created from backend result")

        # Test error handling with missing fields
        result2 = QueryResultUI.from_backend_result({})
        assert result2.chunk_content == ""
        assert result2.similarity == 0.0
        assert result2.source_file == "unknown"
        print("  [OK] QueryResultUI handles missing fields safely")

        return True, None

    except Exception as e:
        return False, str(e)


def test_database_schema():
    """Test that database schemas are valid."""
    print("\nTesting database schemas...")

    try:
        from src.rag.storage import RAGStorage
        import tempfile
        import os
        import time

        # Create temporary database
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as f:
            db_path = f.name

        try:
            # Initialize storage (creates schema)
            storage = RAGStorage(db_path)
            print("  [OK] RAG database schema created")

            # Test basic operations would go here
            # (skipping to avoid creating actual data)

            # Close connection explicitly
            del storage
            time.sleep(0.1)  # Give Windows time to release file handle

        finally:
            # Cleanup
            try:
                if os.path.exists(db_path):
                    os.unlink(db_path)
            except PermissionError:
                # Windows may still have file locked - that's okay for test
                pass

        return True, None

    except Exception as e:
        return False, str(e)


def main():
    """Run all tests."""
    print("="*60)
    print("Skynette Installation Test")
    print("="*60)

    all_passed = True

    # Test 1: Imports
    passed, failed = test_imports()
    if not passed:
        all_passed = False
        print(f"\n[WARN]  {len(failed)} import(s) failed:")
        for name, module, error in failed:
            print(f"  - {name} ({module}): {error}")

    # Test 2: RAG Components
    passed, error = test_rag_components()
    if not passed:
        all_passed = False
        print(f"\n[WARN]  RAG components test failed: {error}")

    # Test 3: UI Models
    passed, error = test_ui_models()
    if not passed:
        all_passed = False
        print(f"\n[WARN]  UI models test failed: {error}")

    # Test 4: Database Schema
    passed, error = test_database_schema()
    if not passed:
        all_passed = False
        print(f"\n[WARN]  Database schema test failed: {error}")

    # Summary
    print("\n" + "="*60)
    if all_passed:
        print("[PASS] ALL TESTS PASSED!")
        print("\nBackend components are working correctly.")
        print("Next step: Test the GUI application using TESTING_GUIDE.md")
        return 0
    else:
        print("[FAIL] SOME TESTS FAILED")
        print("\nFix the issues above before testing the GUI.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
