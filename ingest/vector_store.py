"""
ingest/vector_store.py

Builds and queries a FAISS vector store from embedded document chunks.

What FAISS actually does:
    FAISS (Facebook AI Similarity Search) is a library for finding the
    nearest vectors in a large collection of vectors efficiently.

    Naive similarity search: compare the query vector to EVERY stored vector
    and find the closest ones. This is O(n) — slow with thousands of chunks.

    FAISS uses index structures (like Flat, IVF, HNSW) to make this faster.
    For our scale (hundreds to low thousands of chunks) we use IndexFlatL2
    which does exact nearest-neighbour search — no approximation needed.

How similarity is measured:
    We use L2 (Euclidean) distance — the straight-line distance between two
    points in vector space. Smaller distance = more similar meaning.
    An alternative is cosine similarity (angle between vectors) but L2 on
    normalised vectors gives equivalent results.

What gets stored:
    FAISS only stores vectors — it has no concept of the text they represent.
    We store the chunk metadata (text, source, business_type, section) in a
    parallel Python list that we save alongside the FAISS index.
    When FAISS returns index positions [3, 7, 12], we look up positions
    3, 7, 12 in our metadata list to get the actual chunk text.
"""

import json
import logging
import pickle
from pathlib import Path
from typing import Optional

import faiss
import numpy as np

from ingest.chunker import Chunk
from config.settings import settings

logger = logging.getLogger(__name__)

# File names within the vector store directory
INDEX_FILE = "index.faiss"
CHUNKS_FILE = "chunks.pkl"
META_FILE = "meta.json"


