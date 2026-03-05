"""
ingest/ingest_docs.py

Orchestrates the full RAG ingestion pipeline:
    1. Find all .txt documents in data/pdfs/
    2. Chunk each document using SectionChunker
    3. Embed all chunks using OpenAI's embedding API
    4. Build a FAISS index from the vectors
    5. Save the index and chunk metadata to disk

This is a one-time (or occasional) operation. You run it:
    - Once when setting up the project
    - Again when you add new documents to data/pdfs/
    - It does NOT need to run every time the agent starts

Run directly:
    python ingest/ingest_docs.py

The pipeline prints a summary when complete showing how many chunks
were created per document and per business type.
"""

import logging
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import settings
from config.logging_config import setup_logging
from ingest.create_docs import create_documents
from ingest.chunker import SectionChunker, chunk_file, Chunk
from ingest.embedder import embed_batch
from ingest.vector_store import VectorStore

logger = logging.getLogger(__name__)


def run_ingestion(recreate_docs: bool = True) -> None:
    """
    Run the full ingestion pipeline.

    Args:
        recreate_docs: If True, regenerate the source documents before ingesting.
                       Set to False if you've manually added custom documents.
    """
    setup_logging(log_level=settings.LOG_LEVEL)
    settings.validate()

    start_time = time.time()
    logger.info("Starting RAG ingestion pipeline...")

    # -------------------------------------------------------------------------
    # Step 1: Create documents
    # -------------------------------------------------------------------------
    if recreate_docs:
        logger.info("Step 1/4: Creating source documents...")
        create_documents()
    else:
        logger.info("Step 1/4: Skipping document creation (recreate_docs=False)")

    # -------------------------------------------------------------------------
    # Step 2: Chunk all documents
    # -------------------------------------------------------------------------
    logger.info("Step 2/4: Chunking documents...")

    pdf_dir = settings.PDF_DIR
    txt_files = sorted(pdf_dir.rglob("*.txt"))

    if not txt_files:
        raise FileNotFoundError(
            f"No .txt files found in {pdf_dir}. Run create_docs.py first."
        )

    chunker = SectionChunker(max_chunk_size=2000, min_chunk_size=100)
    all_chunks: list[Chunk] = []

    for file_path in txt_files:
        chunks = chunk_file(file_path, pdf_dir, chunker)
        all_chunks.extend(chunks)
        logger.info(
            "  %-55s → %d chunks",
            str(file_path.relative_to(pdf_dir)), len(chunks)
        )

    logger.info("Total chunks created: %d", len(all_chunks))

    # Show distribution by business type
    by_type = {}
    for chunk in all_chunks:
        by_type[chunk.business_type] = by_type.get(chunk.business_type, 0) + 1
    for bt, count in sorted(by_type.items()):
        logger.info("  %-20s %d chunks", bt, count)

    # -------------------------------------------------------------------------
    # Step 3: Embed all chunks
    # -------------------------------------------------------------------------
    logger.info("Step 3/4: Embedding %d chunks via OpenAI API...", len(all_chunks))
    logger.info("  Model: %s", settings.OPENAI_EMBEDDING_MODEL)
    logger.info(
        "  Estimated API cost: ~$%.4f",
        # text-embedding-3-small costs $0.02 per 1M tokens
        # Average chunk ~300 tokens → total tokens ≈ chunks * 300
        len(all_chunks) * 300 / 1_000_000 * 0.02
    )

    texts = [chunk.text for chunk in all_chunks]
    vectors = embed_batch(texts, batch_size=100)

    # -------------------------------------------------------------------------
    # Step 4: Build and save the FAISS index
    # -------------------------------------------------------------------------
    logger.info("Step 4/4: Building FAISS index and saving to disk...")

    store = VectorStore()
    store.build(all_chunks, vectors)
    store.save()

    # -------------------------------------------------------------------------
    # Summary
    # -------------------------------------------------------------------------
    elapsed = time.time() - start_time
    stats = store.stats()

    print("\n=== RAG Ingestion Complete ===")
    print(f"  Total chunks       : {stats['total_chunks']}")
    print(f"  Vector dimensions  : {stats['dimension']}")
    print(f"  Business types     : {', '.join(stats['business_types'])}")
    print(f"  Time elapsed       : {elapsed:.1f}s")
    print(f"  Index saved to     : {settings.VECTOR_STORE_ABSOLUTE_PATH}")
    print("=" * 32)
    print("\n✅ Module 3 complete — RAG pipeline is ready.\n")


if __name__ == "__main__":
    run_ingestion(recreate_docs=True)
