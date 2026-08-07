"""
NEXUS EDU — Shared Prompt Utilities.

Common prompt-building helpers shared across all generation services.
"""

from __future__ import annotations


def format_context_block(chunks: list) -> str:
    """
    Format a list of RetrievedChunks into a numbered context block
    suitable for injection into any generation prompt.

    Each chunk is preceded by its source document ID and relevance score
    so the LLM can weight evidence and the output schema can reference chunk IDs.
    """
    if not chunks:
        return "(No context available.)"

    lines: list[str] = ["--- RETRIEVED CONTEXT ---"]
    for i, chunk in enumerate(chunks, start=1):
        doc_id = chunk.metadata.get("document_id", "unknown")
        lines.append(f"\n[{i}] chunk_id={chunk.chunk_id} | source={doc_id} | score={chunk.score:.3f}")
        lines.append(chunk.content.strip())

    lines.append("\n--- END CONTEXT ---")
    return "\n".join(lines)
