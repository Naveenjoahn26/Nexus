"""
NEXUS EDU — Plain Text / Markdown Loader.

Loads .txt and .md files as a single RawDocument.
Uses asyncio.to_thread to avoid blocking the event loop on file I/O.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from app.ai.rag.loaders.base import BaseLoader, RawDocument
from app.core.exceptions import DocumentLoadError

logger = logging.getLogger(__name__)

_SUPPORTED_EXTENSIONS = {".txt", ".md", ".markdown"}


class TextLoader(BaseLoader):
    """Load plain text and markdown files."""

    async def load(self, file_path: str) -> list[RawDocument]:
        """
        Load a text file as a single RawDocument.

        Falls back to latin-1 encoding if UTF-8 decoding fails.
        """
        path = Path(file_path)
        if not path.exists():
            raise DocumentLoadError(file_path, "File does not exist.")
        if path.suffix.lower() not in _SUPPORTED_EXTENSIONS:
            raise DocumentLoadError(
                file_path,
                f"Unsupported extension '{path.suffix}'. "
                f"Expected one of {_SUPPORTED_EXTENSIONS}.",
            )

        return await asyncio.to_thread(self._read_file, file_path)

    def _read_file(self, file_path: str) -> list[RawDocument]:
        """Synchronous file read with encoding fallback."""
        path = Path(file_path)

        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            logger.warning(
                "UTF-8 decode failed for %s, falling back to latin-1.", file_path
            )
            content = path.read_text(encoding="latin-1")
        except Exception as exc:
            raise DocumentLoadError(file_path, str(exc)) from exc

        content = content.strip()
        if not content:
            raise DocumentLoadError(file_path, "File is empty.")

        logger.info(
            "Loaded text file: %s — %d characters.", file_path, len(content)
        )
        return [
            RawDocument(
                content=content,
                metadata={
                    "source": file_path,
                    "file_type": path.suffix.lstrip("."),
                },
            )
        ]
