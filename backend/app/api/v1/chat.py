"""
NEXUS EDU — Chat API Router.

Handles conversation management and RAG chat interactions.
Context (workspace, conversation) is resolved automatically from the JWT.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import (
    RequireActiveUser,
    UserWorkspace,
    get_ai_orchestrator,
    get_latest_conversation,
)
from app.schemas.api import ChatMessage, StandardResponse
from app.schemas.chat import ChatMessageResponse, ConversationSummary

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("", response_model=StandardResponse[ChatMessageResponse])
async def send_chat_message(
    request: ChatMessage,
    user: RequireActiveUser,
    workspace_id: UserWorkspace,
    conversation_id: Annotated[uuid.UUID | None, Depends(get_latest_conversation)],
    orchestrator=Depends(get_ai_orchestrator),
):
    """
    Send a message. Context (workspace + conversation) is auto-resolved from your JWT.
    A new conversation is automatically created on first message.
    """
    result = await orchestrator.execute(
        user_id=user.id,
        course_id=workspace_id,
        action_type="chat",
        conversation_id=conversation_id,
        topic=request.message,
    )
    return StandardResponse(
        data=ChatMessageResponse(
            conversation_id=uuid.UUID(str(result["conversation_id"])),
            message_id=uuid.UUID(str(result["message_id"])),
            content=result["data"].get("content", ""),
        )
    )


@router.get("/conversations", response_model=StandardResponse[list[ConversationSummary]])
async def get_conversations(
    user: RequireActiveUser,
    orchestrator=Depends(get_ai_orchestrator),
):
    """Retrieve all your conversation threads, newest first."""
    conversations = await orchestrator.repo.get_user_conversations(user.id)
    return StandardResponse(
        data=[
            ConversationSummary(
                id=c.id,
                title=c.title,
                created_at=c.created_at,
                updated_at=c.updated_at,
            )
            for c in conversations
        ]
    )


@router.delete("/conversations/{conversation_id}", response_model=StandardResponse)
async def delete_conversation(
    conversation_id: uuid.UUID,
    user: RequireActiveUser,
    orchestrator=Depends(get_ai_orchestrator),
):
    """Delete a conversation thread."""
    conv = await orchestrator.repo.get_conversation(conversation_id)
    if not conv or conv.user_id != user.id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    await orchestrator.repo.delete_conversation(conversation_id)
    await orchestrator.db.commit()
    return StandardResponse(data={"deleted": True})
