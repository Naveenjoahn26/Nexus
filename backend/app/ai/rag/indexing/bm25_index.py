"""
NEXUS EDU — BM25 Sparse Index.

Per-course BM25 index built from chunk texts stored in ChromaDB.
ChromaDB is the source of truth; BM25 is a derived, cached index.

Design decisions:
  - LRU cache: Hot courses stay in memory, cold ones are evicted.
  - Lazy building: Index is built on first query, not on ingestion.
    This avoids blocking document uploads with index construction.
  - Invalidation: When documents are added/removed, the cache entry
    is dropped. Next query triggers a rebuild.
  - Only child chunks are indexed (parents are for context expansion).
"""

from __future__ import annotations

import asyncio
import logging
import re
from collections import OrderedDict

from rank_bm25 import BM25Okapi

logger = logging.getLogger(__name__)


class BM25Index:
    """
    In-memory BM25 index with per-course isolation and LRU eviction.

    The index is derived from ChromaDB and rebuilt on demand.
    Invalidation is explicit — call invalidate(course_id) after
    any write operation.
    """

    def __init__(
        self,
        vector_store: "VectorStore",  # noqa: F821 — forward ref to avoid circular import
        max_cached_courses: int = 10,
    ) -> None:
        self._vector_store = vector_store
        self._max_cached = max_cached_courses

        # LRU cache: course_id → (BM25Okapi, chunk_ids, chunk_texts)
        self._cache: OrderedDict[
            str, tuple[BM25Okapi, list[str], list[str]]
        ] = OrderedDict()

    async def ensure_built(self, course_id: str) -> None:
        """Build the BM25 index if not already cached."""
        if course_id not in self._cache:
            await self._build(course_id)

    async def _build(self, course_id: str) -> None:
        """Fetch all child chunks from ChromaDB and build the BM25 index."""
        all_data = await self._vector_store.get_all_chunks(course_id)

        ids = all_data.get("ids", [])
        documents = all_data.get("documents", [])
        metadatas = all_data.get("metadatas", [])

        # Filter to child chunks only.
        child_ids: list[str] = []
        child_texts: list[str] = []
        for chunk_id, text, meta in zip(ids, documents, metadatas):
            if meta.get("chunk_type") == "child":
                child_ids.append(chunk_id)
                child_texts.append(text or "")

        if not child_ids:
            logger.warning(
                "No child chunks found for course '%s'. BM25 index will be empty.",
                course_id,
            )
            # Store an empty but valid index to avoid repeated rebuild attempts.
            self._cache[course_id] = (BM25Okapi([[""]]), [], [])
            self._cache.move_to_end(course_id)
            return

        tokenized = [self._tokenize(text) for text in child_texts]
        index = BM25Okapi(tokenized)

        # LRU eviction if cache is full.
        if len(self._cache) >= self._max_cached:
            evicted_key, _ = self._cache.popitem(last=False)
            logger.debug("Evicted BM25 cache for course: %s", evicted_key)

        self._cache[course_id] = (index, child_ids, child_texts)
        self._cache.move_to_end(course_id)

        logger.info(
            "Built BM25 index for course '%s': %d child chunks.",
            course_id,
            len(child_ids),
        )

    async def query(
        self,
        query: str,
        course_id: str,
        top_k: int = 20,
    ) -> list[tuple[str, str, float]]:
        """
        Query the BM25 index for a course.

        Lazily builds the index on first access.

        Args:
            query: The search query.
            course_id: Course to search within.
            top_k: Number of results.

        Returns:
            List of (chunk_id, content, bm25_score) tuples,
            sorted by score descending. Zero-score matches are excluded.
        """
        await self.ensure_built(course_id)
        return await asyncio.to_thread(self._query_sync, query, course_id, top_k)

    def _query_sync(
        self, query: str, course_id: str, top_k: int
    ) -> list[tuple[str, str, float]]:
        """Synchronous BM25 scoring and ranking."""
        if course_id not in self._cache:
            return []

        index, chunk_ids, chunk_texts = self._cache[course_id]
        self._cache.move_to_end(course_id)  # Touch for LRU freshness.

        tokens = self._tokenize(query)
        if not tokens:
            return []

        scores = index.get_scores(tokens)

        # Sort by score descending and take top-k non-zero results.
        scored_indices = sorted(
            enumerate(scores), key=lambda x: x[1], reverse=True
        )

        results: list[tuple[str, str, float]] = []
        for idx, score in scored_indices:
            if score <= 0:
                break  # Remaining scores are all zero (sorted desc).
            results.append((chunk_ids[idx], chunk_texts[idx], float(score)))
            if len(results) >= top_k:
                break

        return results

    def invalidate(self, course_id: str) -> None:
        """
        Remove a course from the cache, forcing rebuild on next query.

        Call this after any write operation (ingest, delete) for the course.
        """
        removed = self._cache.pop(course_id, None)
        if removed is not None:
            logger.debug("Invalidated BM25 cache for course: %s", course_id)

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        """
        Simple whitespace tokenization with lowercasing and punctuation removal.

        Drops single-character tokens (articles, stray letters) to reduce noise.
        """
        text = text.lower()
        text = re.sub(r"[^\w\s]", " ", text)
        return [token for token in text.split() if len(token) > 1]
