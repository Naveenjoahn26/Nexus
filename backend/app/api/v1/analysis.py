"""
NEXUS EDU — Paper Analysis Generation Router.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dependencies import RequireActiveUser, UserWorkspace, get_ai_orchestrator
from app.schemas.api import GeneratePayload, StandardResponse
from app.schemas.paper_analysis import PaperAnalysis

router = APIRouter(prefix="/generate/analysis", tags=["Generation"])


@router.post("", response_model=StandardResponse[PaperAnalysis])
async def generate_analysis(
    request: GeneratePayload,
    user: RequireActiveUser,
    workspace_id: UserWorkspace,
    orchestrator=Depends(get_ai_orchestrator),
):
    """Generate a structured analysis of academic papers in your workspace."""
    result = await orchestrator.execute(
        user_id=user.id,
        course_id=workspace_id,
        action_type="generate_paper_analysis",
        topic=request.topic,
        additional_instructions=request.additional_instructions,
    )
    return StandardResponse(data=PaperAnalysis.model_validate(result["data"]))
