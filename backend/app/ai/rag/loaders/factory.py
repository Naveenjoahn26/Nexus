"""
NEXUS EDU — Loader Factory.

Maps file extensions to the appropriate document loader.
To add a new format, register its loader class in _LOADER_REGISTRY.
"""

from __future__ import annotations

from pathlib import Path

from app.ai.rag.loaders.base import BaseLoader
from app.ai.rag.loaders.pdf_loader import PDFLoader
from app.ai.rag.loaders.text_loader import TextLoader
from app.ai.rag.loaders.docx_loader import DOCXLoader
from app.ai.rag.loaders.pptx_loader import PPTXLoader
from app.core.exceptions import UnsupportedFileTypeError

# Extension → Loader class mapping.
# Add new loaders here as they are implemented.
_LOADER_REGISTRY: dict[str, type[BaseLoader]] = {
    ".pdf": PDFLoader,
    ".txt": TextLoader,
    ".md": TextLoader,
    ".markdown": TextLoader,
    ".docx": DOCXLoader,
    ".pptx": PPTXLoader,
}


def get_loader(file_path: str) -> BaseLoader:
    """
    Return the appropriate loader for the given file.

    Args:
        file_path: Path to the file to load.

    Returns:
        An instance of the matched BaseLoader subclass.

    Raises:
        UnsupportedFileTypeError: If no loader is registered for the extension.
    """
    ext = Path(file_path).suffix.lower()
    loader_cls = _LOADER_REGISTRY.get(ext)

    if loader_cls is None:
        raise UnsupportedFileTypeError(ext)

    return loader_cls()


def supported_extensions() -> list[str]:
    """Return all currently supported file extensions."""
    return sorted(_LOADER_REGISTRY.keys())
