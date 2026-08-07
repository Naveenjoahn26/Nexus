"""
NEXUS EDU — Documents API Router.

Handles file uploads and ingestion.
No IDs are required from the client — all are auto-generated and linked to the JWT user.
"""

from __future__ import annotations

import shutil
import uuid
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import RequireActiveUser, UserWorkspace, get_rag_pipeline
from app.core.config import Settings, get_settings
from app.core.exceptions import UnsupportedFileTypeError
from app.database.session import get_db_session
from app.schemas.api import StandardResponse, UploadResponse

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload", response_model=StandardResponse[UploadResponse])
async def upload_document(
    file: Annotated[UploadFile, File(..., description="The document file to upload.")],
    user: RequireActiveUser,
    workspace_id: UserWorkspace,
    pipeline=Depends(get_rag_pipeline),
    settings: Annotated[Settings, Depends(get_settings)] = None,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Upload a document. The file is indexed and linked to your account automatically.
    No IDs are required — just upload the file.
    """
    if settings is None:
        settings = get_settings()

    ext = Path(file.filename or "").suffix.lower()
    if ext not in [".pdf", ".docx", ".pptx", ".txt", ".md"]:
        raise UnsupportedFileTypeError(ext)

    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    document_id = str(uuid.uuid4())
    safe_filename = f"{document_id}{ext}"
    file_path = upload_dir / safe_filename

    from app.models.document import Document
    import os

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")

    try:
        result = await pipeline.ingest(
            document_id=document_id,
            file_path=str(file_path),
            course_id=str(workspace_id),
            metadata={"filename": file.filename or "unknown"},
        )

        db.add(Document(
            id=uuid.UUID(document_id),
            course_id=workspace_id,
            filename=safe_filename,
            original_filename=file.filename or "unknown",
            file_type=ext.replace(".", ""),
            file_size_bytes=os.path.getsize(file_path) if file_path.exists() else 0,
            storage_path=str(file_path),
            ingestion_status="completed",
            chunk_count=result.chunk_count,
            child_chunk_count=result.child_chunk_count,
            parent_chunk_count=result.parent_chunk_count,
        ))
        await db.commit()

    except Exception as e:
        if file_path.exists():
            os.remove(str(file_path))
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {e}")

    return StandardResponse(
        data=UploadResponse(
            filename=file.filename or "unknown",
            status="indexed",
            chunks_indexed=result.chunk_count,
        )
    )


@router.delete("/{document_id}", response_model=StandardResponse)
async def delete_document(
    document_id: str,
    user: RequireActiveUser,
    workspace_id: UserWorkspace,
    pipeline=Depends(get_rag_pipeline),
):
    """Delete one of your documents from the index."""
    await pipeline.delete_document(document_id, str(workspace_id))
    return StandardResponse(data={"deleted": True})
