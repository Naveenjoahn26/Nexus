"""
NEXUS EDU — Structured Output Generation.

Provides the core engine for generating deterministic, strictly typed
JSON structures using Instructor and Pydantic.
"""

import logging
from typing import TypeVar

from pydantic import BaseModel
import tenacity

from app.core.config import get_settings
from app.ai.llm.client import get_instructor_client
from app.ai.llm.router import LLMTaskType, get_model_for_task
from app.core.exceptions import NexusBaseError

logger = logging.getLogger(__name__)

# Type variable for generic Pydantic return types
T = TypeVar("T", bound=BaseModel)

class StructuredGenerationError(NexusBaseError):
    """Raised when structured generation fails after all retries."""
    def __init__(self, message: str, original_error: Exception | None = None):
        super().__init__(message)
        self.original_error = original_error


async def generate_structured_output(
    system_prompt: str,
    user_prompt: str,
    response_model: type[T],
    task_type: LLMTaskType = LLMTaskType.JSON_GENERATION,
    temperature: float = 0.0,
) -> T:
    """
    Generate a deterministic, Pydantic-validated output from the LLM.

    Args:
        system_prompt: High-level instructions for the LLM.
        user_prompt: The specific data or request to process.
        response_model: A Pydantic class (inheriting from StrictBaseModel) 
                        that defines the exact required output schema.
        task_type: Determines which model to route to.
        temperature: Controls randomness (default 0.0 for max determinism).

    Returns:
        An instance of `response_model` populated with the LLM's output.

    Raises:
        StructuredGenerationError: If validation fails after all automatic retries.
    """
    settings = get_settings()
    client = get_instructor_client()
    model = get_model_for_task(task_type)
    
    logger.debug(
        "Requesting structured output for '%s' using model '%s' (max_retries=%d)",
        response_model.__name__,
        model,
        settings.llm_max_retries
    )

    try:
        # Instructor patches the create() call to accept `response_model` and `max_retries`.
        # If the generated JSON doesn't match the schema, Instructor catches the Pydantic
        # ValidationError, automatically appends the error to the chat history, and asks 
        # the model to fix it, repeating up to `max_retries` times.
        response = await client.chat.completions.create(
            model=model,
            response_model=response_model,
            max_retries=settings.llm_max_retries,
            temperature=temperature,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        
        logger.debug("Successfully generated structured output for '%s'", response_model.__name__)
        return response

    except tenacity.RetryError as e:
        # Tenacity wraps errors that exceed the max retry count.
        logger.error("Structured generation failed after maximum retries: %s", str(e))
        raise StructuredGenerationError(
            f"Failed to generate valid {response_model.__name__} after {settings.llm_max_retries} attempts.",
            original_error=e
        ) from e
        
    except Exception as e:
        logger.error("Unexpected error during structured generation: %s", str(e))
        raise StructuredGenerationError(f"Structured generation error: {str(e)}", original_error=e) from e
