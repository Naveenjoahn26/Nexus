"""
NEXUS EDU — Presentation (Slide Deck) Schema.

Defines the strict Pydantic output schema for AI-generated presentations.
Each slide is a fully structured object — not markdown prose — so the
frontend can render titles, bullets, speaker notes, and tables independently,
apply themes, and support animations without any string parsing.

Cross-field validator: len(slides) must equal slide_count.
ContentBlock validator: exactly the fields matching block_type must be populated.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Literal

from pydantic import Field, field_validator, model_validator

from app.ai.llm.models import StrictBaseModel


# ── Table data ────────────────────────────────────────────────────────────────


class TableData(StrictBaseModel):
    """Structured table content for use inside a slide content block."""

    headers: Annotated[
        list[str],
        Field(
            min_length=2,
            max_length=8,
            description="Column header labels. Min 2, max 8 columns.",
        ),
    ]
    rows: Annotated[
        list[list[str]],
        Field(
            min_length=1,
            max_length=10,
            description=(
                "Table row data. Each row must have the same number of cells as headers. "
                "Min 1 row, max 10 rows."
            ),
        ),
    ]

    @model_validator(mode="after")
    def validate_row_widths(self) -> "TableData":
        """Every row must have exactly as many cells as there are headers."""
        expected = len(self.headers)
        for i, row in enumerate(self.rows):
            if len(row) != expected:
                raise ValueError(
                    f"Row {i + 1} has {len(row)} cells but table has {expected} headers."
                )
        return self


# ── Content block ─────────────────────────────────────────────────────────────


class ContentBlock(StrictBaseModel):
    """
    A single atomic content unit within a slide.

    Each ContentBlock has a block_type that declares which content field
    is active. The cross-field validator enforces that exactly the relevant
    field is populated and all others are null.
    """

    block_type: Annotated[
        Literal["bullet_points", "paragraph", "table", "code_snippet", "quote", "key_concept"],
        Field(description="The type of content in this block. Determines which field is populated."),
    ]
    heading: Annotated[
        str | None,
        Field(
            default=None,
            max_length=100,
            description="Optional sub-heading for this content block.",
        ),
    ]
    # Populated only when block_type = "bullet_points"
    bullets: Annotated[
        list[str] | None,
        Field(
            default=None,
            max_length=6,
            description=(
                "Bullet point list. Max 6 items. "
                "Each item max 120 characters for slide readability."
            ),
        ),
    ]
    # Populated only when block_type = "paragraph"
    paragraph: Annotated[
        str | None,
        Field(
            default=None,
            max_length=400,
            description="Prose paragraph. Max 400 characters to maintain slide brevity.",
        ),
    ]
    # Populated only when block_type = "table"
    table_data: Annotated[
        TableData | None,
        Field(
            default=None,
            description="Structured table data. Required when block_type is 'table'.",
        ),
    ]
    # Populated only when block_type = "code_snippet"
    code: Annotated[
        str | None,
        Field(
            default=None,
            max_length=800,
            description="Code snippet. Max 800 characters. Include language in the heading.",
        ),
    ]
    # Populated only when block_type = "quote" or "key_concept"
    quote_text: Annotated[
        str | None,
        Field(
            default=None,
            max_length=300,
            description="Quote or key concept text. Max 300 characters.",
        ),
    ]

    @model_validator(mode="after")
    def validate_type_field_alignment(self) -> "ContentBlock":
        """
        Enforce that exactly the field corresponding to block_type is populated.
        All other content fields must be null.
        """
        type_field_map = {
            "bullet_points": "bullets",
            "paragraph": "paragraph",
            "table": "table_data",
            "code_snippet": "code",
            "quote": "quote_text",
            "key_concept": "quote_text",
        }
        expected_field = type_field_map[self.block_type]
        all_content_fields = {"bullets", "paragraph", "table_data", "code", "quote_text"}

        # The expected field must be populated.
        if getattr(self, expected_field) is None:
            raise ValueError(
                f"ContentBlock with block_type='{self.block_type}' "
                f"must have '{expected_field}' populated."
            )
        # All other content fields must be null.
        for field_name in all_content_fields - {expected_field}:
            if getattr(self, field_name) is not None:
                raise ValueError(
                    f"ContentBlock with block_type='{self.block_type}' "
                    f"must have '{field_name}' set to null."
                )
        return self


# ── Slide ─────────────────────────────────────────────────────────────────────


class Slide(StrictBaseModel):
    """A single presentation slide with structured content and speaker notes."""

    slide_number: Annotated[
        int,
        Field(ge=1, description="1-indexed slide number for ordering."),
    ]
    slide_type: Annotated[
        Literal["title", "content", "image_placeholder", "summary", "quote", "table", "divider"],
        Field(description="The functional type of this slide, used by the renderer to apply layout."),
    ]
    title: Annotated[
        str,
        Field(
            min_length=2,
            max_length=80,
            description="Slide title. Max 80 characters for readability.",
        ),
    ]
    content_blocks: Annotated[
        list[ContentBlock] | None,
        Field(
            default=None,
            max_length=4,
            description=(
                "The content blocks on this slide. Max 4 blocks per slide. "
                "Null for 'divider' slides."
            ),
        ),
    ]
    speaker_notes: Annotated[
        str,
        Field(
            min_length=20,
            max_length=500,
            description=(
                "Detailed speaker notes for this slide. "
                "Must provide enough context for the presenter to speak without reading slides."
            ),
        ),
    ]
    layout_hint: Annotated[
        Literal["full_text", "two_column", "title_only", "bullets_right"],
        Field(description="Frontend layout hint for rendering this slide."),
    ]

    @model_validator(mode="after")
    def validate_divider_has_no_content(self) -> "Slide":
        if self.slide_type == "divider" and self.content_blocks is not None:
            raise ValueError("'divider' slides must have content_blocks set to null.")
        if self.slide_type != "divider" and not self.content_blocks:
            raise ValueError(
                f"Slide type '{self.slide_type}' requires at least one content_block."
            )
        return self


# ── Metadata ─────────────────────────────────────────────────────────────────


class PresentationMetadata(StrictBaseModel):
    """Generation and source provenance metadata for the presentation."""

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
            description="UTC timestamp when this presentation was generated.",
        ),
    ]
    source_document_ids: Annotated[
        list[str],
        Field(
            min_length=1,
            description="IDs of the RAG-retrieved source documents used for generation.",
        ),
    ]
    estimated_duration_minutes: Annotated[
        int,
        Field(
            ge=3,
            le=120,
            description="Estimated presentation duration in minutes based on slide count and content.",
        ),
    ]
    topics_covered: Annotated[
        list[str],
        Field(
            min_length=1,
            description="List of distinct topics covered across all slides.",
        ),
    ]


# ── Root model ───────────────────────────────────────────────────────────────


class Presentation(StrictBaseModel):
    """
    Complete AI-generated slide deck.

    All AI generation for presentations must return this exact schema.
    Each slide is a fully structured object enabling theme-independent
    frontend rendering without any prose parsing.
    """

    title: Annotated[
        str,
        Field(min_length=5, max_length=200, description="Full title of the presentation."),
    ]
    subtitle: Annotated[
        str | None,
        Field(default=None, max_length=200, description="Optional subtitle shown on the title slide."),
    ]
    course_name: Annotated[
        str,
        Field(min_length=3, max_length=150, description="Name of the course."),
    ]
    author: Annotated[
        str | None,
        Field(default=None, max_length=100, description="Optional presenter or author name."),
    ]
    slide_count: Annotated[
        int,
        Field(
            ge=3,
            le=60,
            description="Declared total number of slides. Must match len(slides).",
        ),
    ]
    slides: Annotated[
        list[Slide],
        Field(min_length=3, description="All slides in order."),
    ]
    theme_suggestion: Annotated[
        Literal["academic", "minimal", "dark", "colorful"],
        Field(description="Suggested visual theme for the frontend renderer."),
    ]
    metadata: Annotated[
        PresentationMetadata,
        Field(description="Generation provenance and quality metadata."),
    ]

    @model_validator(mode="after")
    def validate_slide_count_matches(self) -> "Presentation":
        """slide_count declaration must exactly match the actual number of slides."""
        if len(self.slides) != self.slide_count:
            raise ValueError(
                f"slide_count={self.slide_count} but {len(self.slides)} slides were generated. "
                "These must match exactly."
            )
        numbers = [s.slide_number for s in self.slides]
        expected = list(range(1, self.slide_count + 1))
        if numbers != expected:
            raise ValueError(
                f"slide_number values must be sequential from 1 to {self.slide_count}. "
                f"Got: {numbers}."
            )
        return self
