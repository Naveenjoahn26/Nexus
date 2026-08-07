"""
NEXUS EDU — Paper Analysis Service.

Generates a structured, schema-validated critical analysis of an academic paper.
The confidence_score field reflects RAG chunk coverage — exposing analysis
completeness to the UI rather than hiding uncertainty.
"""

from __future__ import annotations

import logging

from app.ai.llm.llm_service import LLMService
from app.ai.llm.router import LLMTaskType
from app.ai.prompts.analysis_prompt import (
    PAPER_ANALYSIS_SYSTEM_PROMPT,
    build_paper_analysis_user_prompt,
)
from app.ai.rag.pipeline import RAGPipeline
from app.core.exceptions import InsufficientContextError, PaperAnalysisError
from app.schemas.paper_analysis import PaperAnalysis

logger = logging.getLogger(__name__)

_SERVICE_NAME = "PaperAnalysisService"
_MIN_CONTEXT_CHUNKS = 1


class PaperAnalysisService:
    """
    Generates a validated critical analysis of an academic paper.

    Retrieves content from the paper's ingested chunks in ChromaDB,
    then produces a structured PaperAnalysis with bounded confidence scores,
    directy_quoted flags, and cross-referenced methodology blocks.
    """

    def __init__(self, rag: RAGPipeline, llm: LLMService) -> None:
        self._rag = rag
        self._llm = llm

    async def generate(
        self,
        paper_title: str,
        course_id: str,
        course_name: str,
        analysis_depth: str = "standard",
        top_k: int = 20,
        use_parent: bool = True,
        additional_instructions: str = "",
    ) -> PaperAnalysis:
        """
        Generate a critical analysis for an academic paper.

        Args:
            paper_title: Full title of the paper to analyze.
            course_id: Course identifier for RAG retrieval scope.
            course_name: Course context for the LLM.
            analysis_depth: 'surface', 'standard', or 'deep'.
            top_k: Number of chunks to retrieve. Higher for 'deep' analysis.
            use_parent: Expand to parent chunks for broader paper coverage.
            additional_instructions: Optional extra guidance.

        Returns:
            A validated PaperAnalysis instance.

        Raises:
            InsufficientContextError: Fewer chunks than minimum required.
            PaperAnalysisError: LLM generation failure.
        """
        logger.info(
            "[%s] Analyzing paper | title=%s course_id=%s depth=%s",
            _SERVICE_NAME, paper_title, course_id, analysis_depth,
        )

        # Use paper title as the retrieval query to maximize coverage.
        chunks = await self._rag.retrieve(
            query=paper_title,
            course_id=course_id,
            top_k=top_k,
            use_parent=use_parent,
        )

        if len(chunks) < _MIN_CONTEXT_CHUNKS:
            raise InsufficientContextError(_SERVICE_NAME, course_id, _MIN_CONTEXT_CHUNKS)

        user_prompt = build_paper_analysis_user_prompt(
            paper_title=paper_title,
            course_name=course_name,
            context_chunks=chunks,
            analysis_depth=analysis_depth,
            additional_instructions=additional_instructions,
        )

        try:
            result: PaperAnalysis = await self._llm.generate(
                service_name=_SERVICE_NAME,
                operation="generate_paper_analysis",
                system_prompt=PAPER_ANALYSIS_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                response_model=PaperAnalysis,
                task_type=LLMTaskType.JSON_GENERATION,
                temperature=0.0,
            )
        except Exception as exc:
            raise PaperAnalysisError(str(exc)) from exc

        logger.info(
            "[%s] Analysis complete | findings=%d quality=%s confidence=%.2f",
            _SERVICE_NAME,
            len(result.key_findings),
            result.critical_evaluation.overall_quality,
            result.metadata.confidence_score,
        )
        return result
