"""
NEXUS EDU — PPTX Document Loader.

Extracts text from Microsoft PowerPoint (.pptx) files using python-pptx.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

import pptx

from app.ai.rag.loaders.base import BaseLoader, RawDocument
from app.core.exceptions import DocumentLoadError

logger = logging.getLogger(__name__)


class PPTXLoader(BaseLoader):
    """
    Loader for Microsoft PowerPoint (.pptx) presentations.
    Extracts text from slides and speaker notes into RawDocuments.
    """

    async def load(self, file_path: str | Path) -> list[RawDocument]:
        """
        Load a PPTX file asynchronously.

        Args:
            file_path: Path to the .pptx file.

        Returns:
            A list of RawDocuments, typically one per slide containing text.

        Raises:
            LoadError: If the file cannot be read or parsed.
        """
        path_str = str(file_path)
        logger.debug("Loading PPTX file: %s", path_str)

        try:
            return await asyncio.to_thread(self._load_sync, path_str)
        except Exception as exc:
            logger.error("Failed to load PPTX '%s': %s", path_str, exc)
            raise DocumentLoadError(path_str, f"Exception: {exc}") from exc

    def _load_sync(self, file_path: str) -> list[RawDocument]:
        """Synchronous file loading."""
        prs = pptx.Presentation(file_path)
        documents = []

        for idx, slide in enumerate(prs.slides, start=1):
            slide_text = []
            
            # Extract text from shapes
            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text:
                    slide_text.append(shape.text)
                    
            # Extract speaker notes if any
            if slide.has_notes_slide and slide.notes_slide.notes_text_frame:
                notes = slide.notes_slide.notes_text_frame.text
                if notes.strip():
                    slide_text.append(f"Notes: {notes}")
                    
            content = "\\n\\n".join(slide_text).strip()
            
            if content:
                metadata = {
                    "source": str(Path(file_path).name),
                    "file_type": "pptx",
                    "slide_number": idx,
                }
                documents.append(RawDocument(content=content, metadata=metadata))

        if not documents:
            logger.warning("No text extracted from PPTX: %s", file_path)

        return documents
