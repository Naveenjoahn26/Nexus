"""
NEXUS EDU — Lecture Generation Service.

Orchestrates: RAG retrieval → prompt building → LLM generation → schema validation.
Contains ONLY business logic. All LLM mechanics go through LLMService.
"""

from __future__ import annotations

import logging

from app.ai.llm.llm_service import LLMService
from app.ai.llm.router import LLMTaskType
from app.ai.prompts.lecture_prompt import (
    LECTURE_SYSTEM_PROMPT,
    build_lecture_user_prompt,
)
from app.ai.rag.pipeline import RAGPipeline
from app.core.exceptions import InsufficientContextError, LectureGenerationError
from app.schemas.lecture_notes import LectureNotes

logger = logging.getLogger(__name__)

_SERVICE_NAME = "LectureGenerationService"
_MIN_CONTEXT_CHUNKS = 1


class LectureGenerationService:
    """
    Generates structured lecture notes grounded in RAG-retrieved course content.

    Pipeline:
        1. Retrieve context from RAG (hybrid dense+sparse+rerank)
        2. Build prompt with context injection
        3. Call LLMService → returns validated LectureNotes instance
        4. Return or raise domain exception
    """

    def __init__(self, rag: RAGPipeline, llm: LLMService) -> None:
        self._rag = rag
        self._llm = llm

    async def generate(
        self,
        topic: str,
        course_id: str,
        course_name: str,
        lecture_number: int | None = None,
        top_k: int = 15,
        use_parent: bool = True,
        additional_instructions: str = "",
    ) -> LectureNotes:
        """
        Generate lecture notes for a topic within a course.

        Args:
            topic: The lecture topic or title.
            course_id: The course identifier (ChromaDB collection key).
            course_name: Human-readable course name for the prompt.
            lecture_number: Optional sequential lecture number.
            top_k: Number of RAG chunks to retrieve.
            use_parent: Whether to expand child chunks to parent for richer context.
            additional_instructions: Optional extra generation guidance.

        Returns:
            A validated LectureNotes instance.

        Raises:
            InsufficientContextError: If the RAG pipeline returns fewer chunks than required.
            LectureGenerationError: If LLM generation fails after all retries.
        """
        logger.info(
            "[%s] Generating lecture | topic=%s course_id=%s",
            _SERVICE_NAME, topic, course_id,
        )

        # Step 1: Retrieve context
        chunks = await self._rag.retrieve(
            query=topic,
            course_id=course_id,
            top_k=top_k,
            use_parent=use_parent,
        )

        if len(chunks) < _MIN_CONTEXT_CHUNKS:
            raise InsufficientContextError(_SERVICE_NAME, course_id, _MIN_CONTEXT_CHUNKS)

        logger.debug("[%s] Retrieved %d chunks for topic='%s'", _SERVICE_NAME, len(chunks), topic)

        # Step 2: Build prompt
        user_prompt = build_lecture_user_prompt(
            topic=topic,
            course_name=course_name,
            context_chunks=chunks,
            lecture_number=lecture_number,
            additional_instructions=additional_instructions,
        )

        # Step 3: Generate + validate
        try:
            result: LectureNotes = await self._llm.generate(
                service_name=_SERVICE_NAME,
                operation="generate_lecture_notes",
                system_prompt=LECTURE_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                response_model=LectureNotes,
                task_type=LLMTaskType.JSON_GENERATION,
                temperature=0.0,
            )
        except Exception as exc:
            raise LectureGenerationError(str(exc)) from exc

        logger.info(
            "[%s] Lecture generated | sections=%d key_terms=%d",
            _SERVICE_NAME, len(result.sections), len(result.key_terms),
        )
        return result
