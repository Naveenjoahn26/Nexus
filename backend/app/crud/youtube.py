"""
NEXUS EDU — YouTube CRUD Operations.

Handles storing and querying YouTubeVideo records in PostgreSQL.
Videos are scoped to a course (workspace) and user — no video IDs required from clients.
"""

from __future__ import annotations

import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.youtube import YouTubeVideo


async def create_youtube_video(
    db: AsyncSession,
    course_id: uuid.UUID,
    video_id: str,
    title: str,
    url: str,
    transcript: str,
) -> YouTubeVideo:
    """Create and persist a YouTubeVideo record scoped to a course."""
    video = YouTubeVideo(
        id=uuid.uuid4(),
        course_id=course_id,
        video_id=video_id,
        title=title,
        url=url,
        transcript=transcript,
    )
    db.add(video)
    await db.commit()
    await db.refresh(video)
    return video


async def get_youtube_video_by_video_id(
    db: AsyncSession,
    video_id: str,
    course_id: uuid.UUID | None = None,
) -> YouTubeVideo | None:
    """Fetch YouTubeVideo by video_id, optionally scoped to a course."""
    stmt = select(YouTubeVideo).where(YouTubeVideo.video_id == video_id)
    if course_id is not None:
        stmt = stmt.where(YouTubeVideo.course_id == course_id)
    stmt = stmt.limit(1)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_latest_youtube_video(
    db: AsyncSession,
    course_id: uuid.UUID,
) -> YouTubeVideo | None:
    """Fetch the most recently uploaded YouTube video in a course workspace."""
    stmt = (
        select(YouTubeVideo)
        .where(YouTubeVideo.course_id == course_id)
        .order_by(YouTubeVideo.created_at.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def list_youtube_videos(
    db: AsyncSession,
    course_id: uuid.UUID,
) -> list[YouTubeVideo]:
    """List all YouTube videos uploaded in a course workspace."""
    stmt = (
        select(YouTubeVideo)
        .where(YouTubeVideo.course_id == course_id)
        .order_by(YouTubeVideo.created_at.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())
