"""Shared error types, HTTP mapping, and FastAPI exception handlers."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import structlog

logger = structlog.get_logger(__name__)


class DomainError(Exception):
    """Base class for business rule violations."""

    def __init__(self, message: str, *, code: str = "domain_error", details: dict[str, Any] | None = None) -> None:
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(message)


class NotFoundError(DomainError):
    def __init__(self, *, resource: str, identifier: str, message: str) -> None:
        super().__init__(message, code="not_found", details={"resource": resource, "identifier": identifier})
        self.resource = resource
        self.identifier = identifier


class ValidationAppError(DomainError):
    def __init__(self, message: str, *, field: str | None = None) -> None:
        details = {"field": field} if field else {}
        super().__init__(message, code="validation_error", details=details)


class AuthorizationError(DomainError):
    def __init__(self, message: str = "Permission denied") -> None:
        super().__init__(message, code="permission_denied")


class ConflictError(DomainError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="conflict")


def _error_body(exc: DomainError) -> dict[str, Any]:
    body: dict[str, Any] = {"code": exc.code, "message": exc.message}
    if exc.details:
        body["details"] = exc.details
    return body


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(NotFoundError)
    async def not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
        logger.info("api.not_found", resource=exc.resource, identifier=exc.identifier)
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=_error_body(exc))

    @app.exception_handler(AuthorizationError)
    async def authz_handler(request: Request, exc: AuthorizationError) -> JSONResponse:
        return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content=_error_body(exc))

    @app.exception_handler(ConflictError)
    async def conflict_handler(request: Request, exc: ConflictError) -> JSONResponse:
        return JSONResponse(status_code=status.HTTP_409_CONFLICT, content=_error_body(exc))

    @app.exception_handler(DomainError)
    async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
        status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
        if exc.code == "conflict":
            status_code = status.HTTP_409_CONFLICT
        elif exc.code == "permission_denied":
            status_code = status.HTTP_403_FORBIDDEN
        logger.warning("api.domain_error", code=exc.code, message=exc.message)
        return JSONResponse(status_code=status_code, content=_error_body(exc))

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        errors = exc.errors()
        logger.info("api.validation_error", count=len(errors))
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "code": "validation_error",
                "message": "Request validation failed",
                "details": {"errors": errors},
            },
        )
