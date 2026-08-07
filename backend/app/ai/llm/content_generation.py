"""
NEXUS EDU — Unstructured Content Generation.

Provides standard text generation via the underlying Groq client.
To be used only when explicit JSON structures are not required
(e.g., streaming a chat response or writing a prose summary).
"""

import logging

from app.ai.llm.client import get_standard_client
from app.ai.llm.router import LLMTaskType, get_model_for_task
from app.core.exceptions import NexusBaseError

logger = logging.getLogger(__name__)


class ContentGenerationError(NexusBaseError):
    """Raised when text generation fails."""
    pass


async def generate_content(
    system_prompt: str,
    user_prompt: str,
    task_type: LLMTaskType = LLMTaskType.CONTENT_GENERATION,
    temperature: float = 0.7,
) -> str:
    """
    Generate unstructured text content from the LLM.

    Args:
        system_prompt: High-level instructions for the LLM.
        user_prompt: The specific query or request.
        task_type: Determines which model to route to (default CONTENT_GENERATION).
        temperature: Controls randomness (default 0.7 for prose).

    Returns:
        The generated text string.

    Raises:
        ContentGenerationError: If the API call fails.
    """
    client = get_standard_client()
    model = get_model_for_task(task_type)
    
    logger.debug(
        "Requesting content generation using model '%s' (temp=%.1f)",
        model,
        temperature
    )

    try:
        response = await client.chat.completions.create(
            model=model,
            temperature=temperature,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        
        content = response.choices[0].message.content
        if content is None:
             raise ContentGenerationError("LLM returned an empty response.")
             
        logger.debug("Successfully generated content (%d chars)", len(content))
        return content

    except Exception as e:
        logger.error("Content generation failed: %s", str(e))
        raise ContentGenerationError(f"Content generation error: {str(e)}") from e
