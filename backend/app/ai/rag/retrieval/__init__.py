"""
NEXUS EDU — Retrieval Strategies.

Provides dense, sparse, and hybrid retrieval with RRF fusion.
"""

from app.ai.rag.retrieval.dense_retriever import DenseRetriever
from app.ai.rag.retrieval.hybrid_retriever import HybridRetriever
from app.ai.rag.retrieval.sparse_retriever import SparseRetriever

__all__ = ["DenseRetriever", "HybridRetriever", "SparseRetriever"]
