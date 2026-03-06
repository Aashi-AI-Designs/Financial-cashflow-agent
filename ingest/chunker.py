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
2. SectionChunker     — splits on paragraph boundaries with header detection

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
    text: str
    source_file: str
    business_type: str
    section: str = ""
    chunk_index: int = 0
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        self.text = self.text.strip()

    @property
    def is_empty(self) -> bool:
        return len(self.text.strip()) < 50


class FixedSizeChunker:
    """
    Splits text into fixed-size chunks with overlap.
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
            start += self.chunk_size - self.chunk_overlap
            index += 1

        logger.debug("FixedSizeChunker: %d chunks from %s", len(chunks), source_file)
        return chunks


class SectionChunker:
    """
    Splits text on paragraph boundaries, grouping paragraphs under
    detected section headers.

    Works by splitting on double newlines (paragraphs), then checking
    if each paragraph is a header or content. Headers are short lines
    that don't end in sentence-ending punctuation.

    When to use: structured documents with clear section headers.
    """

    def __init__(self, max_chunk_size: int = 2000, min_chunk_size: int = 100):
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size

    def _is_header(self, line: str) -> bool:
        """Detect section headers."""
        stripped = line.strip()
        if not stripped or len(stripped) < 5 or len(stripped) > 120:
            return False
        # Too many words to be a header
        words = stripped.split()
        if len(words) > 12:
            return False
        # Sentence-ending punctuation means it's content, not a header
        if stripped[-1] in '.,;:':
            return False
        alpha_chars = [c for c in stripped if c.isalpha()]
        if not alpha_chars:
            return False
        # ALL CAPS header
        upper_ratio = sum(1 for c in alpha_chars if c.isupper()) / len(alpha_chars)
        if upper_ratio > 0.6:
            return True
        # Title Case header — majority of words start with uppercase
        if words[0][0].isupper() and sum(1 for w in words if w[0].isupper()) >= len(words) * 0.6:
            return True
        return False

    def _split_large_section(
        self, text: str, source_file: str, business_type: str,
        section: str, start_index: int
    ) -> list[Chunk]:
        """Split an oversized section into paragraph-sized sub-chunks."""
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
        """Split text into paragraph-based chunks grouped under section headers."""
        paragraphs = re.split(r'\n\n+', text)
        chunks = []
        current_section = "Introduction"
        current_text = ""
        chunk_index = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            lines = para.splitlines()
            # A header paragraph: short, 1-2 lines, all lines look like headers
            is_header_para = (
                len(lines) <= 2
                and all(self._is_header(l) for l in lines if l.strip())
            )

            if is_header_para:
                # Save accumulated content as a chunk before starting new section
                if current_text.strip() and len(current_text.strip()) >= self.min_chunk_size:
                    if len(current_text) > self.max_chunk_size:
                        sub_chunks = self._split_large_section(
                            current_text, source_file, business_type,
                            current_section, chunk_index
                        )
                        chunks.extend(sub_chunks)
                        chunk_index += len(sub_chunks)
                    else:
                        chunk = Chunk(
                            text=current_text.strip(),
                            source_file=source_file,
                            business_type=business_type,
                            section=current_section,
                            chunk_index=chunk_index,
                        )
                        if not chunk.is_empty:
                            chunks.append(chunk)
                            chunk_index += 1
                current_section = para.strip()
                current_text = ""
            else:
                current_text += "\n\n" + para if current_text else para

        # Final chunk
        if current_text.strip() and len(current_text.strip()) >= self.min_chunk_size:
            chunk = Chunk(
                text=current_text.strip(),
                source_file=source_file,
                business_type=business_type,
                section=current_section,
                chunk_index=chunk_index,
            )
            if not chunk.is_empty:
                chunks.append(chunk)

        logger.debug("SectionChunker: %d chunks from %s", len(chunks), source_file)
        return chunks


def chunk_file(
    file_path: Path,
    pdf_base_dir: Path,
    chunker=None
) -> list[Chunk]:
    """
    Chunk a single file.
    Automatically determines business_type from folder structure.
    """
    if chunker is None:
        chunker = SectionChunker()

    text = file_path.read_text(encoding="utf-8")
    relative = file_path.relative_to(pdf_base_dir)
    parts = relative.parts
    business_type = parts[0] if len(parts) > 1 else "general"
    source_file = str(relative)

    return chunker.chunk(text, source_file, business_type)
