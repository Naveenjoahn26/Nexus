"""
NEXUS EDU — Cross-Encoder Reranker + MMR Diversity Selection.

Two-stage post-retrieval refinement:
  1. Cross-encoder reranking — scores each (query, chunk) pair jointly. Offloaded to Hugging Face API.
  2. MMR selection — ensures the final chunk set is diverse.
"""

from __future__ import annotations

import asyncio
import logging
import httpx
import numpy as np

from app.core.config import Settings
from app.schemas.common import RetrievedChunk

logger = logging.getLogger(__name__)


class Reranker:
    """
    Cross-encoder reranker with optional MMR diversity selection.
    Uses Hugging Face Serverless Inference API to save RAM.
    """

    def __init__(self, settings: Settings) -> None:
        self._model_name = settings.reranker_model_name
        self._hf_token = settings.hf_token
        self._api_url = f"https://api-inference.huggingface.co/models/{self._model_name}"

    # ── Reranking ────────────────────────────────────────────────

    async def rerank(
        self,
        query: str,
        chunks: list[RetrievedChunk],
        top_k: int = 5,
    ) -> list[RetrievedChunk]:
        """Rerank chunks using Hugging Face Serverless API."""
        if not chunks:
            return []

        if len(chunks) <= top_k:
            return chunks

        return await self._rerank_api(query, chunks, top_k)

    async def _rerank_api(
        self,
        query: str,
        chunks: list[RetrievedChunk],
        top_k: int,
    ) -> list[RetrievedChunk]:
        """Call Hugging Face Inference API to rerank pairs."""
        if not self._hf_token:
            logger.warning("No HF_TOKEN provided! Skipping reranking.")
            return chunks[:top_k]

        headers = {"Authorization": f"Bearer {self._hf_token}"}
        # HF Inference API for sentence classification accepts text pairs
        payload = {"inputs": [{"text": query, "text_pair": chunk.content} for chunk in chunks]}

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(self._api_url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()

                # HF returns a list of lists of dicts e.g. [[{'label': 'LABEL_0', 'score': 0.9}]]
                # For cross-encoders, we take the primary score
                scores = []
                for res in data:
                    if isinstance(res, list) and len(res) > 0 and 'score' in res[0]:
                        scores.append(res[0]['score'])
                    elif isinstance(res, dict) and 'score' in res:
                        scores.append(res['score'])
                    else:
                        scores.append(0.0)

                if len(scores) != len(chunks):
                    raise ValueError("Score count does not match chunk count.")

                scored = sorted(zip(chunks, scores), key=lambda x: x[1], reverse=True)

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
            logger.warning("HF Reranker API failed (%s). Returning un-reranked chunks.", exc)
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
