"""
NEXUS EDU — Deterministic LLM Core.

Provides strict, Pydantic-validated structured outputs and routed
content generation using Groq and Instructor.
"""

from app.ai.llm.content_generation import generate_content
from app.ai.llm.models import StrictBaseModel
from app.ai.llm.router import LLMTaskType
from app.ai.llm.structured_output import generate_structured_output

__all__ = [
    "generate_content",
    "generate_structured_output",
    "LLMTaskType",
    "StrictBaseModel",
]
