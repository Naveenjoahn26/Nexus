"""
NEXUS EDU — Summary Generation Router.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dependencies import RequireActiveUser, UserWorkspace, get_ai_orchestrator
from app.schemas.api import GeneratePayload, StandardResponse
from app.schemas.summary import ContentSummary

router = APIRouter(prefix="/generate/summary", tags=["Generation"])


@router.post("", response_model=StandardResponse[ContentSummary])
async def generate_summary(
    request: GeneratePayload,
    user: RequireActiveUser,
    workspace_id: UserWorkspace,
    orchestrator=Depends(get_ai_orchestrator),
):
    """Generate a structured summary of your uploaded documents."""
    result = await orchestrator.execute(
        user_id=user.id,
        course_id=workspace_id,
        action_type="generate_summary",
        topic=request.topic,
        additional_instructions=request.additional_instructions,
    )
    return StandardResponse(data=ContentSummary.model_validate(result["data"]))
