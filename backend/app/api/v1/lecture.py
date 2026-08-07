"""
NEXUS EDU — Lecture Generation Router.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dependencies import RequireActiveUser, UserWorkspace, get_ai_orchestrator
from app.schemas.api import GeneratePayload, StandardResponse
from app.schemas.lecture_notes import LectureNotes

router = APIRouter(prefix="/generate/lecture", tags=["Generation"])


@router.post("", response_model=StandardResponse[LectureNotes])
async def generate_lecture(
    request: GeneratePayload,
    user: RequireActiveUser,
    workspace_id: UserWorkspace,
    orchestrator=Depends(get_ai_orchestrator),
):
    """Generate comprehensive lecture notes for a topic."""
    result = await orchestrator.execute(
        user_id=user.id,
        course_id=workspace_id,
        action_type="generate_lecture",
        topic=request.topic,
        additional_instructions=request.additional_instructions,
    )
    return StandardResponse(data=LectureNotes.model_validate(result["data"]))
