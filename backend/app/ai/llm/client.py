"""
NEXUS EDU — Groq & Instructor Clients.

Provides singleton, thread-safe asynchronous clients for interacting
with Groq directly and via Instructor for structured outputs.
"""

import logging
import threading

import instructor
from groq import AsyncGroq

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# Global singletons
_std_client: AsyncGroq | None = None
_inst_client: instructor.Instructor | None = None
_lock = threading.Lock()


def get_standard_client() -> AsyncGroq:
    """
    Get or initialize the standard async Groq client.
    Used for unstructured content generation.
    """
    global _std_client
    if _std_client is None:
        with _lock:
            if _std_client is None:
                settings = get_settings()
                if not settings.groq_api_key:
                    raise ValueError("GROQ_API_KEY is not set in environment.")
                
                logger.info("Initializing Standard AsyncGroq client")
                _std_client = AsyncGroq(api_key=settings.groq_api_key)
    
    return _std_client


def get_instructor_client() -> instructor.Instructor:
    """
    Get or initialize the Instructor-patched async Groq client.
    Used exclusively for deterministic, Pydantic-validated JSON generation.
    """
    global _inst_client
    if _inst_client is None:
        with _lock:
            if _inst_client is None:
                std_client = get_standard_client()
                logger.info("Initializing Instructor-patched AsyncGroq client")
                # instructor.from_groq wraps the Groq client to intercept validation errors
                # and automatically retry with JSON mode enabled.
                _inst_client = instructor.from_groq(
                    std_client,
                    mode=instructor.Mode.JSON
                )
    
    return _inst_client
