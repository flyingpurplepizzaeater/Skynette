# src/rag/processor.py
"""
Document Processor

Handles file parsing and chunking for RAG indexing.
Sprint 1: Markdown and text files only.
"""

import re
from pathlib import Path
from typing import List
from src.rag.models import Chunk


class DocumentProcessor:
    """Process documents and create chunks."""

    def __init__(
        self,
        chunk_size: int = 1024,
        chunk_overlap: int = 128,
        max_chunk_size: int = 2048
    ):
        """Initialize processor with chunking parameters."""
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.max_chunk_size = max_chunk_size

    def process_file(self, file_path: str, file_type: str) -> List[Chunk]:
        """Process file and return chunks."""
        content = Path(file_path).read_text(encoding='utf-8')

        if file_type == "markdown":
            return self.chunk_markdown(content)
        elif file_type == "text":
            return self.chunk_text(content)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

    def chunk_markdown(self, content: str) -> List[Chunk]:
        """
        Chunk markdown by sections (headers).

        Strategy: Split on headers (## ) while preserving hierarchy.
        Creates a chunk per section, combining small sections if under chunk_size.
        """
        chunks = []

        # Split by headers - captures headers and content
        parts = re.split(r'(^#{1,6}\s+.+$)', content, flags=re.MULTILINE)

        current_section = []
        chunk_index = 0

        for i, part in enumerate(parts):
            if not part.strip():
                continue

            # Check if this is a header line
            if re.match(r'^#{1,6}\s+.+$', part):
                # Save previous section if it exists
                if current_section:
                    section_text = '\n'.join(current_section).strip()
                    if section_text:
                        chunk = Chunk(
                            document_id="",
                            chunk_index=chunk_index,
                            content=section_text,
                            metadata={"type": "section"}
                        )
                        chunks.append(chunk)
                        chunk_index += 1

                # Start new section with this header
                current_section = [part]
            else:
                # Add content to current section
                current_section.append(part)

                # Check if current section is getting too large
                section_text = '\n'.join(current_section)
                token_count = self.count_tokens(section_text)

                if token_count >= self.chunk_size:
                    # Create chunk and reset
                    chunk = Chunk(
                        document_id="",
                        chunk_index=chunk_index,
                        content=section_text.strip(),
                        metadata={"type": "section"}
                    )
                    chunks.append(chunk)
                    chunk_index += 1
                    current_section = []

        # Add remaining content
        if current_section:
            section_text = '\n'.join(current_section).strip()
            if section_text:
                chunk = Chunk(
                    document_id="",
                    chunk_index=chunk_index,
                    content=section_text,
                    metadata={"type": "section"}
                )
                chunks.append(chunk)

        # If no chunks created (no headers), create one chunk
        if not chunks and content.strip():
            chunk = Chunk(
                document_id="",
                chunk_index=0,
                content=content.strip(),
                metadata={"type": "document"}
            )
            chunks.append(chunk)

        return chunks

    def chunk_text(self, content: str) -> List[Chunk]:
        """
        Chunk plain text by token count with overlap.

        Strategy: Split on sentences/paragraphs, group by token count.
        If no sentences found, split by words.
        """
        # Try to split into sentences (simple regex)
        sentences = re.split(r'(?<=[.!?])\s+', content)

        # If no sentence delimiters found, split by words instead
        if len(sentences) == 1 and len(content.split()) > 50:
            words = content.split()
            sentences = []
            # Group words into pseudo-sentences of ~20 words
            for i in range(0, len(words), 20):
                sentences.append(' '.join(words[i:i+20]))

        chunks = []
        current_chunk = []
        current_tokens = 0
        chunk_index = 0

        for sentence in sentences:
            sentence_tokens = self.count_tokens(sentence)

            # Check if adding this sentence exceeds chunk size
            if current_tokens + sentence_tokens > self.chunk_size and current_chunk:
                # Create chunk
                chunk_text = ' '.join(current_chunk)
                chunk = Chunk(
                    document_id="",
                    chunk_index=chunk_index,
                    content=chunk_text,
                    metadata={"type": "text"}
                )
                chunks.append(chunk)
                chunk_index += 1

                # Start new chunk with overlap - use word-level overlap
                chunk_words = chunk_text.split()
                overlap_word_count = int(self.chunk_overlap / 1.3)  # Convert tokens to words
                overlap_words = chunk_words[-overlap_word_count:] if len(chunk_words) > overlap_word_count else chunk_words

                # Rebuild current_chunk with overlapping words
                overlap_text = ' '.join(overlap_words)
                # Re-split overlap into sentences for consistency
                overlap_sentences = re.split(r'(?<=[.!?])\s+', overlap_text)
                if len(overlap_sentences) == 1 and len(overlap_text.split()) > 20:
                    # Recreate pseudo-sentences
                    overlap_words_list = overlap_text.split()
                    overlap_sentences = []
                    for i in range(0, len(overlap_words_list), 20):
                        overlap_sentences.append(' '.join(overlap_words_list[i:i+20]))

                current_chunk = overlap_sentences
                current_tokens = self.count_tokens(overlap_text)

            current_chunk.append(sentence)
            current_tokens += sentence_tokens

            # Enforce max chunk size
            if current_tokens >= self.max_chunk_size:
                chunk_text = ' '.join(current_chunk)
                chunk = Chunk(
                    document_id="",
                    chunk_index=chunk_index,
                    content=chunk_text,
                    metadata={"type": "text"}
                )
                chunks.append(chunk)
                chunk_index += 1

                current_chunk = []
                current_tokens = 0

        # Add remaining content
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunk = Chunk(
                document_id="",
                chunk_index=chunk_index,
                content=chunk_text,
                metadata={"type": "text"}
            )
            chunks.append(chunk)

        return chunks

    def count_tokens(self, text: str) -> int:
        """
        Estimate token count.

        Sprint 1: Simple word-based estimation.
        Future: Use tiktoken for accurate counts.
        """
        # Simple estimation: ~1.3 tokens per word
        words = len(text.split())
        return int(words * 1.3)
