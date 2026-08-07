"""
NEXUS EDU — Question Paper Schema.

Defines the strict Pydantic output schema for AI-generated question papers.
Every field is validated — the LLM cannot return plain text or malformed JSON.
Cross-field validators enforce business rules the LLM must obey:
  - Total marks must equal sum of all section marks.
  - MCQ questions must have exactly 4 options and exactly 1 correct answer.
  - Question numbers must be unique within their section.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Literal

from pydantic import Field, field_validator, model_validator

from app.ai.llm.models import StrictBaseModel


# ── Leaf nodes (deepest schema components) ───────────────────────────────────


class MCQOption(StrictBaseModel):
    """A single option for a Multiple Choice Question."""

    label: Annotated[
        Literal["A", "B", "C", "D"],
        Field(description="The option label, must be exactly A, B, C, or D."),
    ]
    text: Annotated[
        str,
        Field(
            min_length=2,
            max_length=400,
            description="The full text of this answer option.",
        ),
    ]
    is_correct: Annotated[
        bool,
        Field(
            description=(
                "Whether this option is the correct answer. "
                "Exactly one option in the list must be True."
            )
        ),
    ]


class Question(StrictBaseModel):
    """A single examination question with full metadata."""

    question_number: Annotated[
        int,
        Field(ge=1, description="1-indexed question number within its section."),
    ]
    question_text: Annotated[
        str,
        Field(
            min_length=10,
            max_length=2000,
            description="The full, complete question text.",
        ),
    ]
    question_type: Annotated[
        Literal["MCQ", "SHORT_ANSWER", "LONG_ANSWER", "CASE_STUDY", "NUMERICAL", "TRUE_FALSE"],
        Field(description="The type of question. Determines which supplementary fields are required."),
    ]
    marks: Annotated[
        int,
        Field(ge=1, le=100, description="Marks awarded for this question."),
    ]
    difficulty: Annotated[
        Literal["easy", "medium", "hard"],
        Field(description="Difficulty level of the question."),
    ]
    bloom_level: Annotated[
        Literal["remember", "understand", "apply", "analyze", "evaluate", "create"],
        Field(description="Bloom's taxonomy level this question targets."),
    ]
    topic: Annotated[
        str,
        Field(
            min_length=3,
            max_length=150,
            description="The specific topic or concept this question is testing.",
        ),
    ]
    expected_word_count: Annotated[
        int | None,
        Field(
            default=None,
            ge=10,
            le=2000,
            description=(
                "Approximate expected word count for written responses. "
                "Omit for MCQ and TRUE_FALSE."
            ),
        ),
    ]
    options: Annotated[
        list[MCQOption] | None,
        Field(
            default=None,
            description="Required for MCQ type. Must be exactly 4 options with exactly 1 correct.",
        ),
    ]
    hints: Annotated[
        list[str] | None,
        Field(
            default=None,
            max_length=3,
            description="Optional pedagogical hints. Maximum 3. Omit for exam-mode papers.",
        ),
    ]

    @model_validator(mode="after")
    def validate_mcq_options(self) -> "Question":
        """Enforce MCQ structural rules at the question level."""
        if self.question_type == "MCQ":
            if self.options is None or len(self.options) == 0:
                raise ValueError("MCQ questions require 'options' to be provided.")
            if len(self.options) != 4:
                raise ValueError(
                    f"MCQ must have exactly 4 options, got {len(self.options)}."
                )
            correct_count = sum(1 for o in self.options if o.is_correct)
            if correct_count != 1:
                raise ValueError(
                    f"MCQ must have exactly 1 correct option, got {correct_count}."
                )
            labels = [o.label for o in self.options]
            if sorted(labels) != ["A", "B", "C", "D"]:
                raise ValueError("MCQ options must have labels A, B, C, D (one each).")
        elif self.options is not None:
            raise ValueError(
                f"'options' must be null for question_type='{self.question_type}'."
            )
        return self


# ── Section ──────────────────────────────────────────────────────────────────


class Section(StrictBaseModel):
    """A named section of the question paper (e.g. Section A, Section B)."""

    section_label: Annotated[
        str,
        Field(
            min_length=1,
            max_length=10,
            description="Section identifier, e.g. 'A', 'B', 'I', 'II'.",
        ),
    ]
    section_title: Annotated[
        str,
        Field(
            min_length=3,
            max_length=150,
            description="Human-readable section title, e.g. 'Short Answer Questions'.",
        ),
    ]
    instructions: Annotated[
        str | None,
        Field(
            default=None,
            max_length=500,
            description="Section-level instructions shown to the student above the questions.",
        ),
    ]
    questions_to_attempt: Annotated[
        int | None,
        Field(
            default=None,
            ge=1,
            description=(
                "For 'attempt any N' sections: how many questions the student must answer. "
                "Null means attempt all."
            ),
        ),
    ]
    questions: Annotated[
        list[Question],
        Field(
            min_length=1,
            description="All questions within this section.",
        ),
    ]
    section_marks: Annotated[
        int,
        Field(
            ge=1,
            description="Total marks for this section. Must equal sum of all question marks.",
        ),
    ]

    @model_validator(mode="after")
    def validate_marks_and_numbering(self) -> "Section":
        """Verify section marks equal the sum of question marks, and question numbers are unique."""
        computed_total = sum(q.marks for q in self.questions)
        if computed_total != self.section_marks:
            raise ValueError(
                f"Section '{self.section_label}': section_marks={self.section_marks} "
                f"but question marks sum to {computed_total}."
            )
        numbers = [q.question_number for q in self.questions]
        if len(numbers) != len(set(numbers)):
            raise ValueError(
                f"Section '{self.section_label}': question_number values must be unique."
            )
        return self


# ── Metadata ─────────────────────────────────────────────────────────────────


class PaperMetadata(StrictBaseModel):
    """Generation and source provenance metadata for the question paper."""

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
            description="UTC timestamp when this paper was generated.",
        ),
    ]
    source_document_ids: Annotated[
        list[str],
        Field(
            min_length=1,
            description="IDs of the RAG-retrieved source documents used to generate this paper.",
        ),
    ]
    difficulty_distribution: Annotated[
        dict[str, int],
        Field(
            description=(
                "Count of questions per difficulty level. "
                "Keys must be 'easy', 'medium', 'hard'."
            )
        ),
    ]
    bloom_distribution: Annotated[
        dict[str, int] | None,
        Field(
            default=None,
            description="Optional count of questions per Bloom's taxonomy level.",
        ),
    ]

    @field_validator("difficulty_distribution")
    @classmethod
    def validate_difficulty_keys(cls, v: dict[str, int]) -> dict[str, int]:
        allowed = {"easy", "medium", "hard"}
        invalid = set(v.keys()) - allowed
        if invalid:
            raise ValueError(
                f"difficulty_distribution has invalid keys: {invalid}. "
                f"Allowed: {allowed}"
            )
        return v


# ── Root model ───────────────────────────────────────────────────────────────


class QuestionPaper(StrictBaseModel):
    """
    Complete AI-generated question paper.

    All AI generation for question papers must return this exact schema.
    Plain text responses are rejected; partial schemas trigger automatic retry.
    """

    title: Annotated[
        str,
        Field(
            min_length=5,
            max_length=200,
            description="Full title of the examination paper.",
        ),
    ]
    course_name: Annotated[
        str,
        Field(min_length=3, max_length=150, description="Name of the course."),
    ]
    subject_area: Annotated[
        str,
        Field(
            min_length=3,
            max_length=100,
            description="Academic subject area, e.g. 'Computer Science', 'Mathematics'.",
        ),
    ]
    exam_duration_minutes: Annotated[
        int,
        Field(
            ge=30,
            le=360,
            description="Allowed examination time in minutes.",
        ),
    ]
    total_marks: Annotated[
        int,
        Field(ge=10, le=500, description="Total marks for the entire paper."),
    ]
    instructions: Annotated[
        list[str],
        Field(
            min_length=1,
            max_length=10,
            description=(
                "General instructions shown at the top of the paper "
                "(e.g. 'All questions are compulsory'). Min 1, max 10 items."
            ),
        ),
    ]
    sections: Annotated[
        list[Section],
        Field(
            min_length=1,
            max_length=10,
            description="All sections of this paper.",
        ),
    ]
    metadata: Annotated[
        PaperMetadata,
        Field(description="Generation provenance and quality metadata."),
    ]

    @model_validator(mode="after")
    def validate_total_marks(self) -> "QuestionPaper":
        """Enforce that total_marks equals the sum of all section marks."""
        computed = sum(s.section_marks for s in self.sections)
        if computed != self.total_marks:
            raise ValueError(
                f"total_marks={self.total_marks} but sections sum to {computed}. "
                "Adjust section_marks or total_marks to match."
            )
        return self