class VectorStore:
    """
    A FAISS-backed vector store with chunk metadata.

    Two modes:
    1. Build mode: add chunks + vectors, then save to disk
    2. Query mode: load from disk, search by query vector
    """

    def __init__(self, store_path: Optional[Path] = None):
        self.store_path = store_path or settings.VECTOR_STORE_ABSOLUTE_PATH
        self.store_path.mkdir(parents=True, exist_ok=True)

        self.index: Optional[faiss.IndexFlatL2] = None
        self.chunks: list[Chunk] = []  # Parallel list to the FAISS index
        self.dimension: int = 384      # all-MiniLM-L6-v2 dimension

    # -------------------------------------------------------------------------
    # Building the index
    # -------------------------------------------------------------------------

    def build(self, chunks: list[Chunk], vectors: list[list[float]]) -> None:
        """
        Build the FAISS index from chunks and their embedding vectors.

        Args:
            chunks: List of Chunk objects (text + metadata)
            vectors: Corresponding embedding vectors (same length as chunks)
        """
        if len(chunks) != len(vectors):
            raise ValueError(
                f"chunks ({len(chunks)}) and vectors ({len(vectors)}) must have the same length"
            )
        if not chunks:
            raise ValueError("Cannot build an empty vector store")

        self.dimension = len(vectors[0])
        self.chunks = chunks

        # Convert to numpy float32 — FAISS requires this format
        vectors_np = np.array(vectors, dtype=np.float32)

        # IndexFlatL2: exact nearest-neighbour search using L2 distance
        # For our scale this is fast enough and gives perfect accuracy
        self.index = faiss.IndexFlatL2(self.dimension)
        self.index.add(vectors_np)

        logger.info(
            "Built FAISS index: %d vectors, %d dimensions",
            self.index.ntotal, self.dimension
        )

    # -------------------------------------------------------------------------
    # Saving and loading
    # -------------------------------------------------------------------------

    def save(self) -> None:
        """
        Persist the index and chunk metadata to disk.

        Three files are written:
        - index.faiss: the FAISS index (binary format)
        - chunks.pkl:  the list of Chunk objects (Python pickle)
        - meta.json:   human-readable summary for debugging
        """
        if self.index is None:
            raise RuntimeError("No index to save. Call build() first.")

        # Save FAISS index
        index_path = self.store_path / INDEX_FILE
        faiss.write_index(self.index, str(index_path))
        logger.info("Saved FAISS index to %s", index_path)

        # Save chunk metadata
        chunks_path = self.store_path / CHUNKS_FILE
        with open(chunks_path, "wb") as f:
            pickle.dump(self.chunks, f)
        logger.info("Saved %d chunk metadata records to %s", len(self.chunks), chunks_path)

        # Save human-readable summary
        meta = {
            "total_chunks": len(self.chunks),
            "dimension": self.dimension,
            "business_types": sorted(set(c.business_type for c in self.chunks)),
            "source_files": sorted(set(c.source_file for c in self.chunks)),
            "chunks_per_business_type": {
                bt: sum(1 for c in self.chunks if c.business_type == bt)
                for bt in set(c.business_type for c in self.chunks)
            },
        }
        meta_path = self.store_path / META_FILE
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)
        logger.info("Saved vector store metadata to %s", meta_path)

    def load(self) -> None:
        """
        Load a previously saved index from disk.
        Call this before querying.
        """
        index_path = self.store_path / INDEX_FILE
        chunks_path = self.store_path / CHUNKS_FILE

        if not index_path.exists() or not chunks_path.exists():
            raise FileNotFoundError(
                f"Vector store not found at {self.store_path}. "
                "Run: python ingest/ingest_docs.py"
            )

        self.index = faiss.read_index(str(index_path))
        with open(chunks_path, "rb") as f:
            self.chunks = pickle.load(f)

        self.dimension = self.index.d

        logger.info(
            "Loaded FAISS index: %d vectors, %d dimensions from %s",
            self.index.ntotal, self.dimension, self.store_path
        )

    # -------------------------------------------------------------------------
    # Querying
    # -------------------------------------------------------------------------

    def search(
        self,
        query_vector: list[float],
        top_k: int = 5,
        business_type_filter: Optional[str] = None,
    ) -> list[dict]:
        """
        Find the top_k most semantically similar chunks to a query vector.

        How this works:
        1. Convert query to numpy float32
        2. Ask FAISS for the top_k nearest vectors (by L2 distance)
        3. FAISS returns (distances, indices) — indices point to self.chunks
        4. Look up the actual chunk text and metadata using those indices
        5. Optionally filter by business_type

        Args:
            query_vector: Embedding of the search query
            top_k: Number of results to return
            business_type_filter: If set, only return chunks of this type
                                  (e.g. 'restaurant', 'saas', 'general')

        Returns:
            List of dicts with chunk text, metadata, and similarity score
        """
        if self.index is None:
            raise RuntimeError("Index not loaded. Call load() first.")

        # If filtering by business type, we need to retrieve more results
        # upfront and then filter down to get top_k valid results
        fetch_k = top_k * 4 if business_type_filter else top_k

        query_np = np.array([query_vector], dtype=np.float32)
        distances, indices = self.index.search(query_np, fetch_k)

        results = []
        for distance, idx in zip(distances[0], indices[0]):
            if idx == -1:  # FAISS returns -1 for empty slots
                continue

            chunk = self.chunks[idx]

            # Apply business type filter
            if business_type_filter and business_type_filter != "general":
                # Always include 'general' documents — they apply to all businesses
                if chunk.business_type not in (business_type_filter, "general"):
                    continue

            # Convert L2 distance to a 0-1 similarity score
            # Lower distance = higher similarity
            # We use a simple transformation: similarity = 1 / (1 + distance)
            similarity = float(1 / (1 + distance))

            results.append({
                "text": chunk.text,
                "source_file": chunk.source_file,
                "business_type": chunk.business_type,
                "section": chunk.section,
                "chunk_index": chunk.chunk_index,
                "similarity": round(similarity, 4),
                "l2_distance": round(float(distance), 4),
            })

            if len(results) >= top_k:
                break

        logger.debug(
            "Search returned %d results (filter: %s)",
            len(results), business_type_filter or "none"
        )
        return results

    def is_loaded(self) -> bool:
        return self.index is not None and len(self.chunks) > 0

    def stats(self) -> dict:
        """Return a summary of the current index state."""
        if not self.is_loaded():
            return {"loaded": False}
        return {
            "loaded": True,
            "total_chunks": len(self.chunks),
            "dimension": self.dimension,
            "business_types": sorted(set(c.business_type for c in self.chunks)),
        }


# Shared singleton — loaded once and reused across all tool calls
_store: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    """
    Return the shared VectorStore instance, loading it if needed.
    This is the function other modules should import and use.

    Usage:
        from ingest.vector_store import get_vector_store
        store = get_vector_store()
        results = store.search(query_vector, top_k=5)
    """
    global _store
    if _store is None or not _store.is_loaded():
        _store = VectorStore()
        _store.load()
    return _store
