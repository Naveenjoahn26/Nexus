"""
NEXUS EDU — Lecture Notes Schema.

Defines the strict Pydantic output schema for AI-generated lecture notes.
Enforces hierarchical document structure (section → subsection → content)
so the frontend can render a structured outline, not parse prose.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated

from pydantic import AnyHttpUrl, Field, field_validator, model_validator

from app.ai.llm.models import StrictBaseModel


# ── Leaf nodes ───────────────────────────────────────────────────────────────


class Reference(StrictBaseModel):
    """A bibliographic reference for further reading."""

    title: Annotated[
        str,
        Field(min_length=5, max_length=300, description="Full title of the reference."),
    ]
    authors: Annotated[
        list[str] | None,
        Field(
            default=None,
            description="List of author names. Omit if unknown.",
        ),
    ]
    year: Annotated[
        int | None,
        Field(
            default=None,
            ge=1900,
            le=2030,
            description="Year of publication. Omit if unknown.",
        ),
    ]
    url: Annotated[
        AnyHttpUrl | None,
        Field(
            default=None,
            description="Verified URL to the reference. Must be a valid HTTP/HTTPS URL.",
        ),
    ]


class KeyTerm(StrictBaseModel):
    """A defined key term or concept introduced in this lecture."""

    term: Annotated[
        str,
        Field(
            min_length=2,
            max_length=100,
            description="The key term, concept, or technical vocabulary word.",
        ),
    ]
    definition: Annotated[
        str,
        Field(
            min_length=20,
            max_length=300,
            description="A clear, concise definition appropriate for the target audience.",
        ),
    ]
    related_terms: Annotated[
        list[str] | None,
        Field(
            default=None,
            max_length=5,
            description="Other terms that are closely related to this concept. Max 5.",
        ),
    ]


# ── Section hierarchy ─────────────────────────────────────────────────────────


class LectureSubsection(StrictBaseModel):
    """A subsection nested within a primary lecture section."""

    heading: Annotated[
        str,
        Field(
            min_length=3,
            max_length=150,
            description="The subsection heading.",
        ),
    ]
    content: Annotated[
        str,
        Field(
            min_length=30,
            max_length=3000,
            description="The full prose content of this subsection.",
        ),
    ]
    bullet_points: Annotated[
        list[str] | None,
        Field(
            default=None,
            max_length=10,
            description=(
                "Optional summary bullet points. Max 10 items. "
                "Each bullet should be self-contained (max ~120 chars)."
            ),
        ),
    ]

    @field_validator("bullet_points")
    @classmethod
    def validate_bullet_length(cls, v: list[str] | None) -> list[str] | None:
        if v is not None:
            for i, bullet in enumerate(v):
                if len(bullet) > 200:
                    raise ValueError(
                        f"Bullet point {i + 1} exceeds 200 characters ({len(bullet)} chars). "
                        "Keep bullets concise."
                    )
        return v


class LectureSection(StrictBaseModel):
    """A primary section of the lecture (top-level heading)."""

    section_number: Annotated[
        int,
        Field(ge=1, description="1-indexed section number for ordering."),
    ]
    heading: Annotated[
        str,
        Field(
            min_length=3,
            max_length=150,
            description="The section heading text.",
        ),
    ]
    content: Annotated[
        str,
        Field(
            min_length=50,
            max_length=5000,
            description="The primary prose content of this section.",
        ),
    ]
    subsections: Annotated[
        list[LectureSubsection] | None,
        Field(
            default=None,
            max_length=10,
            description="Optional nested subsections. Max 10 per section.",
        ),
    ]
    key_takeaway: Annotated[
        str,
        Field(
            min_length=20,
            max_length=300,
            description=(
                "A single sentence summarizing the most important concept in this section. "
                "Must be self-contained and actionable."
            ),
        ),
    ]
    examples: Annotated[
        list[str] | None,
        Field(
            default=None,
            max_length=5,
            description="Optional concrete examples illustrating the section content. Max 5.",
        ),
    ]


# ── Metadata ─────────────────────────────────────────────────────────────────


class NotesMetadata(StrictBaseModel):
    """Generation and source provenance metadata for the lecture notes."""

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
            description="UTC timestamp when these notes were generated.",
        ),
    ]
    source_document_ids: Annotated[
        list[str],
        Field(
            min_length=1,
            description="IDs of the RAG-retrieved source documents used for generation.",
        ),
    ]
    word_count: Annotated[
        int,
        Field(
            ge=100,
            description="Total word count of all generated content (excluding metadata).",
        ),
    ]
    topics_covered: Annotated[
        list[str],
        Field(
            min_length=1,
            description="List of distinct academic topics covered in these notes.",
        ),
    ]


# ── Root model ───────────────────────────────────────────────────────────────


class LectureNotes(StrictBaseModel):
    """
    Complete AI-generated lecture notes.

    All AI generation for lecture notes must return this exact schema.
    The hierarchical section structure enables frontend outline rendering
    without any prose parsing.
    """

    title: Annotated[
        str,
        Field(
            min_length=5,
            max_length=200,
            description="Full title of the lecture.",
        ),
    ]
    course_name: Annotated[
        str,
        Field(min_length=3, max_length=150, description="Name of the course."),
    ]
    lecture_number: Annotated[
        int | None,
        Field(
            default=None,
            ge=1,
            description="Sequential lecture number within the course. Omit if not applicable.",
        ),
    ]
    learning_objectives: Annotated[
        list[str],
        Field(
            min_length=2,
            max_length=8,
            description=(
                "Clear, measurable learning objectives. "
                "Use 'By the end of this lecture, students will be able to...' format. "
                "Min 2, max 8."
            ),
        ),
    ]
    sections: Annotated[
        list[LectureSection],
        Field(
            min_length=1,
            max_length=20,
            description="All primary sections of the lecture notes in order.",
        ),
    ]
    key_terms: Annotated[
        list[KeyTerm],
        Field(
            min_length=1,
            description="All key terms and concepts introduced in this lecture.",
        ),
    ]
    summary: Annotated[
        str,
        Field(
            min_length=100,
            max_length=500,
            description=(
                "A comprehensive summary of the entire lecture suitable for revision. "
                "Must stand alone without referencing section numbers."
            ),
        ),
    ]
    further_reading: Annotated[
        list[Reference] | None,
        Field(
            default=None,
            max_length=10,
            description="Optional list of references for deeper study. Max 10.",
        ),
    ]
    metadata: Annotated[
        NotesMetadata,
        Field(description="Generation provenance and quality metadata."),
    ]

    @model_validator(mode="after")
    def validate_section_ordering(self) -> "LectureNotes":
        """Ensure section_numbers are sequential starting from 1."""
        numbers = [s.section_number for s in self.sections]
        expected = list(range(1, len(self.sections) + 1))
        if numbers != expected:
            raise ValueError(
                f"Section numbers must be sequential starting from 1. "
                f"Got: {numbers}, expected: {expected}."
            )
        return self
