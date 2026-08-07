"""
NEXUS EDU — AI Orchestrator.

The central nervous system for all AI generation requests.
Enforces the boundary between API routes and backend AI services.

Responsibilities:
- Manage the Conversation lifecycle (load, save, soft delete).
- Route requests to the appropriate AI Generation Service via a Plugin Registry.
- Persist User Prompts, AI Responses, and Observability Metadata to PostgreSQL.
- Emit structured logs for monitoring.
"""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any, Callable, Coroutine

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import telemetry_logger
from app.models.course import Course
from app.repositories.conversation_repository import ConversationRepository
from app.schemas.metadata import GenerationMetadata
from app.ai.observability import AIObservabilityTracker

# We use standard logger for internal debug/errors, and telemetry_logger for observability.
logger = logging.getLogger(__name__)

# Type alias for a generation service function
GenerationCallable = Callable[..., Coroutine[Any, Any, Any]]


class AIOrchestrator:
    """
    Centralized coordinator for AI requests.
    Uses a plugin registry pattern so new services can be added without modifying this class.
    """

    def __init__(self, db_session: AsyncSession) -> None:
        self.db = db_session
        self.repo = ConversationRepository(db_session)
        
        # Plugin Registry: Maps action_type to the actual async service function.
        # e.g., "generate_lecture" -> LectureGenerationService.generate
        self._registry: dict[str, tuple[GenerationCallable, str]] = {}

    def register_service(self, action_type: str, handler: GenerationCallable, prompt_name: str) -> None:
        """
        Register a new AI service feature (Plugin architecture).
        
        Args:
            action_type: The action key used by the frontend (e.g., 'generate_lecture').
            handler: The async function to execute.
            prompt_name: Logical name for metadata telemetry.
        """
        self._registry[action_type] = (handler, prompt_name)
        logger.debug("Registered AI service: %s -> %s", action_type, handler.__qualname__)

    async def execute(
        self,
        user_id: uuid.UUID,
        course_id: uuid.UUID,
        action_type: str,
        conversation_id: uuid.UUID | None = None,
        conversation_title: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Execute an AI request through the orchestration pipeline.
        
        Pipeline:
            1. Resolve Conversation (create if None).
            2. Save User Prompt.
            3. Lookup Generation Service.
            4. Execute (RAG + LLM).
            5. Capture Metadata and Save AI Response.
        
        Args:
            user_id: The requesting user.
            course_id: The active course scope.
            action_type: The registered service to invoke.
            conversation_id: Optional ID to continue an existing thread.
            conversation_title: Optional title for a new thread.
            **kwargs: Payload arguments passed directly to the generation service.
            
        Returns:
            A dictionary containing the 'conversation_id', 'message_id', and 'data' (the Pydantic schema dict).
        """
        # --- 1. Lookup Service ---
        if action_type not in self._registry:
            telemetry_logger.error(
                "Service not found",
                extra={"user_id": user_id, "event": "Validation Failed", "action": action_type}
            )
            raise ValueError(f"Unknown action_type: {action_type}")
            
        handler, prompt_name = self._registry[action_type]

        # Initialize Observability Tracker
        tracker = AIObservabilityTracker(
            model_name=prompt_name,
            prompt_name=prompt_name,
        )
        req_id = tracker.correlation_id

        # --- 2. Manage Conversation ---
        conv = None
        if conversation_id:
            conv = await self.repo.get_conversation(conversation_id)
            # If the user provided a dummy UUID (like Swagger's default) or one they don't own,
            # gracefully fall back to creating a new conversation instead of throwing an error.
            if conv and conv.user_id != user_id:
                conv = None
                
        if not conv:
            title = conversation_title or f"New {action_type.replace('_', ' ').title()}"
            conv = await self.repo.create_conversation(user_id, course_id, title)
            conversation_id = conv.id

        # --- 3. Look up Course Name ---
        course_result = await self.db.execute(
            select(Course).where(Course.id == course_id)
        )
        course = course_result.scalar_one_or_none()
        course_name = course.name if course else "Unknown Course"

        # --- 4. Save User Prompt ---
        # Reconstruct a generic prompt summary from kwargs for the DB
        user_prompt_text = kwargs.get("topic", kwargs.get("paper_title", "Unknown Request"))
        user_msg = await self.repo.add_message(
            conversation_id=conversation_id,
            role="user",
            content=f"{action_type}: {user_prompt_text}",
        )

        telemetry_logger.info(
            "Request Started",
            extra={
                "conversation_id": str(conversation_id),
                "correlation_id": tracker.correlation_id,
                "request_id": req_id,
                "user_id": str(user_id),
                "event": "Request Started",
                "action": action_type,
            }
        )

        # --- 5. Execute Service ---
        try:
            # Inject course_name into kwargs for all generation services
            service_kwargs = dict(kwargs)
            service_kwargs["course_name"] = course_name

            # PaperAnalysisService expects 'paper_title' instead of 'topic'
            if action_type == "generate_paper_analysis" and "topic" in service_kwargs:
                service_kwargs["paper_title"] = service_kwargs.pop("topic")

            # Filter kwargs to only include parameters the handler actually accepts.
            # This prevents TypeErrors from extra kwargs (e.g. target_audience)
            # that the routers send but the services don't define.
            import inspect
            sig = inspect.signature(handler)
            accepted_params = set(sig.parameters.keys())
            has_var_keyword = any(
                p.kind == inspect.Parameter.VAR_KEYWORD
                for p in sig.parameters.values()
            )
            if not has_var_keyword:
                service_kwargs = {
                    k: v for k, v in service_kwargs.items() if k in accepted_params
                }

            # The generation service handles RAG + LLM internally
            result = await handler(
                course_id=str(course_id),
                **service_kwargs
            )
        except Exception as e:
            tracker.record_error(e)
            metadata = tracker.finalize()
            telemetry_logger.error(
                "Generation Failed",
                extra={
                    "conversation_id": str(conversation_id),
                    "correlation_id": tracker.correlation_id,
                    "request_id": req_id,
                    "user_id": str(user_id),
                    "event": "Failure",
                    "action": action_type,
                    "latency_ms": metadata.latency_ms,
                    "error": metadata.error_message,
                    "error_type": metadata.error_type,
                    "is_failure": metadata.is_failure,
                }
            )
            raise

        # --- 5. Extract Metadata & Save AI Response ---
        # The result is a Pydantic model (LectureNotes, Presentation, etc.)
        structured_data = result.model_dump(mode="json")
        
        retrieved_sources = structured_data.get("source_document_ids", [])
        
        # Update tracker
        tracker.record_retrieval(latency_ms=0.0, sources=retrieved_sources)
        tracker.record_generation(latency_ms=0.0, tokens={})  # Hidden inside service
        
        # Build observability metadata
        metadata = tracker.finalize()

        ai_msg = await self.repo.add_message(
            conversation_id=conversation_id,
            role="assistant",
            structured_response=structured_data,
            generation_metadata=metadata.model_dump(mode="json"),
        )
        
        # Commit the transaction (if everything succeeded)
        await self.db.commit()

        telemetry_logger.info(
            "Generation Success",
            extra={
                "conversation_id": str(conversation_id),
                "correlation_id": tracker.correlation_id,
                "request_id": req_id,
                "user_id": str(user_id),
                "event": "Success",
                "action": action_type,
                "latency_ms": metadata.latency_ms,
                "model": metadata.model_name,
                "prompt_version": metadata.prompt_version,
            }
        )

        return {
            "conversation_id": str(conversation_id),
            "message_id": str(ai_msg.id),
            "data": structured_data,
        }
