"""
NEXUS EDU — Courses API Router.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import RequireActiveUser
from app.database.session import get_db_session
from app.models.course import Course
from app.schemas.api import CourseCreate, CourseRead, StandardResponse

router = APIRouter(prefix="/courses", tags=["Courses"])

@router.post("", response_model=StandardResponse[CourseRead])
async def create_course(
    request: CourseCreate,
    user: RequireActiveUser,
    db: AsyncSession = Depends(get_db_session),
):
    """Create a new course."""
    course = Course(
        owner_id=user.id,
        name=request.name,
        code=request.code,
        description=request.description,
        subject_area=request.subject_area,
        academic_level=request.academic_level,
    )
    db.add(course)
    await db.commit()
    await db.refresh(course)
    
    return StandardResponse(data=CourseRead.model_validate(course))

@router.get("", response_model=StandardResponse[list[CourseRead]])
async def get_courses(
    user: RequireActiveUser,
    db: AsyncSession = Depends(get_db_session),
):
    """List all courses for the user."""
    stmt = select(Course).where(Course.owner_id == user.id, Course.is_active == True)
    result = await db.execute(stmt)
    courses = list(result.scalars().all())
    
    return StandardResponse(data=[CourseRead.model_validate(c) for c in courses])
