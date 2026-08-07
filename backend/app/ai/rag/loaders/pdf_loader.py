"""
NEXUS EDU — PDF Document Loader.

Uses PyMuPDF (fitz) for fast, high-quality text extraction from PDFs.
Outputs one RawDocument per page with normalized text.

Design choice: PyMuPDF over pdfplumber/Unstructured because it's
10x faster and handles 95% of academic PDFs well. If table extraction
becomes critical, we can add a specialized table loader later.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

import fitz  # PyMuPDF

from app.ai.rag.loaders.base import BaseLoader, RawDocument
from app.core.exceptions import DocumentLoadError

logger = logging.getLogger(__name__)


class PDFLoader(BaseLoader):
    """Extract text from PDF files using PyMuPDF."""

    async def load(self, file_path: str) -> list[RawDocument]:
        """
        Load a PDF and return one RawDocument per page.

        Strips artifacts and normalizes whitespace for clean chunking.
        Pages with no extractable text are skipped with a debug log.
        """
        path = Path(file_path)
        if not path.exists():
            raise DocumentLoadError(file_path, "File does not exist.")
        if path.suffix.lower() != ".pdf":
            raise DocumentLoadError(file_path, "Not a PDF file.")

        # PyMuPDF is CPU-bound; offload to thread to keep event loop free.
        return await asyncio.to_thread(self._extract_pages, file_path)

    def _extract_pages(self, file_path: str) -> list[RawDocument]:
        """Synchronous page-by-page PDF text extraction."""
        documents: list[RawDocument] = []

        try:
            doc = fitz.open(file_path)
        except Exception as exc:
            raise DocumentLoadError(file_path, str(exc)) from exc

        try:
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text("text")

                cleaned = self._clean_text(text)
                if not cleaned:
                    logger.debug(
                        "Skipping empty page %d in %s.", page_num + 1, file_path
                    )
                    continue

                documents.append(
                    RawDocument(
                        content=cleaned,
                        metadata={
                            "source": file_path,
                            "page_number": page_num + 1,
                            "total_pages": len(doc),
                            "file_type": "pdf",
                        },
                    )
                )
        finally:
            doc.close()

        if not documents:
            raise DocumentLoadError(file_path, "No extractable text found in PDF.")

        logger.info(
            "Loaded PDF: %s — %d pages with text.", file_path, len(documents)
        )
        return documents

    @staticmethod
    def _clean_text(text: str) -> str:
        """
        Normalize whitespace and strip common PDF artifacts.

        Collapses multiple blank lines into one, strips leading/trailing
        whitespace per line. This produces clean input for the chunker.
        """
        lines = text.splitlines()
        cleaned_lines: list[str] = []
        prev_blank = False

        for line in lines:
            stripped = line.strip()
            if not stripped:
                if not prev_blank:
                    cleaned_lines.append("")
                prev_blank = True
            else:
                cleaned_lines.append(stripped)
                prev_blank = False

        return "\n".join(cleaned_lines).strip()
