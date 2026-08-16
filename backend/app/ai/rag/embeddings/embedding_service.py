"""
NEXUS EDU — Embedding Service (Serverless API Version).

Uses Hugging Face Serverless Inference API for embeddings to save RAM.
Uses BAAI/bge-small-en-v1.5 by default (384 dimensions).
"""

from __future__ import annotations

import logging
import httpx
from typing import TYPE_CHECKING

from app.core.config import Settings
from app.core.exceptions import EmbeddingError

logger = logging.getLogger(__name__)

_BGE_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "


class EmbeddingService:
    """
    Embedding service using Hugging Face Serverless Inference API.
    This keeps the backend RAM usage incredibly low by offloading the heavy ML model.
    """

    def __init__(self, settings: Settings) -> None:
        self._model_name = settings.embedding_model_name
        self._dimension = settings.embedding_dimension
        self._hf_token = settings.hf_token
        self._api_url = f"https://api-inference.huggingface.co/pipeline/feature-extraction/{self._model_name}"
        
        if not self._hf_token:
            logger.warning("No HF_TOKEN provided! Embedding service will use local fallback only.")

    @property
    def dimension(self) -> int:
        """Embedding vector dimensionality."""
        return self._dimension

    async def _embed_api(self, texts: list[str]) -> list[list[float]]:
        """Call Hugging Face Inference API to get embeddings."""
        if not self._hf_token:
            return [self._fallback_embed(t) for t in texts]

        headers = {"Authorization": f"Bearer {self._hf_token}"}
        payload = {"inputs": texts}

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(self._api_url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                
                # HF Inference API sometimes returns nested arrays depending on the model
                # Ensure we return a flat list of floats per text
                if isinstance(data, list) and len(data) > 0:
                    if isinstance(data[0], list):
                        # Some models return [batch_size, sequence_length, hidden_size]
                        # For BGE, it usually returns [batch_size, hidden_size]
                        # Let's handle both gracefully:
                        if isinstance(data[0][0], list):
                            # It's [batch, seq, hidden] -> pool by taking the first token (CLS) or mean
                            return [[float(x) for x in seq[0]] for seq in data]
                        else:
                            return [[float(x) for x in seq] for seq in data]
                
                raise EmbeddingError("Unexpected response format from Hugging Face API.")

        except httpx.HTTPError as exc:
            logger.warning("HF API Error (%s). Using lightweight fallback embedder.", exc)
            return [self._fallback_embed(t) for t in texts]
        except Exception as exc:
            logger.warning("Unexpected embedding error (%s). Using fallback embedder.", exc)
            return [self._fallback_embed(t) for t in texts]

    def _fallback_embed(self, text: str) -> list[float]:
        """Fast 384-dimensional deterministic feature vector for missing API keys/failures."""
        import hashlib
        import math

        vec = [0.0] * self._dimension
        words = text.lower().split()
        for idx, word in enumerate(words):
            h = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
            dim_idx = h % self._dimension
            vec[dim_idx] += 1.0 / (1.0 + math.log(idx + 1))
        norm = math.sqrt(sum(x * x for x in vec)) or 1.0
        return [x / norm for x in vec]

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of document texts."""
        if not texts:
            return []
        return await self._embed_api(texts)

    async def embed_query(self, query: str) -> list[float]:
        """Embed a single query with the BGE retrieval prefix."""
        prefixed = f"{_BGE_QUERY_PREFIX}{query}"
        results = await self._embed_api([prefixed])
        if results and len(results) > 0:
            return results[0]
        raise EmbeddingError("Failed to generate query embedding.")
