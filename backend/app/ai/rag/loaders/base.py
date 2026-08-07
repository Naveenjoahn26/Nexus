"""
NEXUS EDU — Document Loader Base.

Defines the contract for all document loaders and the
RawDocument data structure for loaded content.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass(frozen=True)
class RawDocument:
    """
    A single unit of loaded content (typically one page or section).

    Attributes:
        content: The extracted text.
        metadata: Source info (file_path, page_number, file_type, etc.).
    """

    content: str
    metadata: dict = field(default_factory=dict)


class BaseLoader(ABC):
    """Abstract base for all document loaders."""

    @abstractmethod
    async def load(self, file_path: str) -> list[RawDocument]:
        """
        Load a file and return a list of RawDocuments.

        Each loader decides its own granularity (e.g., per-page for PDFs,
        whole-file for plain text).

        Args:
            file_path: Absolute path to the file.

        Returns:
            List of RawDocument instances.

        Raises:
            DocumentLoadError: If the file cannot be loaded.
        """
        ...
