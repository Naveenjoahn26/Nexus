"""
NEXUS EDU — Message & Generation Metadata Models.

Stores individual user prompts and AI responses within a conversation.
AI responses capture structured telemetry (latency, tokens, sources) 
in a JSONB column to prevent schema bloat while retaining queryability.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    
    # role: 'user' | 'assistant' | 'system'
    role: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    
    # Raw text content (the prompt for user, or raw text for assistant)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # For structured AI outputs (LectureNotes, QuestionPaper, etc.), store the raw JSON here.
    structured_response: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    
    # Telemetry and metadata for AI generations (matches GenerationMetadata schema)
    # Stored as JSONB so we can query on it later (e.g., avg latency per model).
    generation_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="messages")  # noqa: F821

    def __repr__(self) -> str:
        return f"<Message id={self.id} role={self.role}>"
