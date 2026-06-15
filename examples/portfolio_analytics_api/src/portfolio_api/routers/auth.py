"""Auth endpoints: POST /token, GET /me."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from portfolio_api.auth import (
    authenticate_user,
    create_access_token,
    get_current_user,
)
from portfolio_api.models.auth import Token, User
from portfolio_api.settings import Settings, get_settings

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token", response_model=Token, summary="OAuth2 password grant")
def login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    settings: Annotated[Settings, Depends(get_settings)],
) -> Token:
    user = authenticate_user(form.username, form.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # If the request asked for scopes, restrict to ones the user actually has.
    requested = set(form.scopes) if form.scopes else set(user.scopes)
    granted = sorted(requested & set(user.scopes))
    token, expires_in = create_access_token(
        subject=user.username, scopes=granted, settings=settings
    )
    return Token(access_token=token, expires_in=expires_in)


@router.get("/me", response_model=User, summary="Current authenticated user")
def me(user: Annotated[User, Depends(get_current_user)]) -> User:
    return user
