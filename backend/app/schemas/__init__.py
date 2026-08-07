"""
NEXUS EDU — Pydantic Schemas Package.

All AI-generated outputs must map to one of the schemas exported here.
The LLM layer never returns plain text — only validated instances of these models.
"""

# Shared RAG schemas
from app.schemas.common import IngestResult, RetrievedChunk

# API schemas
from app.schemas.api import (
    StandardResponse,
    Token,
    TokenData,
    UserCreate,
    UserRead,
    UploadResponse,
    GeneratePayload,
    ChatMessage,
)
from app.schemas.chat import ChatMessageResponse, ConversationSummary

# AI output schemas — all inherit from StrictBaseModel (extra=forbid, strict=True)
from app.schemas.lecture_notes import (
    KeyTerm,
    LectureNotes,
    LectureSection,
    LectureSubsection,
    NotesMetadata,
    Reference,
)
from app.schemas.paper_analysis import (
    AnalysisMetadata,
    CriticalEvaluation,
    Finding,
    MethodologyBlock,
    PaperAnalysis,
    RelatedWork,
)
from app.schemas.presentation import (
    ContentBlock,
    Presentation,
    PresentationMetadata,
    Slide,
    TableData,
)
from app.schemas.question_paper import (
    MCQOption,
    PaperMetadata,
    Question,
    QuestionPaper,
    Section,
)
from app.schemas.summary import ContentSummary, KeyPoint, SummaryMetadata

__all__ = [
    # Common
    "IngestResult",
    "RetrievedChunk",
    # Question Paper
    "MCQOption",
    "PaperMetadata",
    "Question",
    "QuestionPaper",
    "Section",
    # API
    "StandardResponse",
    "Token",
    "TokenData",
    "UserCreate",
    "UserRead",
    "UploadResponse",
    "GeneratePayload",
    "ChatMessage",
    # Lecture Notes
    "KeyTerm",
    "LectureNotes",
    "LectureSection",
    "LectureSubsection",
    "NotesMetadata",
    "Reference",
    # Presentation
    "ContentBlock",
    "Presentation",
    "PresentationMetadata",
    "Slide",
    "TableData",
    # Paper Analysis
    "AnalysisMetadata",
    "CriticalEvaluation",
    "Finding",
    "MethodologyBlock",
    "PaperAnalysis",
    "RelatedWork",
    # Summary
    "ContentSummary",
    "KeyPoint",
    "SummaryMetadata",
]
