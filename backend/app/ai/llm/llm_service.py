"""
NEXUS EDU — Centralized LLM Service.

The single gateway all generation services use to call the LLM.
No generation service ever imports instructor, groq, or tenacity directly.

Responsibilities:
  - Route requests through the AI Router.
  - Call structured_output or content_generation.
  - Capture and emit telemetry (latency, token usage, retry count).
  - Surface timing data on every call for latency logging.

Design: This is a stateless service class (no instance state).
Instantiate once at startup and inject into all generation services.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import TypeVar

from pydantic import BaseModel

from app.ai.llm.content_generation import generate_content
from app.ai.llm.router import LLMTaskType
from app.ai.llm.structured_output import StructuredGenerationError, generate_structured_output

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


@dataclass
class GenerationTelemetry:
    """
    Captures observability data for a single LLM generation call.

    Logged at INFO level after every generation. Stored in the response
    so API handlers can optionally surface it to monitoring systems.
    """

    service: str
    operation: str
    model: str
    latency_ms: float
    success: bool
    error_type: str | None = None
    extra: dict = field(default_factory=dict)


class LLMService:
    """
    Centralized LLM gateway for all NEXUS EDU generation services.

    Usage:
        llm = LLMService()
        result = await llm.generate(
            service_name="LectureGenerationService",
            operation="generate_lecture_notes",
            system_prompt=...,
            user_prompt=...,
            response_model=LectureNotes,
            task_type=LLMTaskType.JSON_GENERATION,
        )
    """

    async def generate(
        self,
        service_name: str,
        operation: str,
        system_prompt: str,
        user_prompt: str,
        response_model: type[T],
        task_type: LLMTaskType = LLMTaskType.JSON_GENERATION,
        temperature: float = 0.0,
    ) -> T:
        """
        Generate a validated structured output and emit telemetry.

        Args:
            service_name: Human-readable caller name for logging.
            operation: Specific operation name (e.g. 'generate_lecture_notes').
            system_prompt: LLM system instructions.
            user_prompt: LLM user message containing context and request.
            response_model: Pydantic class defining the expected output schema.
            task_type: AI Router task type determining model selection.
            temperature: Generation temperature (0.0 = deterministic).

        Returns:
            A validated instance of response_model.

        Raises:
            StructuredGenerationError: If generation fails after all retries.
        """
        from app.ai.llm.router import get_model_for_task
        model = get_model_for_task(task_type)

        logger.info(
            "[%s] Starting structured generation | operation=%s model=%s",
            service_name, operation, model,
        )

        start = time.perf_counter()
        telemetry = GenerationTelemetry(
            service=service_name,
            operation=operation,
            model=model,
            latency_ms=0.0,
            success=False,
        )

        try:
            result = await generate_structured_output(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                response_model=response_model,
                task_type=task_type,
                temperature=temperature,
            )
            telemetry.success = True
            telemetry.latency_ms = (time.perf_counter() - start) * 1000

            logger.info(
                "[%s] Generation complete | operation=%s latency_ms=%.1f",
                service_name, operation, telemetry.latency_ms,
            )
            return result

        except StructuredGenerationError as exc:
            telemetry.latency_ms = (time.perf_counter() - start) * 1000
            telemetry.error_type = type(exc).__name__
            logger.error(
                "[%s] Structured generation failed | operation=%s latency_ms=%.1f error=%s",
                service_name, operation, telemetry.latency_ms, str(exc),
            )
            raise

        except Exception as exc:
            telemetry.latency_ms = (time.perf_counter() - start) * 1000
            telemetry.error_type = type(exc).__name__
            logger.error(
                "[%s] Unexpected error | operation=%s latency_ms=%.1f error=%s",
                service_name, operation, telemetry.latency_ms, str(exc),
            )
            raise

    async def generate_text(
        self,
        service_name: str,
        operation: str,
        system_prompt: str,
        user_prompt: str,
        task_type: LLMTaskType = LLMTaskType.CONTENT_GENERATION,
        temperature: float = 0.7,
    ) -> str:
        """
        Generate unstructured text and emit telemetry.
        Used for streaming chat and any prose-only output.
        """
        from app.ai.llm.router import get_model_for_task
        model = get_model_for_task(task_type)

        logger.info(
            "[%s] Starting text generation | operation=%s model=%s",
            service_name, operation, model,
        )
        start = time.perf_counter()

        try:
            result = await generate_content(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                task_type=task_type,
                temperature=temperature,
            )
            latency_ms = (time.perf_counter() - start) * 1000
            logger.info(
                "[%s] Text generation complete | operation=%s latency_ms=%.1f chars=%d",
                service_name, operation, latency_ms, len(result),
            )
            return result

        except Exception as exc:
            latency_ms = (time.perf_counter() - start) * 1000
            logger.error(
                "[%s] Text generation failed | operation=%s latency_ms=%.1f error=%s",
                service_name, operation, latency_ms, str(exc),
            )
            raise
