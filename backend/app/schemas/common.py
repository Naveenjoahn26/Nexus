"""
NEXUS EDU — Shared Pydantic Schemas.

Data models used across multiple modules. These are the contracts
between the RAG pipeline and downstream services (chat, lecture,
question paper, PPT, analysis).
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class RetrievedChunk(BaseModel):
    """A single retrieved chunk with relevance metadata."""

    chunk_id: str = Field(..., description="Unique identifier for the chunk.")
    content: str = Field(..., description="The text content of the chunk.")
    score: float = Field(..., description="Relevance score (higher is better).")
    metadata: dict = Field(
        default_factory=dict,
        description="Arbitrary metadata (document_id, page, chunk_type, etc.).",
    )


class IngestResult(BaseModel):
    """Result of a document ingestion operation."""

    document_id: str = Field(..., description="ID of the ingested document.")
    chunk_count: int = Field(
        ..., description="Total chunks created (child + parent)."
    )
    child_chunk_count: int = Field(
        ..., description="Number of child chunks indexed for retrieval."
    )
    parent_chunk_count: int = Field(
        ..., description="Number of parent chunks stored for context expansion."
    )
    status: str = Field(default="success")
