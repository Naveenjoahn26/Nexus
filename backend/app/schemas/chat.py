"""
NEXUS EDU — Chat Schemas.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class ChatMessageResponse(BaseModel):
    """Response containing the AI's reply and conversation context."""
    conversation_id: uuid.UUID
    message_id: uuid.UUID
    content: str


class ConversationSummary(BaseModel):
    """Metadata for a conversation thread."""
    id: uuid.UUID
    title: str
    created_at: datetime
    updated_at: datetime
