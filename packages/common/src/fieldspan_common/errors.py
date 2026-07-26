"""Shared error types for Fieldspan services."""

from __future__ import annotations


class FieldspanError(Exception):
    """Base exception for Fieldspan platform errors."""

    def __init__(self, message: str, *, code: str = "fieldspan_error") -> None:
        self.message = message
        self.code = code
        super().__init__(message)


class NotFoundError(FieldspanError):
    """Raised when a requested resource does not exist."""

    def __init__(self, *, resource: str, identifier: str) -> None:
        self.resource = resource
        self.identifier = identifier
        super().__init__(
            message=f"{resource} '{identifier}' was not found",
            code="not_found",
        )


class ValidationError(FieldspanError):
    """Raised when input fails validation."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="validation_error")


class TenantIsolationError(FieldspanError):
    """Raised when a cross-tenant access is attempted."""

    def __init__(self, *, tenant_id: str, resource: str) -> None:
        super().__init__(
            message=f"Tenant {tenant_id} cannot access {resource}",
            code="tenant_isolation_violation",
        )
