"""
NEXUS EDU — Document Model.

Tracks ingested source documents per course.
Embeddings and chunk data live in ChromaDB — this model stores
only file metadata and ingestion provenance.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.course import Course

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str] = mapped_column(String(20), nullable=False)   # pdf | txt | md
    file_size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    storage_path: Mapped[str] = mapped_column(Text, nullable=False)      # local path or object store key
    ingestion_status: Mapped[str] = mapped_column(
        String(20), default="pending", nullable=False
    )  # pending | processing | completed | failed
    chunk_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    child_chunk_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    parent_chunk_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    ingestion_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    ingested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    @hybrid_property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    @is_deleted.setter
    def is_deleted(self, value: bool) -> None:
        self.deleted_at = datetime.now(timezone.utc) if value else None

    @is_deleted.expression
    def is_deleted(cls):
        return cls.deleted_at.is_not(None)

    # Relationships
    course: Mapped["Course"] = relationship("Course", back_populates="documents")  # noqa: F821

    def __repr__(self) -> str:
        return f"<Document id={self.id} filename={self.filename} status={self.ingestion_status}>"
