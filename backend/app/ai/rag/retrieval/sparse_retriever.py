"""
NEXUS EDU — Sparse Retriever.

BM25-based lexical retrieval for exact term matching.
Excels at finding specific academic terms, theorem names,
formulas, and definitions that dense retrieval often misses.
"""

from __future__ import annotations

import logging

from app.ai.rag.indexing.bm25_index import BM25Index
from app.schemas.common import RetrievedChunk

logger = logging.getLogger(__name__)


class SparseRetriever:
    """BM25-based sparse retrieval for keyword matching."""

    def __init__(self, bm25_index: BM25Index) -> None:
        self._bm25 = bm25_index

    async def retrieve(
        self,
        query: str,
        course_id: str,
        top_k: int = 20,
    ) -> list[RetrievedChunk]:
        """
        Retrieve top-k chunks by BM25 lexical score.

        The BM25 index is built lazily on first access for the course.

        Args:
            query: The search query.
            course_id: Course to search within.
            top_k: Number of results.

        Returns:
            List of RetrievedChunks sorted by BM25 score (descending).
        """
        results = await self._bm25.query(query, course_id, top_k)

        return [
            RetrievedChunk(
                chunk_id=chunk_id,
                content=content,
                score=score,
                metadata={"retrieval_method": "bm25"},
            )
            for chunk_id, content, score in results
        ]
