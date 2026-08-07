"""
NEXUS EDU — User Repository.
"""

from __future__ import annotations

import uuid
from typing import cast

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    """Repository for managing users in PostgreSQL."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_email(self, email: str) -> User | None:
        """Fetch a user by email (case-insensitive)."""
        # Use LOWER() for case-insensitive comparison
        stmt = select(User).where(
            func.lower(User.email) == email.lower(),
            User.deleted_at.is_(None)
        )
        result = await self._session.execute(stmt)
        return cast(User | None, result.scalar_one_or_none())

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        """Fetch a user by ID."""
        stmt = select(User).where(User.id == user_id, User.deleted_at.is_(None))
        result = await self._session.execute(stmt)
        return cast(User | None, result.scalar_one_or_none())

    async def create(self, user: User) -> User:
        """Create a new user."""
        self._session.add(user)
        # Flush to get the generated ID without committing the transaction
        await self._session.flush()
        return user
