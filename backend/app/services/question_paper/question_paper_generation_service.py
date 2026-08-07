"""
NEXUS EDU — Question Paper Generation Service.

Orchestrates: RAG retrieval → prompt building → LLM generation → schema validation.
The most constraint-heavy service: marks must balance across sections,
MCQ options must be exact. Instructor retries handle any validator failures.
"""

from __future__ import annotations

import logging

from app.ai.llm.llm_service import LLMService
from app.ai.llm.router import LLMTaskType
from app.ai.prompts.paper_prompt import (
    QUESTION_PAPER_SYSTEM_PROMPT,
    build_question_paper_user_prompt,
)
from app.ai.rag.pipeline import RAGPipeline
from app.core.exceptions import InsufficientContextError, QuestionPaperGenerationError
from app.schemas.question_paper import QuestionPaper

logger = logging.getLogger(__name__)

_SERVICE_NAME = "QuestionPaperGenerationService"
_MIN_CONTEXT_CHUNKS = 1  # Minimum guard - let the LLM work with what it has


class QuestionPaperGenerationService:
    """
    Generates a structured, schema-validated question paper grounded in course content.

    Uses a higher minimum chunk count than other services because a balanced
    exam needs broad coverage across the syllabus.
    """

    def __init__(self, rag: RAGPipeline, llm: LLMService) -> None:
        self._rag = rag
        self._llm = llm

    async def generate(
        self,
        topic: str,
        course_id: str,
        course_name: str,
        total_marks: int = 100,
        exam_duration_minutes: int = 180,
        num_sections: int = 3,
        difficulty_mix: str = "30% easy, 50% medium, 20% hard",
        bloom_focus: str = "remember, understand, apply, analyze",
        top_k: int = 20,
        use_parent: bool = True,
        additional_instructions: str = "",
    ) -> QuestionPaper:
        """
        Generate a complete examination paper.

        Args:
            topic: Syllabus topic or coverage description.
            course_id: Course identifier for RAG retrieval.
            course_name: Human-readable course name.
            total_marks: Total marks for the paper (validated against section sums).
            exam_duration_minutes: Duration in minutes (30–360).
            num_sections: Number of sections (e.g. 3 for A/B/C).
            difficulty_mix: Natural language description of difficulty distribution.
            bloom_focus: Bloom's taxonomy levels to target.
            top_k: Number of RAG chunks to retrieve.
            use_parent: Expand to parent chunks for richer coverage.
            additional_instructions: Optional generation guidance.

        Returns:
            A validated QuestionPaper instance.

        Raises:
            InsufficientContextError: Fewer chunks than minimum required.
            QuestionPaperGenerationError: LLM generation failure.
        """
        logger.info(
            "[%s] Generating paper | topic=%s course_id=%s total_marks=%d",
            _SERVICE_NAME, topic, course_id, total_marks,
        )

        chunks = await self._rag.retrieve(
            query=topic,
            course_id=course_id,
            top_k=top_k,
            use_parent=use_parent,
        )

        if len(chunks) < _MIN_CONTEXT_CHUNKS:
            raise InsufficientContextError(_SERVICE_NAME, course_id, _MIN_CONTEXT_CHUNKS)

        user_prompt = build_question_paper_user_prompt(
            topic=topic,
            course_name=course_name,
            context_chunks=chunks,
            total_marks=total_marks,
            exam_duration_minutes=exam_duration_minutes,
            num_sections=num_sections,
            difficulty_mix=difficulty_mix,
            bloom_focus=bloom_focus,
            additional_instructions=additional_instructions,
        )

        try:
            result: QuestionPaper = await self._llm.generate(
                service_name=_SERVICE_NAME,
                operation="generate_question_paper",
                system_prompt=QUESTION_PAPER_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                response_model=QuestionPaper,
                task_type=LLMTaskType.JSON_GENERATION,
                temperature=0.0,
            )
        except Exception as exc:
            raise QuestionPaperGenerationError(str(exc)) from exc

        total_questions = sum(len(s.questions) for s in result.sections)
        logger.info(
            "[%s] Paper generated | sections=%d total_questions=%d total_marks=%d",
            _SERVICE_NAME, len(result.sections), total_questions, result.total_marks,
        )
        return result
