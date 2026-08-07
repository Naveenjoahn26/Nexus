"""
NEXUS EDU — Summary Schema.

Defines the strict Pydantic output schema for AI-generated content summaries.
Intentionally the strictest schema per field: every KeyPoint carries
source_chunk_ids for full RAG traceability, compression_ratio exposes
the ratio of summary to source length, and all text fields have both
minimum and maximum length bounds to prevent filler content.

Anti-hallucination: KeyPoint.source_chunk_ids links every factual point
back to a specific RAG chunk, making each claim auditable.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Literal

from pydantic import Field, field_validator, model_validator

from app.ai.llm.models import StrictBaseModel


# ── Key point ─────────────────────────────────────────────────────────────────


class KeyPoint(StrictBaseModel):
    """
    A single structured key point extracted from the source content.

    source_chunk_ids links every point to the specific RAG chunks it was
    derived from, enabling the UI to display citations and the backend to
    verify provenance. This is the primary anti-hallucination mechanism.
    """

    point_number: Annotated[
        int,
        Field(ge=1, description="1-indexed point number for ordering."),
    ]
    heading: Annotated[
        str,
        Field(
            min_length=3,
            max_length=80,
            description="A short, descriptive heading for this key point.",
        ),
    ]
    detail: Annotated[
        str,
        Field(
            min_length=30,
            max_length=300,
            description=(
                "A detailed explanation of this point. Must be self-contained "
                "and not reference 'the above' or other points by number."
            ),
        ),
    ]
    importance: Annotated[
        Literal["critical", "important", "supplementary"],
        Field(
            description=(
                "Relative importance of this point: "
                "'critical' = must know; "
                "'important' = should know; "
                "'supplementary' = nice to know."
            )
        ),
    ]
    source_chunk_ids: Annotated[
        list[str],
        Field(
            min_length=1,
            description=(
                "IDs of the specific RAG chunks this point was derived from. "
                "Every key point must be traceable to at least one source chunk."
            ),
        ),
    ]


# ── Metadata ─────────────────────────────────────────────────────────────────


class SummaryMetadata(StrictBaseModel):
    """Generation and source provenance metadata for the summary."""

    @field_validator("generated_at", mode="before")
    @classmethod
    def parse_generated_at(cls, v: object) -> object:
        """Accept ISO 8601 strings from the LLM and convert to datetime."""
        if isinstance(v, str):
            return datetime.fromisoformat(v.replace("Z", "+00:00"))
        return v

    generated_at: Annotated[
        datetime,
        Field(
            default_factory=lambda: datetime.now(timezone.utc),
            description="UTC timestamp when this summary was generated.",
        ),
    ]
    source_document_ids: Annotated[
        list[str],
        Field(
            min_length=1,
            description="IDs of the source documents this summary was derived from.",
        ),
    ]
    word_count: Annotated[
        int,
        Field(
            ge=50,
            description="Total word count of the generated summary content.",
        ),
    ]
    compression_ratio: Annotated[
        float,
        Field(
            ge=0.01,
            le=1.0,
            description=(
                "Ratio of summary word count to source word count (summary / source). "
                "Lower values = higher compression. Must be between 0.01 and 1.0."
            ),
        ),
    ]
    topics_covered: Annotated[
        list[str],
        Field(
            min_length=1,
            description="List of distinct topics represented in this summary.",
        ),
    ]


# ── Root model ───────────────────────────────────────────────────────────────


class ContentSummary(StrictBaseModel):
    """
    Complete AI-generated content summary.

    All AI generation for summaries must return this exact schema.
    The combination of bounded text fields and per-KeyPoint source traceability
    ensures outputs are concise, factual, and fully auditable.
    """

    title: Annotated[
        str,
        Field(
            min_length=5,
            max_length=200,
            description="Title of the summarized content.",
        ),
    ]
    summary_type: Annotated[
        Literal["chapter", "document", "topic", "multi_document"],
        Field(
            description=(
                "The scope of the summary: "
                "'chapter' = single chapter; "
                "'document' = entire document; "
                "'topic' = a specific topic across content; "
                "'multi_document' = synthesis across multiple documents."
            )
        ),
    ]
    executive_summary: Annotated[
        str,
        Field(
            min_length=80,
            max_length=400,
            description=(
                "A standalone TL;DR summary. Must convey the core idea without "
                "requiring the reader to consult the key_points list."
            ),
        ),
    ]
    key_points: Annotated[
        list[KeyPoint],
        Field(
            min_length=3,
            max_length=12,
            description="The most important points from the source content. Min 3, max 12.",
        ),
    ]
    concepts_introduced: Annotated[
        list[str],
        Field(
            min_length=1,
            max_length=20,
            description="New concepts, terms, or ideas introduced in the summarized content.",
        ),
    ]
    concepts_prerequisite: Annotated[
        list[str] | None,
        Field(
            default=None,
            max_length=10,
            description="Prior concepts the reader should understand. Omit if none needed.",
        ),
    ]
    difficulty_level: Annotated[
        Literal["beginner", "intermediate", "advanced"],
        Field(description="Assessed difficulty level of the summarized content."),
    ]
    estimated_read_time_minutes: Annotated[
        int,
        Field(
            ge=1,
            le=60,
            description=(
                "Estimated time to read the full source material in minutes. "
                "Based on ~200 words/minute average reading speed."
            ),
        ),
    ]
    tags: Annotated[
        list[str],
        Field(
            min_length=1,
            max_length=10,
            description=(
                "Searchable topic tags for this summary. Lowercase, hyphen-separated. "
                "Min 1, max 10."
            ),
        ),
    ]
    metadata: Annotated[
        SummaryMetadata,
        Field(description="Generation provenance and compression metadata."),
    ]

    @model_validator(mode="after")
    def validate_key_point_ordering(self) -> "ContentSummary":
        """Ensure key point numbers are sequential starting from 1."""
        numbers = [kp.point_number for kp in self.key_points]
        expected = list(range(1, len(self.key_points) + 1))
        if numbers != expected:
            raise ValueError(
                f"key_points must be numbered sequentially from 1. "
                f"Got: {numbers}, expected: {expected}."
            )
        return self

    @model_validator(mode="after")
    def validate_tags_format(self) -> "ContentSummary":
        """Enforce lowercase, non-empty tags."""
        for tag in self.tags:
            if tag != tag.lower():
                raise ValueError(f"Tag '{tag}' must be lowercase.")
            if not tag.strip():
                raise ValueError("Tags must not be empty or whitespace-only.")
        return self
