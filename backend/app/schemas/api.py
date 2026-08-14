"""
NEXUS EDU — API Schemas.

Defines the standard request and response models for the FastAPI layer,
including authentication, standard wrapped responses, and user operations.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, EmailStr, Field

T = TypeVar("T")


class StandardResponse(BaseModel, Generic[T]):
    """
    Standardized API response format for all generation and retrieval endpoints.
    Ensures consistent parsing on the client side.
    """
    success: bool = True
    data: T | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    sources: list[dict[str, Any]] = Field(default_factory=list)
    error: str | None = None


# ── Auth & Token Schemas ─────────────────────────────────────────

class Token(BaseModel):
    """OAuth2 JWT Token response."""
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Payload stored in the JWT."""
    sub: str | None = None
    role: str | None = None


# ── User Schemas ─────────────────────────────────────────────────

class UserCreate(BaseModel):
    """Payload for user registration."""
    email: EmailStr
    full_name: str
    password: str = Field(min_length=8)


class UserRead(BaseModel):
    """Public user profile."""
    id: uuid.UUID
    email: EmailStr
    full_name: str
    role: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── Course Schemas ─────────────────────────────────────────────────

class CourseCreate(BaseModel):
    name: str
    code: str | None = None
    description: str | None = None
    subject_area: str | None = None
    academic_level: str = "undergraduate"

class CourseRead(BaseModel):
    id: uuid.UUID
    name: str
    code: str | None
    description: str | None
    subject_area: str | None
    academic_level: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# ── Document & Ingestion Schemas ─────────────────────────────────

class UploadResponse(BaseModel):
    """Response returned after a file is uploaded and ingestion begins."""
    id: str | None = None
    filename: str
    status: str
    chunks_indexed: int = 0
    chunks: int = 0

# ── Generation Schemas ───────────────────────────────────────────

class GeneratePayload(BaseModel):
    """Minimal payload for AI generation endpoints. No IDs required."""
    topic: str = Field(..., description="The topic or subject to generate content for.")
    additional_instructions: str | None = Field(None, description="Optional extra instructions.")

class GeneratePresentationPayload(GeneratePayload):
    """Payload specific for presentation generation."""
    num_slides: int | None = Field(None, description="Number of slides to generate (max 8).")


class ChatMessage(BaseModel):
    """Chat message payload. Just the message — context is resolved from your JWT."""
    message: str = Field(..., description="Your message or question.")

