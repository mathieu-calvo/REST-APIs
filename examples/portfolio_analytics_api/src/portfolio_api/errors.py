"""Domain error hierarchy + handlers — mirrors notebook 6.1."""
from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class DomainError(Exception):
    """Base of the app's domain-error hierarchy. The handler maps each subclass
    to a stable error envelope so clients see one shape, not three."""

    status_code: int = status.HTTP_400_BAD_REQUEST
    code: str = "domain_error"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotFoundError(DomainError):
    status_code = status.HTTP_404_NOT_FOUND
    code = "not_found"


class ConflictError(DomainError):
    status_code = status.HTTP_409_CONFLICT
    code = "conflict"


def _envelope(*, code: str, message: str, details=None) -> dict:
    out = {"error": {"code": code, "message": message}}
    if details is not None:
        out["error"]["details"] = details
    return out


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def _domain(request: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_envelope(code=exc.code, message=exc.message),
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        # Map HTTP status codes to stable error codes for the few we raise directly.
        mapping = {
            status.HTTP_401_UNAUTHORIZED: "unauthenticated",
            status.HTTP_403_FORBIDDEN: "forbidden",
            status.HTTP_404_NOT_FOUND: "not_found",
            status.HTTP_409_CONFLICT: "conflict",
            status.HTTP_429_TOO_MANY_REQUESTS: "rate_limited",
        }
        code = mapping.get(exc.status_code, "http_error")
        # Preserve WWW-Authenticate if the original exception set it.
        headers = exc.headers or None
        return JSONResponse(
            status_code=exc.status_code,
            content=_envelope(code=code, message=str(exc.detail)),
            headers=headers,
        )

    @app.exception_handler(RequestValidationError)
    async def _validation(request: Request, exc: RequestValidationError) -> JSONResponse:
        # Pydantic's structured errors are rich; surface them as `details`
        # while keeping the envelope consistent.
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=_envelope(
                code="validation_error",
                message="request payload failed validation",
                details=exc.errors(),
            ),
        )
