"""
NEXUS EDU — ChromaDB Vector Store.

Manages persistent vector storage with per-course collection isolation.
Each course gets its own ChromaDB collection, ensuring retrieval
is always scoped to the correct document set.

ChromaDB is the single source of truth for all chunk data —
BM25 indices are derived from it and rebuilt on demand.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

import chromadb

from app.ai.rag.chunking.recursive_chunker import Chunk
from app.core.config import Settings
from app.core.exceptions import IndexingError

logger = logging.getLogger(__name__)


class VectorStore:
    """
    ChromaDB-backed persistent vector store.

    Collections are scoped per-course to enable fast filtered retrieval
    without the overhead of metadata-based WHERE clauses on a single
    large collection.
    """

    def __init__(self, settings: Settings) -> None:
        persist_dir = Path(settings.chroma_persist_dir)
        persist_dir.mkdir(parents=True, exist_ok=True)

        self._client = chromadb.PersistentClient(path=str(persist_dir))
        logger.info("ChromaDB initialized at: %s", persist_dir)

    def _collection_name(self, course_id: str) -> str:
        """Generate a deterministic, ChromaDB-safe collection name."""
        # ChromaDB names: 3–63 chars, [a-zA-Z0-9_-], start/end with alphanum.
        safe_id = course_id.replace("-", "_").replace(" ", "_")
        name = f"nexus_{safe_id}"
        # Enforce ChromaDB length constraints.
        return name[:63] if len(name) > 63 else name

    def _get_collection(self, course_id: str) -> chromadb.Collection:
        """Get or create a collection for a course."""
        return self._client.get_or_create_collection(
            name=self._collection_name(course_id),
            metadata={"hnsw:space": "cosine"},
        )

    # ── Write Operations ─────────────────────────────────────────

    async def add_chunks(
        self,
        chunks: list[Chunk],
        embeddings: list[list[float]],
        course_id: str,
    ) -> None:
        """
        Upsert chunks with their embeddings into the course collection.

        Uses upsert (not add) to make re-ingestion idempotent —
        the same document can be re-processed without duplicates.

        Args:
            chunks: List of Chunk objects to store.
            embeddings: Corresponding embedding vectors (same order).
            course_id: Course this document belongs to.

        Raises:
            IndexingError: If chunk/embedding count mismatch or upsert fails.
        """
        if not chunks:
            return

        if len(chunks) != len(embeddings):
            raise IndexingError(
                f"Chunk count ({len(chunks)}) != embedding count ({len(embeddings)})."
            )

        await asyncio.to_thread(self._upsert_sync, chunks, embeddings, course_id)

    def _upsert_sync(
        self,
        chunks: list[Chunk],
        embeddings: list[list[float]],
        course_id: str,
    ) -> None:
        """Synchronous upsert with automatic batching."""
        collection = self._get_collection(course_id)

        # ChromaDB recommends batches ≤ 5000 for large upserts.
        batch_size = 5000
        for i in range(0, len(chunks), batch_size):
            batch_chunks = chunks[i : i + batch_size]
            batch_embeddings = embeddings[i : i + batch_size]

            collection.upsert(
                ids=[c.chunk_id for c in batch_chunks],
                embeddings=batch_embeddings,
                documents=[c.content for c in batch_chunks],
                metadatas=[c.metadata for c in batch_chunks],
            )

        logger.info(
            "Upserted %d chunks into '%s'.",
            len(chunks),
            self._collection_name(course_id),
        )

    async def delete_document(self, document_id: str, course_id: str) -> int:
        """
        Delete all chunks belonging to a specific document.

        Returns the number of chunks deleted.
        """
        return await asyncio.to_thread(
            self._delete_document_sync, document_id, course_id
        )

    def _delete_document_sync(self, document_id: str, course_id: str) -> int:
        """Synchronous document deletion."""
        collection = self._get_collection(course_id)

        # Fetch IDs first, then delete by ID (ChromaDB doesn't return
        # count from delete-by-where).
        existing = collection.get(
            where={"document_id": document_id},
            include=[],
        )
        chunk_ids = existing.get("ids", [])

        if chunk_ids:
            collection.delete(ids=chunk_ids)
            logger.info(
                "Deleted %d chunks for document '%s' from '%s'.",
                len(chunk_ids),
                document_id,
                self._collection_name(course_id),
            )
        return len(chunk_ids)

    async def delete_course(self, course_id: str) -> None:
        """Delete the entire collection for a course."""
        name = self._collection_name(course_id)
        try:
            await asyncio.to_thread(self._client.delete_collection, name)
            logger.info("Deleted collection: %s", name)
        except Exception:
            logger.warning("Collection '%s' not found, nothing to delete.", name)

    # ── Read Operations ──────────────────────────────────────────

    async def query(
        self,
        embedding: list[float],
        course_id: str,
        top_k: int = 20,
        where: dict | None = None,
    ) -> dict:
        """
        Query the collection by embedding similarity.

        Args:
            embedding: Query embedding vector.
            course_id: Course to search within.
            top_k: Number of results to return.
            where: Optional ChromaDB metadata filter (e.g., {"chunk_type": "child"}).

        Returns:
            ChromaDB result dict with keys: ids, documents, metadatas, distances.
            All values are nested lists (outer list = queries, inner = results).
        """
        return await asyncio.to_thread(
            self._query_sync, embedding, course_id, top_k, where
        )

    def _query_sync(
        self,
        embedding: list[float],
        course_id: str,
        top_k: int,
        where: dict | None,
    ) -> dict:
        """Synchronous cosine similarity query."""
        collection = self._get_collection(course_id)

        query_params: dict = {
            "query_embeddings": [embedding],
            "n_results": min(top_k, collection.count() or top_k),
            "include": ["documents", "metadatas", "distances"],
        }
        if where:
            query_params["where"] = where

        try:
            return collection.query(**query_params)
        except Exception as exc:
            logger.error("ChromaDB query failed: %s", exc)
            return {
                "ids": [[]],
                "documents": [[]],
                "metadatas": [[]],
                "distances": [[]],
            }

    async def get_by_ids(self, chunk_ids: list[str], course_id: str) -> dict:
        """
        Fetch specific chunks by their IDs.

        Used for parent chunk expansion after child retrieval.
        """
        if not chunk_ids:
            return {"ids": [], "documents": [], "metadatas": []}
        return await asyncio.to_thread(
            self._get_by_ids_sync, chunk_ids, course_id
        )

    def _get_by_ids_sync(self, chunk_ids: list[str], course_id: str) -> dict:
        """Synchronous ID-based fetch."""
        collection = self._get_collection(course_id)
        try:
            return collection.get(ids=chunk_ids, include=["documents", "metadatas"])
        except Exception as exc:
            logger.error("ChromaDB get_by_ids failed: %s", exc)
            return {"ids": [], "documents": [], "metadatas": []}

    async def get_embeddings_by_ids(self, chunk_ids: list[str], course_id: str) -> dict:
        """
        Fetch specific chunks by their IDs, including their embeddings.
        
        Used to optimize MMR reranking by avoiding redundant embed model calls.
        """
        if not chunk_ids:
            return {"ids": [], "documents": [], "metadatas": [], "embeddings": []}
        return await asyncio.to_thread(
            self._get_embeddings_by_ids_sync, chunk_ids, course_id
        )

    def _get_embeddings_by_ids_sync(self, chunk_ids: list[str], course_id: str) -> dict:
        """Synchronous ID-based fetch with embeddings."""
        collection = self._get_collection(course_id)
        try:
            return collection.get(ids=chunk_ids, include=["documents", "metadatas", "embeddings"])
        except Exception as exc:
            logger.error("ChromaDB get_embeddings_by_ids failed: %s", exc)
            return {"ids": [], "documents": [], "metadatas": [], "embeddings": []}

    async def get_all_chunks(self, course_id: str) -> dict:
        """
        Fetch all chunks in a course collection.

        Used by BM25Index to build the sparse retrieval index.
        Returns all stored documents with their metadata.
        """
        return await asyncio.to_thread(self._get_all_sync, course_id)

    def _get_all_sync(self, course_id: str) -> dict:
        """Synchronous full collection fetch."""
        collection = self._get_collection(course_id)
        return collection.get(include=["documents", "metadatas"])
