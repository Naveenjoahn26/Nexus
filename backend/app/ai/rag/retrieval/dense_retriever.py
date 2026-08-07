"""
NEXUS EDU — Dense Retriever.

Embedding-based semantic retrieval using ChromaDB.
Encodes the query with the BGE prefix, then performs cosine
similarity search against indexed child chunks.
"""

from __future__ import annotations

import logging

from app.ai.rag.embeddings.embedding_service import EmbeddingService
from app.ai.rag.indexing.vector_store import VectorStore
from app.schemas.common import RetrievedChunk

logger = logging.getLogger(__name__)


class DenseRetriever:
    """Embedding-based dense retrieval using ChromaDB."""

    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_store: VectorStore,
    ) -> None:
        self._embedder = embedding_service
        self._store = vector_store

    async def retrieve(
        self,
        query: str,
        course_id: str,
        top_k: int = 20,
    ) -> list[RetrievedChunk]:
        """
        Retrieve top-k chunks by embedding cosine similarity.

        Only searches child chunks — parents are stored for context
        expansion but never returned by the retriever directly.

        Args:
            query: The search query.
            course_id: Course to search within.
            top_k: Number of results.

        Returns:
            List of RetrievedChunks sorted by similarity (descending).
        """
        query_embedding = await self._embedder.embed_query(query)

        results = await self._store.query(
            embedding=query_embedding,
            course_id=course_id,
            top_k=top_k,
            where={"chunk_type": "child"},
        )

        return self._parse_results(results)

    @staticmethod
    def _parse_results(results: dict) -> list[RetrievedChunk]:
        """Convert ChromaDB result format to RetrievedChunk list."""
        chunks: list[RetrievedChunk] = []

        # ChromaDB returns nested lists: outer = queries, inner = results.
        ids = results.get("ids", [[]])[0]
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for chunk_id, content, metadata, distance in zip(
            ids, documents, metadatas, distances
        ):
            # ChromaDB cosine distance = 1 - cosine_similarity.
            # Convert back to similarity so higher = better.
            similarity = max(0.0, 1.0 - distance)

            chunks.append(
                RetrievedChunk(
                    chunk_id=chunk_id,
                    content=content or "",
                    score=similarity,
                    metadata=metadata or {},
                )
            )

        return chunks
