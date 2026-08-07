"""
NEXUS EDU — Authentication Router.

Handles user registration, login, and JWT token issuance.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
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

_DEBUG_LOG = Path(__file__).resolve().parents[4] / "debug-74d681.log"


def _agent_log(hypothesis_id: str, location: str, message: str, data: dict) -> None:
    # #region agent log
    try:
        payload = {
            "sessionId": "74d681",
            "hypothesisId": hypothesis_id,
            "location": location,
            "message": message,
            "data": data,
            "timestamp": int(time.time() * 1000),
        }
        with _DEBUG_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload) + "\n")
    except Exception:
        pass
    # #endregion


@router.post("/register", response_model=StandardResponse[UserRead])
async def register(
    user_in: UserCreate,
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
):
    """Register a new user."""
    # #region agent log
    _agent_log(
        "C",
        "auth.py:register:entry",
        "register called",
        {"email": user_in.email, "passwordLen": len(user_in.password), "fullNameLen": len(user_in.full_name)},
    )
    # #endregion
    try:
        existing_user = await user_repo.get_by_email(user_in.email)
        # #region agent log
        _agent_log(
            "B",
            "auth.py:register:after_email_lookup",
            "duplicate check completed",
            {"email": user_in.email, "existingUser": existing_user is not None},
        )
        # #endregion
    except Exception as exc:
        # #region agent log
        _agent_log(
            "A",
            "auth.py:register:email_lookup_error",
            "database query failed during duplicate check",
            {"email": user_in.email, "errorType": type(exc).__name__, "error": str(exc)[:500]},
        )
        # #endregion
        raise

    if existing_user:
        raise ResourceConflictError("Email already registered")

    user = User(
        email=user_in.email.lower(),  # Normalize email to lowercase
        full_name=user_in.full_name,
        hashed_password=get_password_hash(user_in.password),
    )
    try:
        user = await user_repo.create(user)
        await user_repo._session.refresh(user)
        # #region agent log
        _agent_log(
            "B",
            "auth.py:register:success",
            "user created",
            {"userId": str(user.id), "email": user.email},
        )
        # #endregion
    except Exception as exc:
        # #region agent log
        _agent_log(
            "B",
            "auth.py:register:create_error",
            "user insert failed",
            {"email": user_in.email, "errorType": type(exc).__name__, "error": str(exc)[:500]},
        )
        # #endregion
        raise

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
