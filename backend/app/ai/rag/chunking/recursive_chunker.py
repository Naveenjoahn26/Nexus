"""
NEXUS EDU — Recursive Text Chunker.

Splits text using a hierarchy of separators, respecting document structure.
Produces both parent and child chunks for parent-document retrieval.

Separator hierarchy (strongest → weakest):
  \\n\\n  →  \\n  →  ". "  →  " "

Parent chunks (~1500 chars) provide broad context for the LLM.
Child chunks (~512 chars) provide precise targets for retrieval.
Each child carries a parent_id linking it to its parent chunk.
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field

from app.ai.rag.loaders.base import RawDocument

logger = logging.getLogger(__name__)

# Separator hierarchy: strongest to weakest structural boundary.
_SEPARATORS: list[str] = ["\n\n", "\n", ". ", " "]


@dataclass
class Chunk:
    """
    A text chunk with lineage metadata.

    Not frozen because the pipeline may inject additional metadata
    (e.g., course_id) after chunk creation.
    """

    chunk_id: str
    content: str
    metadata: dict = field(default_factory=dict)


class RecursiveChunker:
    """
    Recursive character text splitter with parent-child generation.

    Tries the strongest separator first (paragraph boundary).
    Falls back to weaker separators only when a segment still exceeds
    the target chunk size. This naturally respects document structure
    in well-formatted academic text.
    """

    def __init__(
        self,
        child_chunk_size: int = 512,
        child_chunk_overlap: int = 50,
        parent_chunk_size: int = 1500,
        parent_chunk_overlap: int = 100,
    ) -> None:
        if child_chunk_size >= parent_chunk_size:
            raise ValueError(
                f"child_chunk_size ({child_chunk_size}) must be less than "
                f"parent_chunk_size ({parent_chunk_size})."
            )
        self._child_size = child_chunk_size
        self._child_overlap = child_chunk_overlap
        self._parent_size = parent_chunk_size
        self._parent_overlap = parent_chunk_overlap

    def chunk_documents(
        self,
        documents: list[RawDocument],
        document_id: str,
    ) -> tuple[list[Chunk], list[Chunk]]:
        """
        Split documents into parent and child chunks.

        Args:
            documents: List of RawDocuments (e.g., one per page from PDF).
            document_id: Unique ID for the source document.

        Returns:
            Tuple of (child_chunks, parent_chunks).
            Each child has 'parent_id' in metadata linking to its parent.
        """
        # Merge all pages into a single text stream.
        full_text = "\n\n".join(doc.content for doc in documents)

        # Preserve source metadata for lineage tracking.
        source_meta = documents[0].metadata if documents else {}

        # Step 1: Create parent chunks from the full text.
        parent_chunks = self._create_chunks(
            text=full_text,
            chunk_size=self._parent_size,
            chunk_overlap=self._parent_overlap,
            document_id=document_id,
            chunk_type="parent",
            source_meta=source_meta,
        )

        # Step 2: Create child chunks from each parent using global indexing.
        child_chunks: list[Chunk] = []
        global_child_idx = 0
        for parent in parent_chunks:
            children = self._create_chunks(
                text=parent.content,
                chunk_size=self._child_size,
                chunk_overlap=self._child_overlap,
                document_id=document_id,
                chunk_type="child",
                source_meta=source_meta,
                parent_id=parent.chunk_id,
                start_index=global_child_idx,
            )
            global_child_idx += len(children)
            child_chunks.extend(children)

        # Enforce strict ID uniqueness across all chunks
        child_chunks = self._ensure_unique_ids(child_chunks)
        parent_chunks = self._ensure_unique_ids(parent_chunks)

        logger.info(
            "Chunked document '%s': %d parent, %d child chunks.",
            document_id,
            len(parent_chunks),
            len(child_chunks),
        )
        return child_chunks, parent_chunks

    def _create_chunks(
        self,
        text: str,
        chunk_size: int,
        chunk_overlap: int,
        document_id: str,
        chunk_type: str,
        source_meta: dict,
        parent_id: str | None = None,
        start_index: int = 0,
    ) -> list[Chunk]:
        """Split text and wrap results as Chunk objects."""
        raw_splits = self._recursive_split(text, chunk_size, chunk_overlap)

        chunks: list[Chunk] = []
        for offset, content in enumerate(raw_splits):
            idx = start_index + offset
            chunk_id = self._generate_id(
                document_id=document_id,
                chunk_type=chunk_type,
                index=idx,
                content=content,
                parent_id=parent_id,
            )
            metadata: dict = {
                "document_id": document_id,
                "chunk_type": chunk_type,
                "chunk_index": idx,
                "source": source_meta.get("source", ""),
                "file_type": source_meta.get("file_type", ""),
            }
            if parent_id is not None:
                metadata["parent_id"] = parent_id

            chunks.append(Chunk(chunk_id=chunk_id, content=content, metadata=metadata))

        return chunks

    # ── Core splitting logic ─────────────────────────────────────

    def _recursive_split(
        self,
        text: str,
        chunk_size: int,
        chunk_overlap: int,
        separators: list[str] | None = None,
    ) -> list[str]:
        """
        Recursively split text using the separator hierarchy.

        Tries the current separator. If any resulting segment is still
        too large, recurses with the next (weaker) separator.
        """
        if separators is None:
            separators = list(_SEPARATORS)

        text = text.strip()
        if not text:
            return []

        # Text fits in one chunk — done.
        if len(text) <= chunk_size:
            return [text]

        # Pick the current separator; if none left, force-split by characters.
        if not separators:
            return self._force_split(text, chunk_size, chunk_overlap)

        separator = separators[0]
        remaining_separators = separators[1:]

        # If this separator isn't present in the text, try the next one.
        if separator not in text:
            return self._recursive_split(
                text, chunk_size, chunk_overlap, remaining_separators
            )

        # Split and merge segments back into chunks of the target size.
        segments = text.split(separator)
        merged = self._merge_segments(segments, separator, chunk_size, chunk_overlap)

        # Recursively split any chunks that are still too large.
        final: list[str] = []
        for chunk in merged:
            if len(chunk) > chunk_size and remaining_separators:
                sub = self._recursive_split(
                    chunk, chunk_size, chunk_overlap, remaining_separators
                )
                final.extend(sub)
            else:
                final.append(chunk)

        return final

    @staticmethod
    def _merge_segments(
        segments: list[str],
        separator: str,
        chunk_size: int,
        overlap: int,
    ) -> list[str]:
        """
        Merge small segments into chunks that fit within chunk_size.

        Maintains overlap between consecutive chunks to avoid losing
        context at chunk boundaries.
        """
        chunks: list[str] = []
        current_parts: list[str] = []
        current_len = 0

        for segment in segments:
            seg_len = len(segment) + (len(separator) if current_parts else 0)

            if current_len + seg_len > chunk_size and current_parts:
                # Finalize the current chunk.
                merged = separator.join(current_parts).strip()
                if merged:
                    chunks.append(merged)

                # Start the next chunk with overlap from the end of the current.
                if overlap > 0:
                    overlap_text = merged[-overlap:]
                    current_parts = [overlap_text]
                    current_len = len(overlap_text)
                else:
                    current_parts = []
                    current_len = 0

            current_parts.append(segment)
            current_len += seg_len

        # Flush remaining.
        if current_parts:
            merged = separator.join(current_parts).strip()
            if merged:
                chunks.append(merged)

        return chunks

    @staticmethod
    def _force_split(text: str, chunk_size: int, overlap: int) -> list[str]:
        """Last resort: split by character count with overlap."""
        chunks: list[str] = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            step = chunk_size - overlap if overlap > 0 else chunk_size
            start += max(step, 1)  # Guard against zero/negative step
        return chunks

    @staticmethod
    def _generate_id(
        document_id: str,
        chunk_type: str,
        index: int,
        content: str,
        parent_id: str | None = None,
    ) -> str:
        """
        Generate a deterministic chunk ID.

        Includes a content hash so the same document re-ingested
        with the same parameters produces identical IDs (idempotent).
        """
        hash_input = f"{document_id}:{chunk_type}:{index}:{content[:100]}"
        if parent_id:
            hash_input += f":{parent_id}"
        content_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:12]
        return f"{chunk_type}_{content_hash}"

    @staticmethod
    def _ensure_unique_ids(chunks: list[Chunk]) -> list[Chunk]:
        """
        Ensure all chunks in the list have unique chunk_ids.

        If a duplicate ID is encountered (e.g. identical text segments),
        append a suffix index to preserve uniqueness.
        """
        seen_ids: set[str] = set()
        for chunk in chunks:
            base_id = chunk.chunk_id
            suffix = 0
            while chunk.chunk_id in seen_ids:
                suffix += 1
                chunk.chunk_id = f"{base_id}_{suffix}"
            seen_ids.add(chunk.chunk_id)
        return chunks

