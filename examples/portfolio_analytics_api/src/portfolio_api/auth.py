"""OAuth2 password + JWT — mirrors notebooks 5.1 and 5.2."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from portfolio_api.models.auth import TokenData, User
from portfolio_api.settings import Settings, get_settings

# pbkdf2_sha256 is intentional: bcrypt 5.x is incompatible with passlib 1.7.x,
# and the curriculum uses pbkdf2 throughout (notebook 5.1).
_pwd_ctx = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

# Demo user table — in a real app this would live in a UserRepo. Passwords are
# hashed at startup so the file doesn't carry plaintext.
_DEMO_USERS: dict[str, dict] = {
    "alice": {
        "username": "alice",
        "full_name": "Alice Adams",
        "hashed_password": _pwd_ctx.hash("alice-secret"),
        "disabled": False,
        "scopes": ["portfolios:read", "portfolios:write"],
    },
    "bob": {
        "username": "bob",
        "full_name": "Bob Brown",
        "hashed_password": _pwd_ctx.hash("bob-secret"),
        "disabled": False,
        "scopes": ["portfolios:read"],
    },
}

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/auth/token", auto_error=False)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_ctx.verify(plain, hashed)


def authenticate_user(username: str, password: str) -> User | None:
    record = _DEMO_USERS.get(username)
    if record is None or record["disabled"]:
        return None
    if not verify_password(password, record["hashed_password"]):
        return None
    return User(
        username=record["username"],
        full_name=record["full_name"],
        disabled=record["disabled"],
        scopes=record["scopes"],
    )


def create_access_token(
    *, subject: str, scopes: list[str], settings: Settings, now: datetime | None = None
) -> tuple[str, int]:
    """Return (token, expires_in_seconds)."""
    now = now or datetime.now(timezone.utc)
    expires = now + timedelta(seconds=settings.access_token_ttl_seconds)
    payload = {
        "sub": subject,
        "scopes": scopes,
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "iat": int(now.timestamp()),
        "exp": int(expires.timestamp()),
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return token, settings.access_token_ttl_seconds


def decode_token(token: str, settings: Settings) -> TokenData:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            audience=settings.jwt_audience,
            issuer=settings.jwt_issuer,
        )
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"invalid token: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    sub = payload.get("sub")
    if not isinstance(sub, str):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="token missing sub",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return TokenData(sub=sub, scopes=payload.get("scopes", []))


def get_current_user(
    token: Annotated[str | None, Depends(oauth2_scheme)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> User:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    data = decode_token(token, settings)
    record = _DEMO_USERS.get(data.sub)
    if record is None or record["disabled"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="unknown or disabled user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return User(
        username=record["username"],
        full_name=record["full_name"],
        disabled=record["disabled"],
        scopes=data.scopes,
    )


def require_scope(scope: str):
    """Dependency factory: return a dep that 403s if the user lacks `scope`."""

    def _checker(user: Annotated[User, Depends(get_current_user)]) -> User:
        if scope not in user.scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"missing required scope: {scope}",
            )
        return user

    return _checker
