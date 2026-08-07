"""
NEXUS EDU — Course Model.

A Course is the top-level academic unit. Each course has its own
ChromaDB collection (nexus_{course_id}) for scoped RAG retrieval.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.conversation import Conversation
    from app.models.document import Document
    from app.models.user import User

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    code: Mapped[str | None] = mapped_column(String(30), nullable=True)  # e.g. "CS301"
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    subject_area: Mapped[str | None] = mapped_column(String(100), nullable=True)
    academic_level: Mapped[str] = mapped_column(
        String(30), default="undergraduate", nullable=False
    )  # undergraduate | postgraduate | phd
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="courses")  # noqa: F821
    documents: Mapped[list["Document"]] = relationship(  # noqa: F821
        "Document", back_populates="course", cascade="all, delete-orphan", lazy="select"
    )
    conversations: Mapped[list["Conversation"]] = relationship(  # noqa: F821
        "Conversation", back_populates="course", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<Course id={self.id} name={self.name}>"
