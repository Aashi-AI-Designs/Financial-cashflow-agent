"""
ingest/chunker.py

Splits documents into chunks before embedding.

Why chunking matters:
- LLMs have context limits — you can't embed an entire document as one unit
- Smaller chunks retrieve more precisely — a query about food cost gets the
  food cost section, not an entire restaurant guide
- Overlap between chunks ensures boundary sentences are captured fully

Chunking strategies implemented:
1. FixedSizeChunker   — simple, splits by character count with overlap
2. SentenceChunker    — splits on sentence boundaries, more natural
3. SectionChunker     — splits on headers/sections, best for structured docs

For this project we use SectionChunker as our documents have clear headers.
FixedSizeChunker is kept for reference and comparison.
"""

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class Chunk:
    """
    A single piece of text ready for embedding.

    Metadata travels with the chunk so that when the agent retrieves it,
    it knows exactly where it came from — which document, which section,
    which business type. This is how the agent cites its sources.
    """
    text: str                          # The actual text content
    source_file: str                   # Relative path of the source document
    business_type: str                 # 'general', 'restaurant', 'saas', etc.
    section: str = ""                  # Section heading if available
    chunk_index: int = 0               # Position within the document
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        self.text = self.text.strip()

    @property
    def is_empty(self) -> bool:
        return len(self.text.strip()) < 50  # Ignore tiny fragments


class FixedSizeChunker:
    """
    Splits text into fixed-size chunks with overlap.

    Simple and reliable. The overlap ensures that a concept split
    across a chunk boundary appears in both chunks, so retrieval
    doesn't miss it.

    Overlap example with chunk_size=100, overlap=20:
        Chunk 1: characters 0-100
        Chunk 2: characters 80-180   ← 20 chars overlap with chunk 1
        Chunk 3: characters 160-260  ← 20 chars overlap with chunk 2

    When to use: unstructured text without clear section boundaries.
    """

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        if chunk_overlap >= chunk_size:
            raise ValueError(
                f"chunk_overlap ({chunk_overlap}) must be less than chunk_size ({chunk_size})"
            )
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk(self, text: str, source_file: str, business_type: str) -> list[Chunk]:
        """Split text into fixed-size overlapping chunks."""
        chunks = []
        start = 0
        index = 0

        while start < len(text):
            end = start + self.chunk_size
            chunk_text = text[start:end]

            chunk = Chunk(
                text=chunk_text,
                source_file=source_file,
                business_type=business_type,
                chunk_index=index,
            )

            if not chunk.is_empty:
                chunks.append(chunk)

            # Move forward by (chunk_size - overlap) to create the overlap
            start += self.chunk_size - self.chunk_overlap
            index += 1

        logger.debug(
            "FixedSizeChunker: %d chunks from %s", len(chunks), source_file
        )
        return chunks


