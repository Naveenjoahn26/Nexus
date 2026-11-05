"""
NEXUS EDU — Authentication Router.

Handles user registration, login, and JWT token issuance.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.api.dependencies import get_current_user, get_user_repository
from app.core.exceptions import CredentialsException, ResourceConflictError
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.api import StandardResponse, Token, UserCreate, UserRead

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=StandardResponse[UserRead])
async def register(
    user_in: UserCreate,
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
):
    """Register a new user."""
    existing_user = await user_repo.get_by_email(user_in.email)
    if existing_user:
        raise ResourceConflictError("Email already registered")

    user = User(
        email=user_in.email.lower(),  # Normalize email to lowercase
        full_name=user_in.full_name,
        hashed_password=get_password_hash(user_in.password),
    )
    user = await user_repo.create(user)
    await user_repo._session.refresh(user)

    return StandardResponse(data=UserRead.model_validate(user))


@router.post("/login", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
):
    """
    OAuth2 compatible token login, getting an access token for future requests.
    Note: Returns a raw Token to comply with OAuth2 specification.
    """
    user = await user_repo.get_by_email(form_data.username.lower())
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise CredentialsException("Incorrect email or password")
        
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role}
    )
    return Token(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=StandardResponse[UserRead])
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get the profile of the currently authenticated user."""
    return StandardResponse(data=current_user)
