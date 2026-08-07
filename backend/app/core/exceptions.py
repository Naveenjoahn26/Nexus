"""
NEXUS EDU — Custom Exception Hierarchy.

All application-specific exceptions inherit from NexusBaseError.
This enables consistent error handling and clean error propagation
without leaking implementation details to API consumers.
"""


class NexusBaseError(Exception):
    """Base exception for all NEXUS EDU errors."""

    def __init__(self, message: str = "An unexpected error occurred.") -> None:
        self.message = message
        super().__init__(self.message)

class APIException(NexusBaseError):
    """Base class for all API-related exceptions that map to HTTP codes."""
    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        super().__init__(message)


# ── Document Errors ──────────────────────────────────────────────


class DocumentLoadError(NexusBaseError):
    """Raised when a document cannot be loaded or parsed."""

    def __init__(self, file_path: str, reason: str = "") -> None:
        detail = f"Failed to load document: {file_path}"
        if reason:
            detail += f" — {reason}"
        super().__init__(detail)


class UnsupportedFileTypeError(NexusBaseError):
    """Raised when a file type has no registered loader."""

    def __init__(self, file_extension: str) -> None:
        super().__init__(
            f"Unsupported file type: '{file_extension}'. "
            f"Supported types: .pdf, .txt, .md"
        )


# ── RAG Pipeline Errors ─────────────────────────────────────────


class EmbeddingError(NexusBaseError):
    """Raised when embedding generation fails."""

    def __init__(self, reason: str = "Embedding generation failed.") -> None:
        super().__init__(reason)


class RetrievalError(NexusBaseError):
    """Raised when retrieval operations fail."""

    def __init__(self, reason: str = "Retrieval failed.") -> None:
        super().__init__(reason)


class IndexingError(NexusBaseError):
    """Raised when vector store or index operations fail."""

    def __init__(self, reason: str = "Indexing operation failed.") -> None:
        super().__init__(reason)


# ── Ingestion Errors ─────────────────────────────────────────────


class IngestionError(NexusBaseError):
    """Raised when the document ingestion pipeline fails."""

    def __init__(self, document_id: str, reason: str = "") -> None:
        detail = f"Ingestion failed for document '{document_id}'"
        if reason:
            detail += f" — {reason}"
        super().__init__(detail)


# ── AI Generation Service Errors ─────────────────────────────────


class GenerationError(NexusBaseError):
    """
    Base exception for all AI generation service failures.
    Carries the service name and attempt count for structured logging.
    """

    def __init__(self, service: str, reason: str, attempts: int = 1) -> None:
        self.service = service
        self.attempts = attempts
        super().__init__(
            f"[{service}] Generation failed after {attempts} attempt(s): {reason}"
        )


class LectureGenerationError(GenerationError):
    """Raised when lecture notes generation fails."""

    def __init__(self, reason: str, attempts: int = 1) -> None:
        super().__init__("LectureGenerationService", reason, attempts)


class QuestionPaperGenerationError(GenerationError):
    """Raised when question paper generation fails."""

    def __init__(self, reason: str, attempts: int = 1) -> None:
        super().__init__("QuestionPaperGenerationService", reason, attempts)


class PresentationGenerationError(GenerationError):
    """Raised when presentation generation fails."""

    def __init__(self, reason: str, attempts: int = 1) -> None:
        super().__init__("PresentationGenerationService", reason, attempts)


class SummaryGenerationError(GenerationError):
    """Raised when summary generation fails."""

    def __init__(self, reason: str, attempts: int = 1) -> None:
        super().__init__("SummaryGenerationService", reason, attempts)


class PaperAnalysisError(GenerationError):
    """Raised when paper analysis generation fails."""

    def __init__(self, reason: str, attempts: int = 1) -> None:
        super().__init__("PaperAnalysisService", reason, attempts)


class InsufficientContextError(APIException):
    """
    Raised when the RAG pipeline returns insufficient context
    to generate a trustworthy output.
    """

    def __init__(self, service: str, course_id: str, min_chunks: int) -> None:
        super().__init__(
            status_code=400,
            message=f"[{service}] Insufficient RAG context for course '{course_id}'. "
                    f"Need at least {min_chunks} chunk(s) to generate content."
        )

# ── API / HTTP Errors ─────────────────────────────────────────────


class CredentialsException(APIException):
    """Raised for 401 Unauthorized errors."""
    def __init__(self, message: str = "Could not validate credentials") -> None:
        super().__init__(status_code=401, message=message)


class PermissionDeniedException(APIException):
    """Raised for 403 Forbidden errors."""
    def __init__(self, message: str = "Permission denied") -> None:
        super().__init__(status_code=403, message=message)


class ResourceNotFoundError(APIException):
    """Raised for 404 Not Found errors."""
    def __init__(self, resource: str = "Resource") -> None:
        super().__init__(status_code=404, message=f"{resource} not found")


class ResourceConflictError(APIException):
    """Raised for 409 Conflict errors (e.g., duplicate user)."""
    def __init__(self, message: str = "Resource conflict") -> None:
        super().__init__(status_code=409, message=message)

