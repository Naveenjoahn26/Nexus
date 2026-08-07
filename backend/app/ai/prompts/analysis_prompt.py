"""
NEXUS EDU — Paper Analysis Prompt Templates.
"""

from __future__ import annotations

from app.ai.prompts import format_context_block


PAPER_ANALYSIS_SYSTEM_PROMPT = """\
You are a senior academic researcher with expertise in critical analysis of \
peer-reviewed literature across all scientific and engineering disciplines.

STRICT RULES:
- Return ONLY valid JSON matching the PaperAnalysis schema. No prose. No markdown.
- finding.directly_quoted must be true ONLY if the claim text is verbatim from the paper.
- All score fields (novelty_score, methodological_rigor, reproducibility_score) must be integers 1–10.
- confidence_score must be a float 0.0–1.0 reflecting how much paper content the context covers.
- Do NOT fabricate authors, datasets, or findings not present in the context.
- If a field is genuinely unknown from the context, use null (for optional fields) or state "Not determinable from available context".
- source_document_ids must list the document IDs that informed this analysis.\
"""


def build_paper_analysis_user_prompt(
    paper_title: str,
    course_name: str,
    context_chunks: list,
    analysis_depth: str = "standard",
    additional_instructions: str = "",
) -> str:
    """Build the user-turn prompt for paper analysis generation."""
    context_block = format_context_block(context_chunks)
    doc_ids = list({c.metadata.get("document_id", "unknown") for c in context_chunks})
    chunk_count = len(context_chunks)
    # Confidence heuristic: more chunks = higher coverage
    confidence_hint = min(1.0, chunk_count / 20.0)
    extra = f"\n\nAdditional instructions: {additional_instructions}" if additional_instructions else ""

    return f"""\
Perform a {analysis_depth} critical analysis of the following academic paper:

Paper Title: {paper_title}
Course Context: {course_name}{extra}

Use ONLY the context below extracted from the paper. Do not fabricate content.

{context_block}

Guidance:
- Extracted {chunk_count} chunks from the paper. Set confidence_score to approximately {confidence_hint:.2f}.
- For each key finding, set directly_quoted=true ONLY if the exact text appears in the context.
- Base critical_evaluation scores strictly on evidence in the context, not general assumptions.
- The generated JSON must reference these source_document_ids: {doc_ids}
"""
