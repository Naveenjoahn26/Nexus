"""
NEXUS EDU — Chat Generation Service.

Orchestrates RAG retrieval and unstructured chat generation.
"""

from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel, Field

from app.ai.llm.llm_service import LLMService
from app.ai.llm.router import LLMTaskType
from app.ai.rag.pipeline import RAGPipeline
from app.core.exceptions import InsufficientContextError

logger = logging.getLogger(__name__)

_SERVICE_NAME = "ChatGenerationService"


class ChatResponseData(BaseModel):
    """Internal model for orchestrator serialization."""
    content: str
    source_document_ids: list[str] = Field(default_factory=list)


class ChatGenerationService:
    def __init__(self, rag: RAGPipeline, llm: LLMService) -> None:
        self._rag = rag
        self._llm = llm

    async def generate(
        self,
        topic: str,
        course_id: str,
        conversation_id: str | None = None,
        top_k: int = 5,
        use_parent: bool = True,
        **kwargs: Any,
    ) -> ChatResponseData:
        """Generate a chat response based on RAG context."""
        logger.info("[%s] Generating chat | topic='%s' course_id=%s", _SERVICE_NAME, topic, course_id)

        # Retrieve context
        chunks = await self._rag.retrieve(
            query=topic,
            course_id=course_id,
            top_k=top_k,
            use_parent=use_parent,
        )
        
        # Build prompt
        system_prompt = "You are a helpful teaching assistant for a university course. Use the provided context to answer the student's question."
        
        context_text = "\n\n".join(
            f"--- Source: {c.metadata.get('filename', 'Unknown')} ---\n{c.content}"
            for c in chunks
        )
        
        user_prompt = f"Context:\n{context_text}\n\nStudent Question:\n{topic}"
        
        # Generate text
        content = await self._llm.generate_text(
            service_name=_SERVICE_NAME,
            operation="chat_generation",
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            task_type=LLMTaskType.CONTENT_GENERATION,
            temperature=0.7,
        )
        
        source_ids = list(set([c.metadata.get("document_id") for c in chunks if c.metadata.get("document_id")]))
        
        return ChatResponseData(
            content=content,
            source_document_ids=source_ids,
        )
