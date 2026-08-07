"""
NEXUS EDU — Presentation Generation Service.

Generates structured slide decks grounded in course content.
The ContentBlock type-field alignment and slide_count validators
in the schema handle structural guarantees via Instructor retries.
"""

from __future__ import annotations

import logging

from app.ai.llm.llm_service import LLMService
from app.ai.llm.router import LLMTaskType
from app.ai.prompts.ppt_prompt import (
    PRESENTATION_SYSTEM_PROMPT,
    build_presentation_user_prompt,
)
from app.ai.rag.pipeline import RAGPipeline
from app.core.exceptions import InsufficientContextError, PresentationGenerationError
from app.schemas.presentation import Presentation

logger = logging.getLogger(__name__)

_SERVICE_NAME = "PresentationGenerationService"
_MIN_CONTEXT_CHUNKS = 1


class PresentationGenerationService:
    """
    Generates a fully structured presentation slide deck.

    Each slide is a schema-validated object with typed content blocks,
    enabling theme-independent frontend rendering.
    """

    def __init__(self, rag: RAGPipeline, llm: LLMService) -> None:
        self._rag = rag
        self._llm = llm

    async def generate(
        self,
        topic: str,
        course_id: str,
        course_name: str,
        num_slides: int = 8,
        audience_level: str = "undergraduate",
        theme: str = "academic",
        include_summary_slide: bool = True,
        top_k: int = 15,
        use_parent: bool = True,
        additional_instructions: str = "",
    ) -> Presentation:
        """
        Generate a presentation for a course topic.

        Args:
            topic: Presentation subject/title.
            course_id: Course identifier for RAG retrieval.
            course_name: Human-readable course name.
            num_slides: Target slide count (max 8).
            audience_level: Audience description (e.g. "undergraduate", "postgraduate").
            theme: Visual theme suggestion for the frontend.
            include_summary_slide: Whether to append a summary slide.
            top_k: Number of RAG chunks to retrieve.
            use_parent: Expand to parent chunks for broader context.
            additional_instructions: Optional generation guidance.

        Returns:
            A validated Presentation instance.

        Raises:
            InsufficientContextError: Fewer chunks than minimum required.
            PresentationGenerationError: LLM generation failure.
        """
        num_slides = min(num_slides, 8)
        effective_top_k = min(top_k, num_slides * 2)

        logger.info(
            "[%s] Generating presentation | topic=%s course_id=%s num_slides=%d top_k=%d",
            _SERVICE_NAME, topic, course_id, num_slides, effective_top_k
        )

        chunks = await self._rag.retrieve(
            query=topic,
            course_id=course_id,
            top_k=effective_top_k,
            use_parent=use_parent,
        )

        if len(chunks) < _MIN_CONTEXT_CHUNKS:
            raise InsufficientContextError(_SERVICE_NAME, course_id, _MIN_CONTEXT_CHUNKS)

        user_prompt = build_presentation_user_prompt(
            topic=topic,
            course_name=course_name,
            context_chunks=chunks,
            num_slides=num_slides,
            audience_level=audience_level,
            theme=theme,
            include_summary_slide=include_summary_slide,
            additional_instructions=additional_instructions,
        )

        try:
            result: Presentation = await self._llm.generate(
                service_name=_SERVICE_NAME,
                operation="generate_presentation",
                system_prompt=PRESENTATION_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                response_model=Presentation,
                task_type=LLMTaskType.JSON_GENERATION,
                temperature=0.0,
            )
        except Exception as exc:
            raise PresentationGenerationError(str(exc)) from exc

        logger.info(
            "[%s] Presentation generated | slides=%d theme=%s",
            _SERVICE_NAME, result.slide_count, result.theme_suggestion,
        )
        return result
