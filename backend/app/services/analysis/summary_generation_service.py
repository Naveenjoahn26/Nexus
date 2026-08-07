"""
NEXUS EDU — Summary Generation Service.

Generates structured, RAG-traceable content summaries.
Every KeyPoint carries source_chunk_ids for full auditability.
"""

from __future__ import annotations

import logging

from app.ai.llm.llm_service import LLMService
from app.ai.llm.router import LLMTaskType
from app.ai.prompts.summary_prompt import (
    SUMMARY_SYSTEM_PROMPT,
    build_summary_user_prompt,
)
from app.ai.rag.pipeline import RAGPipeline
from app.core.exceptions import InsufficientContextError, SummaryGenerationError
from app.schemas.summary import ContentSummary

logger = logging.getLogger(__name__)

_SERVICE_NAME = "SummaryGenerationService"
_MIN_CONTEXT_CHUNKS = 1


class SummaryGenerationService:
    """
    Generates validated content summaries with per-point RAG traceability.

    The summary schema requires source_chunk_ids on every KeyPoint,
    making each factual claim auditable and citation-safe.
    """

    def __init__(self, rag: RAGPipeline, llm: LLMService) -> None:
        self._rag = rag
        self._llm = llm

    async def generate(
        self,
        topic: str,
        course_id: str,
        course_name: str,
        summary_type: str = "document",
        difficulty_level: str = "intermediate",
        top_k: int = 12,
        use_parent: bool = False,
        additional_instructions: str = "",
    ) -> ContentSummary:
        """
        Generate a structured content summary.

        Args:
            topic: Topic or document title to summarize.
            course_id: Course identifier for RAG retrieval.
            course_name: Human-readable course name.
            summary_type: One of 'chapter', 'document', 'topic', 'multi_document'.
            difficulty_level: Target difficulty 'beginner', 'intermediate', or 'advanced'.
            top_k: Number of RAG chunks to retrieve (lower than other services —
                   summaries should be concise, not exhaustive).
            use_parent: Expand to parent chunks. Default False for summaries to
                        keep context focused on the most relevant passages.
            additional_instructions: Optional extra guidance.

        Returns:
            A validated ContentSummary instance.

        Raises:
            InsufficientContextError: Fewer chunks than minimum required.
            SummaryGenerationError: LLM generation failure.
        """
        logger.info(
            "[%s] Generating summary | topic=%s course_id=%s type=%s",
            _SERVICE_NAME, topic, course_id, summary_type,
        )

        chunks = await self._rag.retrieve(
            query=topic,
            course_id=course_id,
            top_k=top_k,
            use_parent=use_parent,
        )

        if len(chunks) < _MIN_CONTEXT_CHUNKS:
            raise InsufficientContextError(_SERVICE_NAME, course_id, _MIN_CONTEXT_CHUNKS)

        user_prompt = build_summary_user_prompt(
            topic=topic,
            course_name=course_name,
            context_chunks=chunks,
            summary_type=summary_type,
            difficulty_level=difficulty_level,
            additional_instructions=additional_instructions,
        )

        try:
            result: ContentSummary = await self._llm.generate(
                service_name=_SERVICE_NAME,
                operation="generate_summary",
                system_prompt=SUMMARY_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                response_model=ContentSummary,
                task_type=LLMTaskType.JSON_GENERATION,
                temperature=0.0,
            )
        except Exception as exc:
            raise SummaryGenerationError(str(exc)) from exc

        logger.info(
            "[%s] Summary generated | key_points=%d tags=%s",
            _SERVICE_NAME, len(result.key_points), result.tags,
        )
        return result
