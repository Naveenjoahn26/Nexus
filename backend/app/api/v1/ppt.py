"""
NEXUS EDU — Presentation Generation Router.
"""

from __future__ import annotations

import os
import uuid
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from app.api.dependencies import RequireActiveUser, UserWorkspace, get_ai_orchestrator
from app.schemas.api import GeneratePresentationPayload, StandardResponse
from app.schemas.presentation import Presentation
from app.services.ppt.builder import PresentationBuilder

router = APIRouter(prefix="/generate/presentation", tags=["Generation"])


@router.post("", response_model=StandardResponse[Presentation])
async def generate_presentation(
    request: GeneratePresentationPayload,
    user: RequireActiveUser,
    workspace_id: UserWorkspace,
    orchestrator=Depends(get_ai_orchestrator),
):
    """Generate a presentation from your uploaded documents."""
    result = await orchestrator.execute(
        user_id=user.id,
        course_id=workspace_id,
        action_type="generate_presentation",
        topic=request.topic,
        additional_instructions=request.additional_instructions,
        num_slides=min(request.num_slides or 8, 8),
    )

    presentation_data = Presentation.model_validate(result["data"])

    builder = PresentationBuilder()
    file_id = str(uuid.uuid4())
    output_path = os.path.join("app", "storage", "exports", f"{file_id}.pptx")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    builder.build(presentation_data, output_path)

    return StandardResponse(
        data=presentation_data,
        metadata={"download_url": f"/api/v1/generate/presentation/download/{file_id}"},
    )


@router.get("/download/{file_id}")
async def download_presentation(file_id: str):
    """Download a generated PPTX file."""
    file_path = os.path.join("app", "storage", "exports", f"{file_id}.pptx")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Presentation file not found")
    return FileResponse(
        path=file_path,
        filename=f"presentation_{file_id}.pptx",
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
    )
