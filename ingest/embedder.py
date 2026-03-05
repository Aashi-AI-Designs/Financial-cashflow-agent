"""
ingest/embedder.py

Converts text into embedding vectors using the OpenAI API.

What an embedding actually is:
    You send a string of text to OpenAI's embedding model.
    It returns a list of 1,536 floating point numbers.
    That list is a coordinate in 1,536-dimensional space.
    Text with similar MEANING ends up at similar coordinates —
    even if the words are completely different.

    "business is running out of money"
    "company has 2 months of runway left"
    → These two sentences will have vectors very close to each other

This is why semantic search works: embed the query, find the chunks
whose vectors are nearest to the query vector.

Why text-embedding-3-small?
    - 1,536 dimensions — enough for high-quality semantic search
    - Significantly cheaper than text-embedding-3-large
    - Faster response times
    - More than sufficient for document retrieval tasks
"""

import logging
import time
from typing import List

import openai

from config.settings import settings

logger = logging.getLogger(__name__)

# Initialise the OpenAI client once — reused for all embedding calls
_client = None


def get_client() -> openai.OpenAI:
    """Lazy initialisation of the OpenAI client."""
    global _client
    if _client is None:
        _client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
    return _client


def embed_text(text: str) -> list[float]:
    """
    Embed a single string of text.

    Returns a list of 1,536 floats representing the text in vector space.

    Args:
        text: The text to embed. Should be under 8,191 tokens (~6,000 words).

    Returns:
        A list of 1,536 floats.
    """
    if not text or not text.strip():
        raise ValueError("Cannot embed empty text")

    client = get_client()

    response = client.embeddings.create(
        model=settings.OPENAI_EMBEDDING_MODEL,
        input=text.strip(),
    )

    vector = response.data[0].embedding
    logger.debug("Embedded text (%d chars) → vector of %d dims", len(text), len(vector))
    return vector


def embed_batch(
    texts: list[str],
    batch_size: int = 100,
    delay_between_batches: float = 0.5,
) -> list[list[float]]:
    """
    Embed a list of texts efficiently using batching.

    Why batching?
    The OpenAI API accepts up to 2,048 texts in a single request.
    Sending texts one-by-one would be slow and waste API calls.
    Batching sends multiple texts per request, reducing latency and cost.

    Args:
        texts: List of strings to embed
        batch_size: Number of texts per API call (max 2048, we use 100 for safety)
        delay_between_batches: Seconds to wait between batches (avoids rate limits)

    Returns:
        List of embedding vectors in the same order as input texts.
    """
    if not texts:
        return []

    client = get_client()
    all_vectors = []
    total = len(texts)

    for i in range(0, total, batch_size):
        batch = texts[i: i + batch_size]
        batch_num = i // batch_size + 1
        total_batches = (total + batch_size - 1) // batch_size

        logger.info(
            "Embedding batch %d/%d (%d texts)...",
            batch_num, total_batches, len(batch)
        )

        # Retry logic for transient API errors
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = client.embeddings.create(
                    model=settings.OPENAI_EMBEDDING_MODEL,
                    input=batch,
                )

                # Results come back in the same order as input
                batch_vectors = [item.embedding for item in response.data]
                all_vectors.extend(batch_vectors)
                break

            except openai.RateLimitError:
                wait_time = (attempt + 1) * 10
                logger.warning(
                    "Rate limit hit. Waiting %d seconds before retry %d/%d...",
                    wait_time, attempt + 1, max_retries
                )
                time.sleep(wait_time)

            except openai.APIError as e:
                if attempt == max_retries - 1:
                    logger.error("Failed to embed batch after %d retries: %s", max_retries, e)
                    raise
                logger.warning("API error on attempt %d: %s. Retrying...", attempt + 1, e)
                time.sleep(2)

        # Polite delay between batches to avoid hammering the API
        if i + batch_size < total:
            time.sleep(delay_between_batches)

    logger.info(
        "Embedding complete: %d texts → %d vectors (dim=%d)",
        total, len(all_vectors),
        len(all_vectors[0]) if all_vectors else 0
    )

    return all_vectors
