"""
NEXUS EDU — Document Loaders.

Provides file-type-specific loaders and a factory for automatic selection.
"""

from app.ai.rag.loaders.base import BaseLoader, RawDocument
from app.ai.rag.loaders.factory import get_loader

__all__ = ["BaseLoader", "RawDocument", "get_loader"]
