"""
NEXUS EDU — Question Paper Generation Router.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dependencies import RequireActiveUser, UserWorkspace, get_ai_orchestrator
from app.schemas.api import GeneratePayload, StandardResponse
from app.schemas.question_paper import QuestionPaper

router = APIRouter(prefix="/generate/question-paper", tags=["Generation"])


@router.post("", response_model=StandardResponse[QuestionPaper])
async def generate_question_paper(
    request: GeneratePayload,
    user: RequireActiveUser,
    workspace_id: UserWorkspace,
    orchestrator=Depends(get_ai_orchestrator),
):
    """Generate a question paper with MCQs and short-answer questions."""
    result = await orchestrator.execute(
        user_id=user.id,
        course_id=workspace_id,
        action_type="generate_question_paper",
        topic=request.topic,
        additional_instructions=request.additional_instructions,
    )
    return StandardResponse(data=QuestionPaper.model_validate(result["data"]))
