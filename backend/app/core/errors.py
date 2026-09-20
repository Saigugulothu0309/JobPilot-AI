"""Minimal application-level exception handling."""

from fastapi import Request
from fastapi.responses import JSONResponse


class ApplicationError(Exception):
    """Base exception for future application-level errors."""

    def __init__(self, detail: str, status_code: int = 400) -> None:
        self.detail = detail
        self.status_code = status_code
        super().__init__(detail)


def application_error_handler(_: Request, exc: Exception) -> JSONResponse:
    """Convert known application errors into stable JSON responses."""
    if isinstance(exc, ApplicationError):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
