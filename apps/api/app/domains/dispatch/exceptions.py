"""Domain-specific exceptions for Dispatch."""

from __future__ import annotations

from uuid import UUID

from app.core.errors import DomainError, NotFoundError


class DispatchError(DomainError):
    """Base exception for dispatch operations."""

    domain = "dispatch"


class DispatchNotFoundError(NotFoundError, DispatchError):
    """Raised when a dispatch record cannot be located."""

    def __init__(self, entity_id: UUID) -> None:
        super().__init__(
            resource="dispatch",
            identifier=str(entity_id),
            message=f"Dispatch {entity_id} was not found",
        )


class DispatchValidationError(DispatchError):
    """Raised when dispatch business rules are violated."""

    def __init__(self, message: str, *, code: str = "validation_error") -> None:
        super().__init__(message=message, code=code)


class DispatchConflictError(DispatchError):
    """Raised when an operation conflicts with current dispatch state."""

    def __init__(self, message: str, *, code: str = "conflict") -> None:
        super().__init__(message=message, code=code)


class DispatchPermissionError(DispatchError):
    """Raised when caller lacks permission for dispatch action."""

    def __init__(self, action: str) -> None:
        super().__init__(
            message=f"Permission denied for {action} on dispatch",
            code="permission_denied",
        )


class DispatchStateError(DispatchError):
    """Raised when an operation is invalid for the current dispatch state."""

    def __init__(self, current: str, action: str) -> None:
        super().__init__(
            message=f"Cannot {action} while dispatch is in status '{current}'",
            code="invalid_state",
        )
        self.current = current
        self.action = action


class DispatchTenantScopeError(DispatchError):
    """Raised when tenant context is missing or mismatched."""

    def __init__(self, message: str = "Tenant scope violation") -> None:
        super().__init__(message=message, code="tenant_scope_error")


def not_found(entity_id: UUID) -> DispatchNotFoundError:
    """Factory for consistent not-found exceptions."""
    return DispatchNotFoundError(entity_id)


def validation(message: str, *, code: str = "validation_error") -> DispatchValidationError:
    """Factory for validation failures."""
    return DispatchValidationError(message, code=code)
