"""
NEXUS EDU — Async Session Factory.

Provides a context-managed async session for use in FastAPI dependencies
and repository classes. Each request gets its own session; the session is
committed or rolled back at the end of the request scope.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.database.database import get_engine

# Session factory — created once, reused across all requests.
# expire_on_commit=False prevents lazy-load errors after commit
# when the session is closed but the object is still referenced.
AsyncSessionFactory: async_sessionmaker[AsyncSession] | None = None


def _get_factory() -> async_sessionmaker[AsyncSession]:
    global AsyncSessionFactory
    if AsyncSessionFactory is None:
        AsyncSessionFactory = async_sessionmaker(
            bind=get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )
    return AsyncSessionFactory


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency: yields an AsyncSession scoped to a single request.

    Usage:
        @router.get("/endpoint")
        async def handler(db: AsyncSession = Depends(get_db_session)):
            ...
    """
    factory = _get_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
