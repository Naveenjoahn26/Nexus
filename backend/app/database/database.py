"""
NEXUS EDU — Async SQLAlchemy Engine.

Creates the async engine with connection pooling sized for production.
The engine is a singleton — created once at startup, reused for the
lifetime of the process.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.core.config import get_settings

_engine: AsyncEngine | None = None


def get_engine() -> AsyncEngine:
    """Return or create the singleton async database engine."""
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            settings.database_url,
            pool_size=settings.db_pool_size,
            max_overflow=settings.db_max_overflow,
            pool_timeout=settings.db_pool_timeout,
            pool_recycle=settings.db_pool_recycle,
            pool_pre_ping=True,   # verify connections before checkout
            echo=settings.debug,  # log SQL in development only
        )
    return _engine


async def dispose_engine() -> None:
    """Gracefully close all pooled connections. Call on application shutdown."""
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None
