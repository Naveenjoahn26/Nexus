"""
NEXUS EDU — YouTube Schemas.

Pydantic schemas for YouTube upload and chat endpoints.
- Upload: user provides just the URL
- Chat: user provides just a question (like ChatGPT)
  The latest uploaded video in the user's workspace is used as context automatically.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class YouTubeUploadRequest(BaseModel):
    url: str = Field(..., description="YouTube Video URL")


class YouTubeUploadResponse(BaseModel):
    message: str
    video_id: str
    title: str
    source: str = "youtube"


class YouTubeChatRequest(BaseModel):
    """
    Only the question is required.
    The backend automatically uses the most recently uploaded YouTube video
    in the user's workspace as context.
    """
    question: str = Field(..., description="Your question about the YouTube video")


class YouTubeChatResponse(BaseModel):
    answer: str
    video_title: str = ""
    video_url: str = ""
    sources: list[dict[str, Any]] = Field(default_factory=list)


class YouTubeVideoRead(BaseModel):
    """Summary of an uploaded YouTube video."""
    video_id: str
    title: str
    url: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
