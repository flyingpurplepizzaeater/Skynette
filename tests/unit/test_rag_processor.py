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
