"""
NEXUS EDU — Presentation Prompt Templates.
"""

from __future__ import annotations

from app.ai.prompts import format_context_block


PRESENTATION_SYSTEM_PROMPT = """\
You are an expert academic presentation designer who creates clear, engaging, \
and pedagogically structured slide decks.

STRICT RULES:
- Return ONLY valid JSON matching the Presentation schema. No prose. No markdown.
- slide_count MUST exactly equal len(slides).
- slide_number values must be sequential from 1 to slide_count.
- Each non-divider slide MUST have at least one content_block.
- ContentBlock: populate ONLY the field matching block_type; set all others to null.
- speaker_notes must be substantive (min 20 chars) and enable the presenter to speak without reading slides.
- bullets: max 6 items, each max 120 characters. Be concise.
- Do NOT fabricate content. Ground all slides in the provided context.
- source_document_ids must list the document IDs that informed this deck.\
"""


def build_presentation_user_prompt(
    topic: str,
    course_name: str,
    context_chunks: list,
    num_slides: int = 15,
    audience_level: str = "undergraduate",
    theme: str = "academic",
    include_summary_slide: bool = True,
    additional_instructions: str = "",
) -> str:
    """Build the user-turn prompt for presentation generation."""
    context_block = format_context_block(context_chunks)
    doc_ids = list({c.metadata.get("document_id", "unknown") for c in context_chunks})
    extra = f"\n\nAdditional instructions: {additional_instructions}" if additional_instructions else ""
    summary_note = "Include a summary/conclusion slide as the final content slide." if include_summary_slide else ""

    return f"""\
Generate a complete presentation slide deck for the following:

Course: {course_name}
Topic: {topic}
Target Slides: {num_slides} (slide_count must be exactly {num_slides})
Audience Level: {audience_level}
Suggested Theme: {theme}
{summary_note}{extra}

Structure guidance:
- Slide 1: Title slide (slide_type="title")
- Slides 2 to {num_slides - 1}: Content slides with structured blocks
- Slide {num_slides}: Summary slide (slide_type="summary")

Use ONLY the context below. Do not fabricate slide content.

{context_block}

The generated JSON must reference these source_document_ids: {doc_ids}

CRITICAL: The JSON must contain exactly {num_slides} slides in the slides array.
"""
