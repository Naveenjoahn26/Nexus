"""
NEXUS EDU — Embedding Service.

Wraps sentence-transformers with lazy model loading and async interface.
Uses BAAI/bge-small-en-v1.5 by default (384 dimensions).

Design decisions:
  - Lazy loading: Model is loaded on first call, not at import time.
    This keeps application startup fast and avoids loading the model
    for routes that don't need embeddings.
  - Thread-safe singleton: The model is loaded once and shared across
    all requests via a double-check lock pattern.
  - BGE query prefix: BGE models produce better retrieval embeddings
    when queries include a task-specific prefix.
"""

from __future__ import annotations

import asyncio
import logging
import threading
from typing import TYPE_CHECKING

from app.core.config import Settings
from app.core.exceptions import EmbeddingError

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

# BGE models use this prefix to differentiate queries from documents.
# This improves retrieval quality by ~2-3% on standard benchmarks.
_BGE_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "


class EmbeddingService:
    """
    Thread-safe embedding service with lazy model loading.

    The sentence-transformers model is loaded on first use and cached
    for the lifetime of the process. All encoding is offloaded to a
    thread pool to keep the async event loop responsive.
    """

    def __init__(self, settings: Settings) -> None:
        self._model_name = settings.embedding_model_name
        self._batch_size = settings.embedding_batch_size
        self._dimension = settings.embedding_dimension
        self._model: SentenceTransformer | None = None
        self._lock = threading.Lock()

    @property
    def dimension(self) -> int:
        """Embedding vector dimensionality."""
        return self._dimension

    def _get_model(self) -> SentenceTransformer:
        """Lazy-load the model on first use (double-check locking)."""
        if self._model is None:
            with self._lock:
                if self._model is None:
                    try:
                        from sentence_transformers import SentenceTransformer

                        logger.info("Loading embedding model: %s", self._model_name)
                        self._model = SentenceTransformer(self._model_name)
                        logger.info("Embedding model loaded successfully.")
                    except Exception as exc:
                        raise EmbeddingError(
                            f"Failed to load embedding model '{self._model_name}': {exc}"
                        ) from exc
        return self._model

    def _embed_sync(self, texts: list[str]) -> list[list[float]]:
        """Synchronous batch embedding with L2 normalization."""
        model = self._get_model()
        embeddings = model.encode(
            texts,
            batch_size=self._batch_size,
            show_progress_bar=False,
            normalize_embeddings=True,  # L2 normalize for cosine similarity
        )
        return embeddings.tolist()

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """
        Embed a batch of document texts (no query prefix).

        Args:
            texts: List of text strings to embed.

        Returns:
            List of embedding vectors (each has `self.dimension` floats).

        Raises:
            EmbeddingError: If encoding fails.
        """
        if not texts:
            return []

        try:
            return await asyncio.to_thread(self._embed_sync, texts)
        except EmbeddingError:
            raise
        except Exception as exc:
            raise EmbeddingError(f"Batch embedding failed: {exc}") from exc

    async def embed_query(self, query: str) -> list[float]:
        """
        Embed a single query with the BGE retrieval prefix.

        The prefix signals to the model that this is a search query,
        improving retrieval relevance vs. treating it as a document.

        Args:
            query: The search query string.

        Returns:
            A single embedding vector.

        Raises:
            EmbeddingError: If encoding fails.
        """
        prefixed = f"{_BGE_QUERY_PREFIX}{query}"
        try:
            results = await asyncio.to_thread(self._embed_sync, [prefixed])
            return results[0]
        except EmbeddingError:
            raise
        except Exception as exc:
            raise EmbeddingError(f"Query embedding failed: {exc}") from exc
