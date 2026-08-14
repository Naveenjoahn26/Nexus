"""
NEXUS EDU — Cross-Encoder Reranker + MMR Diversity Selection.

Two-stage post-retrieval refinement:
  1. Cross-encoder reranking — scores each (query, chunk) pair jointly
     for much higher precision than bi-encoder similarity.
  2. MMR selection — ensures the final chunk set is diverse, preventing
     redundant information from wasting LLM context tokens.

The cross-encoder is lazy-loaded and thread-safe (same pattern as
the embedding service). MMR uses pre-computed embeddings to measure
inter-chunk similarity.
"""

from __future__ import annotations

import asyncio
import logging
import threading
from typing import TYPE_CHECKING

import numpy as np

from app.core.config import Settings
from app.schemas.common import RetrievedChunk

if TYPE_CHECKING:
    from sentence_transformers import CrossEncoder

logger = logging.getLogger(__name__)


class Reranker:
    """
    Cross-encoder reranker with optional MMR diversity selection.

    The cross-encoder evaluates each (query, document) pair jointly,
    achieving significantly higher precision than the bi-encoder used
    for initial retrieval. This is the highest-ROI post-retrieval step.
    """

    def __init__(self, settings: Settings) -> None:
        self._model_name = settings.reranker_model_name
        self._model: CrossEncoder | None = None
        self._lock = threading.Lock()

    def _get_model(self) -> CrossEncoder:
        """Lazy-load the cross-encoder (double-check locking)."""
        if self._model is None:
            with self._lock:
                if self._model is None:
                    from sentence_transformers import CrossEncoder

                    logger.info("Loading reranker model: %s", self._model_name)
                    self._model = CrossEncoder(self._model_name)
                    logger.info("Reranker model loaded successfully.")
        return self._model

    # ── Reranking ────────────────────────────────────────────────

    async def rerank(
        self,
        query: str,
        chunks: list[RetrievedChunk],
        top_k: int = 5,
    ) -> list[RetrievedChunk]:
        """
        Rerank chunks using the cross-encoder.

        Args:
            query: The search query.
            chunks: Candidate chunks from hybrid retrieval.
            top_k: Number of top results to return.

        Returns:
            Top-k chunks sorted by cross-encoder relevance score.
        """
        if not chunks:
            return []

        if len(chunks) <= top_k:
            return chunks

        return await asyncio.to_thread(self._rerank_sync, query, chunks, top_k)

    def _rerank_sync(
        self,
        query: str,
        chunks: list[RetrievedChunk],
        top_k: int,
    ) -> list[RetrievedChunk]:
        """Synchronous cross-encoder scoring with fallback."""
        try:
            model = self._get_model()
            pairs = [[query, chunk.content] for chunk in chunks]
            scores = model.predict(pairs, show_progress_bar=False)

            scored = sorted(
                zip(chunks, scores), key=lambda x: x[1], reverse=True
            )

            return [
                RetrievedChunk(
                    chunk_id=chunk.chunk_id,
                    content=chunk.content,
                    score=float(score),
                    metadata=chunk.metadata,
                )
                for chunk, score in scored[:top_k]
            ]
        except Exception as exc:
            logger.warning("Cross-encoder reranker unavailable (%s). Returning top candidate chunks.", exc)
            return chunks[:top_k]

    # ── Reranking + MMR ──────────────────────────────────────────

    async def rerank_with_mmr(
        self,
        query: str,
        chunks: list[RetrievedChunk],
        embeddings: list[list[float]],
        top_k: int = 5,
        mmr_lambda: float = 0.7,
    ) -> list[RetrievedChunk]:
        """
        Rerank with cross-encoder, then apply MMR for diversity.

        Pipeline: cross-encoder scoring → take 3x top_k pool → MMR select top_k.

        Args:
            query: The search query.
            chunks: Candidate chunks from hybrid retrieval.
            embeddings: Pre-computed embeddings for MMR similarity (same order as chunks).
            top_k: Final number of diverse, relevant chunks.
            mmr_lambda: Relevance vs. diversity trade-off (1.0 = pure relevance).

        Returns:
            Top-k diverse, relevant chunks.
        """
        if not chunks:
            return []

        if len(chunks) <= top_k:
            return chunks

        # Step 1: Rerank with cross-encoder (pool 3x top_k for MMR selection).
        pool_size = min(len(chunks), top_k * 3)
        reranked = await self.rerank(query, chunks, top_k=pool_size)

        if len(reranked) <= top_k:
            return reranked

        # Step 2: Build embedding map for MMR.
        chunk_to_emb = {c.chunk_id: emb for c, emb in zip(chunks, embeddings)}

        pool_chunks: list[RetrievedChunk] = []
        pool_embeddings: list[list[float]] = []
        for chunk in reranked:
            emb = chunk_to_emb.get(chunk.chunk_id)
            if emb is not None:
                pool_chunks.append(chunk)
                pool_embeddings.append(emb)

        if len(pool_chunks) <= top_k:
            return pool_chunks

        # Step 3: MMR diversity selection.
        return await asyncio.to_thread(
            self._mmr_select, pool_chunks, pool_embeddings, top_k, mmr_lambda
        )

    @staticmethod
    def _mmr_select(
        chunks: list[RetrievedChunk],
        embeddings: list[list[float]],
        top_k: int,
        mmr_lambda: float,
    ) -> list[RetrievedChunk]:
        """
        Maximal Marginal Relevance selection.

        MMR(d) = λ · Relevance(d) − (1−λ) · max_sim(d, S)

        where S is the set of already-selected chunks. This greedily
        selects the next chunk that maximizes a combination of relevance
        (from the cross-encoder) and novelty (low similarity to already
        selected chunks).

        Relevance scores are normalized to [0, 1] for fair weighting.
        Similarity is computed via dot product on L2-normalized embeddings
        (equivalent to cosine similarity).
        """
        if not chunks:
            return []

        n = len(chunks)
        emb_matrix = np.array(embeddings, dtype=np.float32)

        # Normalize relevance scores to [0, 1].
        scores = np.array([c.score for c in chunks], dtype=np.float32)
        score_range = scores.max() - scores.min()
        if score_range > 0:
            norm_scores = (scores - scores.min()) / score_range
        else:
            norm_scores = np.ones(n, dtype=np.float32)

        # Pre-compute pairwise cosine similarity matrix.
        # Embeddings are already L2-normalized from sentence-transformers.
        sim_matrix = emb_matrix @ emb_matrix.T

        selected: list[int] = []
        candidates = set(range(n))

        for _ in range(min(top_k, n)):
            if not candidates:
                break

            if not selected:
                # First pick: highest relevance.
                best = max(candidates, key=lambda i: norm_scores[i])
            else:
                best = -1
                best_mmr = -float("inf")

                for idx in candidates:
                    relevance = float(norm_scores[idx])
                    max_sim = max(float(sim_matrix[idx][s]) for s in selected)
                    mmr_score = mmr_lambda * relevance - (1 - mmr_lambda) * max_sim

                    if mmr_score > best_mmr:
                        best_mmr = mmr_score
                        best = idx

            selected.append(best)
            candidates.discard(best)

        return [chunks[i] for i in selected]
