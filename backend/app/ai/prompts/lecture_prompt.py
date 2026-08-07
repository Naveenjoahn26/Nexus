"""
NEXUS EDU — Lecture Notes Prompt Templates.

Pure functions. No state, no LLM calls.
Separation of prompt construction from generation logic (SRP).
"""

from __future__ import annotations

from app.ai.prompts import format_context_block


LECTURE_SYSTEM_PROMPT = """\
You are an expert academic content creator specializing in producing structured, \
pedagogically rigorous lecture notes.

STRICT RULES:
- You MUST return ONLY valid JSON matching the LectureNotes schema. No prose. No markdown.
- Every section must have a non-empty key_takeaway.
- learning_objectives must use the format: "By the end of this lecture, students will be able to [measurable action]."
- The summary must be self-contained and not reference section numbers.
- section_number values must be sequential starting from 1.
- Do NOT fabricate content. Ground all claims in the provided context.
- source_document_ids must list the document IDs that informed this output.\
"""


def build_lecture_user_prompt(
    topic: str,
    course_name: str,
    context_chunks: list,
    lecture_number: int | None = None,
    additional_instructions: str = "",
) -> str:
    """Build the user-turn prompt for lecture notes generation."""
    context_block = format_context_block(context_chunks)
    chunk_ids = [c.chunk_id for c in context_chunks]
    doc_ids = list({c.metadata.get("document_id", "unknown") for c in context_chunks})

    lecture_ref = f"Lecture {lecture_number}: " if lecture_number else ""
    extra = f"\n\nAdditional instructions: {additional_instructions}" if additional_instructions else ""

    return f"""\
Generate comprehensive lecture notes for the following:

Course: {course_name}
Topic: {lecture_ref}{topic}{extra}

Use ONLY the context below. Do not fabricate information.

{context_block}

The generated JSON must reference these source_document_ids: {doc_ids}
Available chunk_ids for reference: {chunk_ids}
"""
