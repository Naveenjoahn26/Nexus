"""
NEXUS EDU — Summary Prompt Templates.
"""

from __future__ import annotations

from app.ai.prompts import format_context_block


SUMMARY_SYSTEM_PROMPT = """\
You are an expert academic summarizer who distills complex material into \
clear, accurate, and well-structured summaries.

STRICT RULES:
- Return ONLY valid JSON matching the ContentSummary schema. No prose. No markdown.
- executive_summary must be self-contained (80–400 chars). Do not reference key_points by number.
- key_points must be numbered sequentially from 1.
- Every KeyPoint MUST have source_chunk_ids listing the specific chunks it was derived from.
- tags must be lowercase and hyphen-separated (e.g. "machine-learning", "neural-networks").
- compression_ratio = summary_word_count / source_word_count. Estimate based on context size.
- Do NOT fabricate content. Every point must be grounded in the provided context.\
"""


def build_summary_user_prompt(
    topic: str,
    course_name: str,
    context_chunks: list,
    summary_type: str = "document",
    difficulty_level: str = "intermediate",
    additional_instructions: str = "",
) -> str:
    """Build the user-turn prompt for summary generation."""
    context_block = format_context_block(context_chunks)
    doc_ids = list({c.metadata.get("document_id", "unknown") for c in context_chunks})
    chunk_ids = [c.chunk_id for c in context_chunks]
    source_word_count_estimate = sum(len(c.content.split()) for c in context_chunks)
    extra = f"\n\nAdditional instructions: {additional_instructions}" if additional_instructions else ""

    return f"""\
Generate a structured summary for the following:

Course: {course_name}
Topic: {topic}
Summary Type: {summary_type}
Target Difficulty Level: {difficulty_level}{extra}

Use ONLY the context below. Do not fabricate information.

{context_block}

Guidance:
- Source material is approximately {source_word_count_estimate} words.
- Set compression_ratio = (summary word count) / {source_word_count_estimate}.
- Every key_point MUST include source_chunk_ids from this list: {chunk_ids}
- The generated JSON must reference these source_document_ids: {doc_ids}
"""
