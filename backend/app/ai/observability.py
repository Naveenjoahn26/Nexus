"""
NEXUS EDU — AI Observability Tracker.

Manages the lifecycle, metrics, and trace contexts of AI generation requests.
"""

from __future__ import annotations

import time
import uuid
from typing import Any

from app.schemas.metadata import GenerationMetadata


class AIObservabilityTracker:
    """
    Context manager and tracker for AI generation observability.
    Captures latency, tokens, trace IDs, and evaluations to produce GenerationMetadata.
    """

    def __init__(self, model_name: str, prompt_name: str, prompt_version: str = "1.0.0"):
        self.correlation_id = str(uuid.uuid4())
        self.model_name = model_name
        self.prompt_name = prompt_name
        self.prompt_version = prompt_version
        
        self.start_time: float = time.perf_counter()
        self.end_time: float | None = None
        
        self.retrieval_time_ms: float = 0.0
        self.generation_time_ms: float = 0.0
        self.retry_count: int = 0
        self.token_usage: dict[str, int] | None = None
        self.retrieved_sources: list[str] = []
        self.source_attribution_scores: dict[str, float] | None = None
        
        # Error tracking
        self.error_type: str | None = None
        self.error_message: str | None = None
        self.is_failure: bool = False

    def record_retrieval(self, latency_ms: float, sources: list[str], attribution_scores: dict[str, float] | None = None) -> None:
        """Record metrics related to the RAG retrieval phase."""
        self.retrieval_time_ms = latency_ms
        self.retrieved_sources = sources
        self.source_attribution_scores = attribution_scores

    def record_generation(self, latency_ms: float, tokens: dict[str, int], retries: int = 0) -> None:
        """Record metrics related to the LLM generation phase."""
        self.generation_time_ms = latency_ms
        self.token_usage = tokens
        self.retry_count = retries

    def record_error(self, error: Exception) -> None:
        """Record a generation failure."""
        self.is_failure = True
        self.error_type = type(error).__name__
        self.error_message = str(error)

    def finalize(self) -> GenerationMetadata:
        """Calculate total latency and build the final metadata object."""
        if self.end_time is None:
            self.end_time = time.perf_counter()
            
        total_latency_ms = (self.end_time - self.start_time) * 1000
        
        return GenerationMetadata(
            model_name=self.model_name,
            prompt_name=self.prompt_name,
            prompt_version=self.prompt_version,
            latency_ms=total_latency_ms,
            retrieval_time_ms=self.retrieval_time_ms,
            generation_time_ms=self.generation_time_ms,
            retry_count=self.retry_count,
            token_usage=self.token_usage,
            retrieved_document_count=len(self.retrieved_sources),
            retrieved_sources=self.retrieved_sources,
            correlation_id=self.correlation_id,
            error_type=self.error_type,
            error_message=self.error_message,
            is_failure=self.is_failure,
            source_attribution_scores=self.source_attribution_scores,
        )
