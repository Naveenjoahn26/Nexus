"""
NEXUS EDU — Base Model Registry for Alembic.

Import all SQLAlchemy models here so Alembic can discover them
during the autogenerate phase.
"""

from app.database.base import Base

# Import all models to register them with Base.metadata
from app.models.conversation import Conversation  # noqa: F401
from app.models.course import Course  # noqa: F401
from app.models.document import Document  # noqa: F401
from app.models.message import Message  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.youtube import YouTubeVideo  # noqa: F401

