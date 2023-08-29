"""Domain-specific exceptions for PartsRequest."""

from __future__ import annotations

from uuid import UUID

from app.core.errors import DomainError, NotFoundError


class PartsRequestError(DomainError):
    """Base exception for parts_request operations."""

    domain = "parts_request"


class PartsRequestNotFoundError(NotFoundError, PartsRequestError):
    """Raised when a parts_request record cannot be located."""

    def __init__(self, entity_id: UUID) -> None:
        super().__init__(
            resource="parts_request",
            identifier=str(entity_id),
            message=f"PartsRequest {entity_id} was not found",
        )


class PartsRequestValidationError(PartsRequestError):
    """Raised when parts_request business rules are violated."""

    def __init__(self, message: str, *, code: str = "validation_error") -> None:
        super().__init__(message=message, code=code)


class PartsRequestConflictError(PartsRequestError):
    """Raised when an operation conflicts with current parts_request state."""

    def __init__(self, message: str, *, code: str = "conflict") -> None:
        super().__init__(message=message, code=code)


class PartsRequestPermissionError(PartsRequestError):
    """Raised when caller lacks permission for parts_request action."""

    def __init__(self, action: str) -> None:
        super().__init__(
            message=f"Permission denied for {action} on parts_request",
            code="permission_denied",
        )


class PartsRequestStateError(PartsRequestError):
    """Raised when an operation is invalid for the current parts_request state."""

    def __init__(self, current: str, action: str) -> None:
        super().__init__(
            message=f"Cannot {action} while parts_request is in status '{current}'",
            code="invalid_state",
        )
        self.current = current
        self.action = action


class PartsRequestTenantScopeError(PartsRequestError):
    """Raised when tenant context is missing or mismatched."""

    def __init__(self, message: str = "Tenant scope violation") -> None:
        super().__init__(message=message, code="tenant_scope_error")


def not_found(entity_id: UUID) -> PartsRequestNotFoundError:
    """Factory for consistent not-found exceptions."""
    return PartsRequestNotFoundError(entity_id)


def validation(message: str, *, code: str = "validation_error") -> PartsRequestValidationError:
    """Factory for validation failures."""
    return PartsRequestValidationError(message, code=code)
