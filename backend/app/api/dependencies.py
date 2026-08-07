"""
NEXUS EDU — API Dependencies.

FastAPI dependency injection providers. Ensures routers remain thin
by cleanly injecting services, repositories, and context.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from typing import Annotated

import jwt
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.exceptions import CredentialsException, PermissionDeniedException
from app.database.session import get_db_session
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.api import TokenData

# OAuth2 scheme configures Swagger UI to send tokens automatically
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_user_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)]
) -> UserRepository:
    """Provide the UserRepository."""
    return UserRepository(session)


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> User:
    """
    Validate the JWT token and return the current user.
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        user_id_str: str | None = payload.get("sub")
        if user_id_str is None:
            raise CredentialsException("Token missing subject claim")
            
        token_data = TokenData(sub=user_id_str, role=payload.get("role"))
    except jwt.InvalidTokenError:
        raise CredentialsException("Invalid or expired token")

    try:
        user_id = uuid.UUID(token_data.sub)
    except ValueError:
        raise CredentialsException("Invalid user ID format in token")

    user = await user_repo.get_by_id(user_id)
    if user is None or not user.is_active:
        raise CredentialsException("User not found or inactive")

    return user


class RoleChecker:
    """Dependency class to enforce role-based access control."""
    def __init__(self, allowed_roles: list[str]) -> None:
        self.allowed_roles = allowed_roles

    def __call__(self, user: Annotated[User, Depends(get_current_user)]) -> User:
        if user.role not in self.allowed_roles:
            raise PermissionDeniedException(
                f"Role '{user.role}' lacks permission for this action."
            )
        return user


# Common Dependency Aliases
RequireActiveUser = Annotated[User, Depends(get_current_user)]
RequireAdmin = Annotated[User, Depends(RoleChecker(["admin"]))]

async def resolve_course_id(
    user_id: uuid.UUID,
    db: AsyncSession,
    provided_course_id: uuid.UUID | str | None = None
) -> uuid.UUID:
    """
    Resolve the target course context.
    If no course_id is provided, fetch the user's most recent workspace or create a default one.
    """
    if provided_course_id:
        try:
            return uuid.UUID(str(provided_course_id))
        except ValueError:
            # If the user left Swagger's default "string" in the field, gracefully 
            # ignore it and fall back to auto-resolving the workspace.
            pass
        
    from sqlalchemy import select
    from app.models.course import Course
    
    # Fetch most recently updated active course
    stmt = (
        select(Course)
        .where(Course.owner_id == user_id, Course.is_active == True)
        .order_by(Course.updated_at.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    course = result.scalar_one_or_none()
    
    if course:
        return course.id
        
    # Auto-create a default workspace if the user has no courses
    default_course = Course(
        owner_id=user_id,
        name="My Workspace",
        description="Auto-generated default workspace",
    )
    db.add(default_course)
    await db.commit()
    await db.refresh(default_course)
    return default_course.id

async def get_user_workspace(
    user: Annotated["User", Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> uuid.UUID:
    """
    FastAPI dependency: resolves the authenticated user's active workspace UUID.
    Auto-creates a default workspace if the user has no courses yet.
    Routers inject this instead of asking the client for course_id.
    """
    return await resolve_course_id(user.id, db)

# Annotated alias for cleaner router signatures
UserWorkspace = Annotated[uuid.UUID, Depends(get_user_workspace)]


async def get_latest_conversation(
    user: Annotated["User", Depends(get_current_user)],
    workspace_id: Annotated[uuid.UUID, Depends(get_user_workspace)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> uuid.UUID | None:
    """
    FastAPI dependency: returns the UUID of the user's most recently updated
    active conversation, or None if the user has never chatted before.
    The orchestrator will create a new conversation when None is received.
    """
    from sqlalchemy import select
    from app.models.conversation import Conversation

    stmt = (
        select(Conversation.id)
        .where(
            Conversation.user_id == user.id,
            Conversation.course_id == workspace_id,
            Conversation.is_deleted == False,
        )
        .order_by(Conversation.updated_at.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


# The pipeline is stateless and thread-safe except for some cached models.
# It should act as a singleton per app lifecycle.
_rag_pipeline_instance = None

async def get_rag_pipeline(
    settings: Annotated[Settings, Depends(get_settings)]
):
    """Provide the RAGPipeline as a singleton."""
    global _rag_pipeline_instance
    if _rag_pipeline_instance is None:
        from app.ai.rag.pipeline import RAGPipeline
        _rag_pipeline_instance = RAGPipeline(settings)
    return _rag_pipeline_instance

async def get_ai_orchestrator(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    pipeline=Depends(get_rag_pipeline)
):
    """Provide the AIOrchestrator."""
    from app.ai.orchestrator import AIOrchestrator
    from app.ai.llm.llm_service import LLMService
    from app.services.lecture.lecture_generation_service import LectureGenerationService
    from app.services.ppt.presentation_generation_service import PresentationGenerationService
    from app.services.question_paper.question_paper_generation_service import QuestionPaperGenerationService
    from app.services.analysis.summary_generation_service import SummaryGenerationService
    from app.services.analysis.paper_analysis_service import PaperAnalysisService
    from app.services.chat.chat_generation_service import ChatGenerationService

    orchestrator = AIOrchestrator(session)
    llm = LLMService()

    # Register services
    orchestrator.register_service("generate_lecture", LectureGenerationService(pipeline, llm).generate, "lecture_generation")
    orchestrator.register_service("generate_presentation", PresentationGenerationService(pipeline, llm).generate, "presentation_generation")
    orchestrator.register_service("generate_question_paper", QuestionPaperGenerationService(pipeline, llm).generate, "question_paper_generation")
    orchestrator.register_service("generate_summary", SummaryGenerationService(pipeline, llm).generate, "summary_generation")
    orchestrator.register_service("generate_paper_analysis", PaperAnalysisService(pipeline, llm).generate, "paper_analysis_generation")
    orchestrator.register_service("chat", ChatGenerationService(pipeline, llm).generate, "chat_generation")

    return orchestrator


