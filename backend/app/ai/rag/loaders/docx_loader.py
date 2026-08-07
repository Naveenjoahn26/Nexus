"""
NEXUS EDU — DOCX Document Loader.

Extracts text from Microsoft Word (.docx) files using python-docx.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

import docx

from app.ai.rag.loaders.base import BaseLoader, RawDocument
from app.core.exceptions import DocumentLoadError

logger = logging.getLogger(__name__)


class DOCXLoader(BaseLoader):
    """
    Loader for Microsoft Word (.docx) documents.
    Extracts all paragraphs into a single RawDocument.
    """

    async def load(self, file_path: str | Path) -> list[RawDocument]:
        """
        Load a DOCX file asynchronously.

        Args:
            file_path: Path to the .docx file.

        Returns:
            A list containing a single RawDocument with the extracted text.

        Raises:
            LoadError: If the file cannot be read or parsed.
        """
        path_str = str(file_path)
        logger.debug("Loading DOCX file: %s", path_str)

        try:
            return await asyncio.to_thread(self._load_sync, path_str)
        except Exception as exc:
            logger.error("Failed to load DOCX '%s': %s", path_str, exc)
            raise DocumentLoadError(path_str, f"Exception: {exc}") from exc

    def _load_sync(self, file_path: str) -> list[RawDocument]:
        """Synchronous file loading."""
        doc = docx.Document(file_path)
        
        # Extract text from paragraphs
        text_content = "\\n\\n".join([p.text for p in doc.paragraphs if p.text.strip()])

        if not text_content.strip():
            logger.warning("No text extracted from DOCX: %s", file_path)

        metadata = {
            "source": str(Path(file_path).name),
            "file_type": "docx",
        }

        # We return a single document rather than per-page because DOCX doesn't have fixed pages
        return [RawDocument(content=text_content, metadata=metadata)]
