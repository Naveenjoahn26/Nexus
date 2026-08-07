"""
NEXUS EDU — AI Task Router.

Maps distinct functional requirements to the optimal underlying LLM model.
"""

from enum import Enum
import logging

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class LLMTaskType(str, Enum):
    """
    Categorization of AI tasks to determine the optimal model routing.
    """
    METADATA_EXTRACTION = "metadata_extraction"
    JSON_GENERATION = "json_generation"
    CONTENT_GENERATION = "content_generation"


def get_model_for_task(task_type: LLMTaskType) -> str:
    """
    Route the task to the configured optimal Groq model.
    """
    settings = get_settings()
    
    if task_type == LLMTaskType.METADATA_EXTRACTION:
        model = settings.llm_model_metadata
    elif task_type == LLMTaskType.JSON_GENERATION:
        model = settings.llm_model_json
    elif task_type == LLMTaskType.CONTENT_GENERATION:
        model = settings.llm_model_content
    else:
        # Fallback to the most robust model if unknown task
        model = settings.llm_model_content
        logger.warning(
            "Unknown task type '%s', falling back to robust model '%s'",
            task_type,
            model
        )

    logger.debug("Routed task '%s' to model '%s'", task_type.value, model)
    return model
