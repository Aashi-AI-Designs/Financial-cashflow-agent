"""
ingest/embedder.py

Converts text into embedding vectors using a FREE local model.
No API key needed. No cost. Runs entirely on your CPU.

Model: all-MiniLM-L6-v2
- Downloads once (~90MB) and is cached locally forever after
- Produces 384-dimensional vectors (vs 1536 for OpenAI)
- Fast on CPU — good enough for learning and development
- Completely free and private
"""

import logging
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

# Model downloads automatically on first use (~90MB, one time only)
MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384  # This model produces 384-dimensional vectors

_model = None


def get_model() -> SentenceTransformer:
    """Lazy load the model — only downloaded once, cached forever after."""
    global _model
    if _model is None:
        logger.info("Loading local embedding model: %s", MODEL_NAME)
        _model = SentenceTransformer(MODEL_NAME)
        logger.info("Model loaded successfully")
    return _model


def embed_text(text: str) -> list[float]:
    """Embed a single string of text."""
    if not text or not text.strip():
        raise ValueError("Cannot embed empty text")
    model = get_model()
    vector = model.encode(text.strip()).tolist()
    logger.debug("Embedded text (%d chars) → vector of %d dims", len(text), len(vector))
    return vector


def embed_batch(
    texts: list[str],
    batch_size: int = 32,
    delay_between_batches: float = 0,
) -> list[list[float]]:
    """
    Embed a list of texts using the local model.
    batch_size and delay_between_batches kept for API compatibility
    but delay is unused since there are no rate limits locally.
    """
    if not texts:
        return []

    model = get_model()
    logger.info("Embedding %d texts locally (no API cost)...", len(texts))

    vectors = model.encode(texts, batch_size=batch_size, show_progress_bar=True)
    result = vectors.tolist()

    logger.info(
        "Embedding complete: %d texts → %d vectors (dim=%d)",
        len(texts), len(result), len(result[0]) if result else 0
    )
    return result
