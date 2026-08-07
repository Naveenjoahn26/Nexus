"""
NEXUS EDU — LLM Structured Models.

Provides the base Pydantic models for structured output generation.
By inheriting from StrictBaseModel, we ensure the LLM strictly
adheres to the defined schema without hallucinating extra fields.
"""

from pydantic import BaseModel, ConfigDict


class StrictBaseModel(BaseModel):
    """
    Base model for all LLM structured outputs.
    
    extra='forbid' ensures that if the LLM generates hallucinated keys
    not present in the schema, Pydantic will raise a ValidationError,
    triggering Instructor's automatic retry mechanism.
    """
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
    )
