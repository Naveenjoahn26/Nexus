"""
NEXUS EDU — YouTube API Router.

ChatGPT-style endpoints:
- POST /youtube/upload  → user provides only a URL
- POST /youtube/chat    → user provides only a question
- GET  /youtube/videos  → list all uploaded videos in the workspace

The backend automatically:
  - Ties all uploaded videos to the authenticated user's course workspace
  - Uses the most recently uploaded video as context for chat
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.llm.llm_service import LLMService
from app.ai.rag.embeddings.embedding_service import EmbeddingService
from app.ai.rag.indexing.vector_store import VectorStore
from app.api.dependencies import RequireActiveUser, UserWorkspace
from app.core.config import Settings, get_settings
from app.database.session import get_db_session
from app.schemas.youtube import (
    YouTubeChatRequest,
    YouTubeChatResponse,
    YouTubeUploadRequest,
    YouTubeUploadResponse,
    YouTubeVideoRead,
)
from app.services.youtube_service import YouTubeService
from app.crud.youtube import list_youtube_videos

router = APIRouter(tags=["YouTube"])


def _get_youtube_service(settings: Annotated[Settings, Depends(get_settings)]) -> YouTubeService:
    """Dependency: build YouTubeService reusing existing singletons."""
    return YouTubeService(
        settings=settings,
        embedding_service=EmbeddingService(settings),
        vector_store=VectorStore(settings),
        llm_service=LLMService(),
    )


@router.post("/upload", response_model=YouTubeUploadResponse)
async def upload_youtube_video(
    request: YouTubeUploadRequest,
    user: RequireActiveUser,
    workspace_id: UserWorkspace,
    service: YouTubeService = Depends(_get_youtube_service),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Paste a YouTube URL — the backend extracts the transcript, embeds it,
    and stores everything in your workspace. No IDs needed.
    """
    try:
        result = await service.process_youtube_video(
            url=request.url,
            course_id=workspace_id,
            db=db,
        )
        return YouTubeUploadResponse(
            message=result["message"],
            video_id=result["video_id"],
            title=result["title"],
            source=result["source"],
        )
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to process YouTube video: {exc}")


@router.post("/chat", response_model=YouTubeChatResponse)
async def chat_youtube(
    request: YouTubeChatRequest,
    user: RequireActiveUser,
    workspace_id: UserWorkspace,
    service: YouTubeService = Depends(_get_youtube_service),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Ask any question about the most recently uploaded YouTube video in your workspace.
    Just send your question — no video ID needed.
    """
    try:
        result = await service.chat(
            question=request.question,
            course_id=workspace_id,
            db=db,
        )
        return YouTubeChatResponse(
            answer=result["answer"],
            video_title=result.get("video_title", ""),
            video_url=result.get("video_url", ""),
            sources=result.get("sources", []),
        )
    except ValueError as err:
        raise HTTPException(status_code=404, detail=str(err))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"YouTube chat failed: {exc}")


@router.get("/videos", response_model=list[YouTubeVideoRead])
async def list_my_youtube_videos(
    user: RequireActiveUser,
    workspace_id: UserWorkspace,
    db: AsyncSession = Depends(get_db_session),
):
    """
    List all YouTube videos uploaded in your workspace, newest first.
    """
    return await list_youtube_videos(db, workspace_id)
