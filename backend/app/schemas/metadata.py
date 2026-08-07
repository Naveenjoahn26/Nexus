"""
NEXUS EDU — Generation Metadata Schema.

Reusable Pydantic model for AI observability telemetry.
Saved into the JSONB generation_metadata column on the Message table.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated

from pydantic import BaseModel, Field


class GenerationMetadata(BaseModel):
    """
    Telemetry and observability metadata for every AI generation.
    Matches the schema required for the AI Orchestrator.
    """
    model_name: Annotated[
        str, Field(description="The exact name/version of the LLM used (e.g., llama3-groq-70b-8192-tool-use-preview).")
    ]
    prompt_name: Annotated[
        str, Field(description="The logical name of the prompt template used (e.g., 'generate_lecture_notes').")
    ]
    prompt_version: Annotated[
        str, Field(description="Version hash or semantic version of the prompt.")
    ]
    latency_ms: Annotated[
        float, Field(ge=0.0, description="Total wall-clock latency of the generation in milliseconds.")
    ]
    retrieval_time_ms: Annotated[
        float, Field(ge=0.0, description="Time spent in the RAG retrieval pipeline in milliseconds.")
    ]
    generation_time_ms: Annotated[
        float, Field(ge=0.0, description="Time spent waiting for the LLM API in milliseconds.")
    ]
    retry_count: Annotated[
        int, Field(ge=0, description="Number of times the LLM was retried due to validation failures.")
    ]
    token_usage: Annotated[
        dict[str, int] | None, Field(default=None, description="Input, output, and total token usage.")
    ]
    retrieved_document_count: Annotated[
        int, Field(ge=0, description="Number of distinct source documents referenced.")
    ]
    retrieved_sources: Annotated[
        list[str], Field(default_factory=list, description="List of document IDs or chunk IDs retrieved.")
    ]
    correlation_id: Annotated[
        str | None, Field(default=None, description="Unique trace ID to correlate this request across services.")
    ]
    error_type: Annotated[
        str | None, Field(default=None, description="The type of error encountered, if any (e.g., 'TimeoutError').")
    ]
    error_message: Annotated[
        str | None, Field(default=None, description="The specific error message.")
    ]
    is_failure: Annotated[
        bool, Field(default=False, description="True if the generation request failed.")
    ]
    source_attribution_scores: Annotated[
        dict[str, float] | None, Field(default=None, description="Mapping of source document IDs to their attribution confidence scores.")
    ]
    created_at: Annotated[
        datetime, Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp of generation.")
    ]