class SectionChunker:
    """
    Splits text on section headers (ALL CAPS lines or lines ending with newlines).

    This is the right chunker for our documents because they are structured
    with clear section titles. Each section becomes its own chunk (or is
    split further if it exceeds max_chunk_size).

    Why section-based chunking is better for our use case:
    - "What is burn rate?" retrieves the burn rate section, not a random
      character window that might include half of two different sections
    - Sections are semantically coherent — all content in a chunk is
      about the same topic
    - Source attribution is cleaner — the agent can say "according to
      the SaaS Metrics Guide, section on Churn Rate..."

    When to use: structured documents with clear headers.
    """

    def __init__(self, max_chunk_size: int = 2000, min_chunk_size: int = 100):
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size

    def _is_header(self, line: str) -> bool:
        """Detect section headers — ALL CAPS lines of reasonable length."""
        stripped = line.strip()
        if not stripped:
            return False
        # A header: mostly uppercase, not too short, not too long
        if len(stripped) < 5 or len(stripped) > 120:
            return False
        # At least 60% uppercase (allows for numbers and punctuation)
        alpha_chars = [c for c in stripped if c.isalpha()]
        if not alpha_chars:
            return False
        upper_ratio = sum(1 for c in alpha_chars if c.isupper()) / len(alpha_chars)
        return upper_ratio > 0.6

    def _split_large_section(
        self, text: str, source_file: str, business_type: str,
        section: str, start_index: int
    ) -> list[Chunk]:
        """
        If a section exceeds max_chunk_size, split it into paragraph-sized chunks.
        Preserves the section name in each sub-chunk's metadata.
        """
        chunks = []
        paragraphs = re.split(r'\n\n+', text)
        current_text = ""
        chunk_index = start_index

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            if len(current_text) + len(para) > self.max_chunk_size and current_text:
                chunk = Chunk(
                    text=current_text.strip(),
                    source_file=source_file,
                    business_type=business_type,
                    section=section,
                    chunk_index=chunk_index,
                )
                if not chunk.is_empty:
                    chunks.append(chunk)
                current_text = para
                chunk_index += 1
            else:
                current_text += "\n\n" + para if current_text else para

        # Don't forget the last piece
        if current_text.strip():
            chunk = Chunk(
                text=current_text.strip(),
                source_file=source_file,
                business_type=business_type,
                section=section,
                chunk_index=chunk_index,
            )
            if not chunk.is_empty:
                chunks.append(chunk)

        return chunks

    def chunk(self, text: str, source_file: str, business_type: str) -> list[Chunk]:
        """Split text into section-based chunks."""
        lines = text.split('\n')
        chunks = []
        current_section = "Introduction"
        current_lines = []
        chunk_index = 0

        for line in lines:
            if self._is_header(line):
                # Save the accumulated section before starting the new one
                if current_lines:
                    section_text = '\n'.join(current_lines).strip()
                    if len(section_text) >= self.min_chunk_size:
                        if len(section_text) > self.max_chunk_size:
                            # Section too large — split into paragraphs
                            sub_chunks = self._split_large_section(
                                section_text, source_file, business_type,
                                current_section, chunk_index
                            )
                            chunks.extend(sub_chunks)
                            chunk_index += len(sub_chunks)
                        else:
                            chunk = Chunk(
                                text=section_text,
                                source_file=source_file,
                                business_type=business_type,
                                section=current_section,
                                chunk_index=chunk_index,
                            )
                            if not chunk.is_empty:
                                chunks.append(chunk)
                                chunk_index += 1

                # Start the new section
                current_section = line.strip()
                current_lines = []
            else:
                current_lines.append(line)

        # Handle the final section
        if current_lines:
            section_text = '\n'.join(current_lines).strip()
            if len(section_text) >= self.min_chunk_size:
                chunk = Chunk(
                    text=section_text,
                    source_file=source_file,
                    business_type=business_type,
                    section=current_section,
                    chunk_index=chunk_index,
                )
                if not chunk.is_empty:
                    chunks.append(chunk)

        logger.debug(
            "SectionChunker: %d chunks from %s", len(chunks), source_file
        )
        return chunks


def chunk_file(
    file_path: Path,
    pdf_base_dir: Path,
    chunker: SectionChunker | FixedSizeChunker | None = None
) -> list[Chunk]:
    """
    Chunk a single file.

    Automatically determines the business_type from the folder structure:
        data/pdfs/restaurant/food_cost_management.txt → business_type = 'restaurant'
        data/pdfs/general/cash_flow_fundamentals.txt  → business_type = 'general'

    Args:
        file_path: Absolute path to the text file
        pdf_base_dir: The data/pdfs/ directory (used to compute relative path)
        chunker: Chunker instance to use (defaults to SectionChunker)
    """
    if chunker is None:
        chunker = SectionChunker()

    text = file_path.read_text(encoding="utf-8")

    # Derive business_type from folder name
    relative = file_path.relative_to(pdf_base_dir)
    parts = relative.parts
    business_type = parts[0] if len(parts) > 1 else "general"
    source_file = str(relative)

    return chunker.chunk(text, source_file, business_type)
