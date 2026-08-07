"""
NEXUS EDU — Conversation Repository.

Handles CRUD operations and history retrieval for conversations
and messages. Used exclusively by the AI Orchestrator.
"""

from __future__ import annotations

import uuid
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.conversation import Conversation
from app.models.message import Message


class ConversationRepository:
    """Repository for managing AI conversations and messages."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_conversation(
        self, user_id: uuid.UUID, course_id: uuid.UUID, title: str
    ) -> Conversation:
        """Create a new conversation session."""
        conv = Conversation(
            user_id=user_id,
            course_id=course_id,
            title=title,
        )
        self.session.add(conv)
        await self.session.flush()
        return conv

    async def get_conversation(self, conversation_id: uuid.UUID) -> Conversation | None:
        """Fetch a conversation and all its messages (ordered by time)."""
        stmt = (
            select(Conversation)
            .where(Conversation.id == conversation_id, Conversation.is_deleted == False)
            .options(selectinload(Conversation.messages))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def add_message(
        self,
        conversation_id: uuid.UUID,
        role: str,
        content: str | None = None,
        structured_response: dict | None = None,
        generation_metadata: dict | None = None,
    ) -> Message:
        """
        Append a new message to the conversation.
        
        Args:
            conversation_id: The active conversation ID.
            role: 'user' or 'assistant'.
            content: Raw text (the user's prompt).
            structured_response: The validated JSON output from the AI (for assistant).
            generation_metadata: Telemetry dict (for assistant).
        """
        msg = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            structured_response=structured_response,
            generation_metadata=generation_metadata,
        )
        self.session.add(msg)
        await self.session.flush()
        return msg

    async def get_recent_history(
        self, conversation_id: uuid.UUID, limit: int = 10
    ) -> Sequence[Message]:
        """Fetch the most recent N messages for context injection."""
        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        # Reverse to chronological order
        messages = list(result.scalars().all())
        messages.reverse()
        return messages

    async def get_user_conversations(self, user_id: uuid.UUID) -> Sequence[Conversation]:
        """Fetch all non-deleted conversations for a user, newest first."""
        stmt = (
            select(Conversation)
            .where(Conversation.user_id == user_id, Conversation.is_deleted == False)
            .order_by(Conversation.updated_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def delete_conversation(self, conversation_id: uuid.UUID) -> bool:
        """Soft delete a conversation."""
        conv = await self.session.get(Conversation, conversation_id)
        if conv and not conv.is_deleted:
            conv.is_deleted = True
            await self.session.flush()
            return True
        return False
