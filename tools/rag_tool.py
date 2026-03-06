"""
tools/rag_tool.py

The RAG Tool searches the vector store for document chunks that are
semantically relevant to a question, and returns them as context
the agent can use in its reasoning.

How it works:
    1. Agent calls rag_tool("What is a healthy runway for a SaaS startup?")
    2. Tool embeds the question using the same model used during ingestion
    3. Tool searches FAISS for the most similar document chunks
    4. Tool returns the chunks as formatted text with source attribution
    5. Agent reads the chunks and uses them as knowledge in its answer

Why source attribution matters:
    The agent should be able to say "According to the SaaS Metrics Guide,
    Series A investors typically look for $100k MRR..." rather than just
    asserting things. Source attribution makes the agent trustworthy.
"""

import logging

from ingest.embedder import embed_text
from ingest.vector_store import get_vector_store
from config.settings import settings

logger = logging.getLogger(__name__)


def _format_chunks(results: list[dict]) -> str:
    """
    Format retrieved chunks as readable context for the agent.
    Includes source attribution so the agent can cite its sources.
    """
    if not results:
        return "No relevant documents found."

    lines = []
    for i, result in enumerate(results, 1):
        source = result["source_file"].replace("\\", "/")
        section = result["section"]
        similarity = result["similarity"]

        lines.append(f"[Source {i}: {source} — {section}] (relevance: {similarity:.2f})")
        lines.append(result["text"])
        lines.append("")  # Empty line between chunks

    return "\n".join(lines)


class RAGTool:
    """
    The RAG tool the agent calls to retrieve financial planning knowledge.

    Usage:
        tool = RAGTool()
        result = tool.run(
            "What is a healthy food cost percentage for a café?",
            business_type="restaurant"
        )
    """

    NAME = "rag_tool"
    DESCRIPTION = """Use this tool to retrieve financial planning knowledge, best practices,
benchmarks, and guidance from the document library.
Use it for questions about: industry benchmarks, recommended ratios, financial strategies,
what healthy metrics look like, how to interpret financial data, cost-cutting strategies,
and any question requiring financial planning expertise rather than raw data.
Input: a clear natural language question about financial best practices or benchmarks.
Output: relevant excerpts from financial planning documents with source attribution."""

    def __init__(self, top_k: int = None):
        self.top_k = top_k or settings.RAG_TOP_K
        self._store = None

    def _get_store(self):
        """Lazy load the vector store."""
        if self._store is None:
            self._store = get_vector_store()
        return self._store

    def run(self, question: str, business_type: str = None) -> str:
        """
        Search for relevant document chunks and return them as context.

        Args:
            question: Natural language question to search for
            business_type: Optional filter — restricts results to chunks
                          relevant to this business type (plus 'general' docs)
                          Values: 'restaurant', 'retail', 'saas',
                                  'funded_startup', 'freelance', or None

        Returns:
            Formatted document excerpts as a string
        """
        logger.info(
            "RAGTool: '%s' (business_type=%s)", question, business_type or "all"
        )

        try:
            # Embed the question using the same model used during ingestion
            query_vector = embed_text(question)

            # Search the vector store
            store = self._get_store()
            results = store.search(
                query_vector=query_vector,
                top_k=self.top_k,
                business_type_filter=business_type,
            )

            if not results:
                logger.warning("RAGTool: No results found for: %s", question)
                return "No relevant documents found for this question."

            logger.info("RAGTool: Found %d relevant chunks", len(results))
            return _format_chunks(results)

        except Exception as e:
            error_msg = f"RAG tool error: {e}"
            logger.error(error_msg)
            return error_msg
