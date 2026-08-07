"""
NEXUS EDU — SQLAlchemy Declarative Base.

Single shared Base for all ORM models. Alembic reads this to
auto-generate migrations. Never import models directly from
this module — import from app.models.* instead.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""
    pass
