"""
NEXUS EDU — Hybrid Retriever with Reciprocal Rank Fusion.

Combines dense (embedding) and sparse (BM25) retrieval for
maximum recall, then fuses results using RRF.

Why RRF over weighted linear combination:
  - BM25 scores and cosine similarities are on incompatible scales.
    Normalizing them requires dataset-specific tuning.
  - RRF only cares about rank position, making it scale-invariant.
  - Single hyperparameter (k=60 is robust across domains).
  - Chunks appearing in BOTH result lists get a natural score boost,
    which is a strong relevance signal.
"""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict

from app.ai.rag.retrieval.dense_retriever import DenseRetriever
from app.ai.rag.retrieval.sparse_retriever import SparseRetriever
from app.schemas.common import RetrievedChunk

logger = logging.getLogger(__name__)


class HybridRetriever:
    """
    Hybrid retrieval with Reciprocal Rank Fusion (RRF).

    RRF formula: score(d) = Σ 1 / (k + rank_i(d))
    where k is a constant and rank_i is the 1-indexed position
    of document d in result list i.
    """

    def __init__(
        self,
        dense_retriever: DenseRetriever,
        sparse_retriever: SparseRetriever,
        rrf_k: int = 60,
    ) -> None:
        self._dense = dense_retriever
        self._sparse = sparse_retriever
        self._rrf_k = rrf_k

    async def retrieve(
        self,
        query: str,
        course_id: str,
        dense_top_k: int = 20,
        sparse_top_k: int = 20,
        final_top_k: int = 20,
    ) -> list[RetrievedChunk]:
        """
        Run dense and sparse retrieval concurrently, then fuse with RRF.

        Args:
            query: The search query.
            course_id: Course to search within.
            dense_top_k: Number of dense results to fetch.
            sparse_top_k: Number of sparse results to fetch.
            final_top_k: Number of fused results to return.

        Returns:
            Fused list of RetrievedChunks sorted by RRF score (descending).
        """
        # Run both retrievers in parallel for minimum latency.
        dense_results, sparse_results = await asyncio.gather(
            self._dense.retrieve(query, course_id, dense_top_k),
            self._sparse.retrieve(query, course_id, sparse_top_k),
        )

        logger.debug(
            "Hybrid retrieval — Dense: %d results, Sparse: %d results.",
            len(dense_results),
            len(sparse_results),
        )

        fused = self._reciprocal_rank_fusion(
            dense_results, sparse_results, final_top_k
        )

        logger.debug("RRF fusion produced %d results.", len(fused))
        return fused

    def _reciprocal_rank_fusion(
        self,
        dense_results: list[RetrievedChunk],
        sparse_results: list[RetrievedChunk],
        top_k: int,
    ) -> list[RetrievedChunk]:
        """
        Fuse two ranked lists using RRF.

        Each chunk's score = sum of 1/(k + rank) across all lists
        it appears in. Chunks appearing in both lists are naturally
        boosted — a strong relevance signal.
        """
        rrf_scores: dict[str, float] = defaultdict(float)
        chunk_map: dict[str, RetrievedChunk] = {}

        # Score dense results by rank position.
        for rank, chunk in enumerate(dense_results, start=1):
            rrf_scores[chunk.chunk_id] += 1.0 / (self._rrf_k + rank)
            chunk_map[chunk.chunk_id] = chunk

        # Score sparse results by rank position.
        for rank, chunk in enumerate(sparse_results, start=1):
            rrf_scores[chunk.chunk_id] += 1.0 / (self._rrf_k + rank)
            # Prefer the dense version if the chunk appears in both
            # (dense has richer metadata from ChromaDB).
            if chunk.chunk_id not in chunk_map:
                chunk_map[chunk.chunk_id] = chunk

        # Sort by fused RRF score (descending) and take top-k.
        sorted_ids = sorted(
            rrf_scores.keys(),
            key=lambda cid: rrf_scores[cid],
            reverse=True,
        )[:top_k]

        return [
            RetrievedChunk(
                chunk_id=cid,
                content=chunk_map[cid].content,
                score=rrf_scores[cid],
                metadata=chunk_map[cid].metadata,
            )
            for cid in sorted_ids
        ]
