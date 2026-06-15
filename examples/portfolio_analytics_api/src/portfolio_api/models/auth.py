"""Auth-related models."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class Token(BaseModel):
    """Response body of POST /token."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    """Decoded JWT payload — internal use, never serialized to clients."""

    model_config = ConfigDict(extra="ignore")

    sub: str = Field(description="Subject (username)")
    scopes: list[str] = Field(default_factory=list)


class User(BaseModel):
    """A user record. The capstone keeps a hardcoded demo table; in a real app
    this would come from a UserRepo."""

    model_config = ConfigDict(extra="forbid")

    username: str
    full_name: str | None = None
    disabled: bool = False
    scopes: list[str] = Field(default_factory=list)
