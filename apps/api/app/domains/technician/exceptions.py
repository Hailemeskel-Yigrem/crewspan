"""Domain-specific exceptions for Technician."""

from __future__ import annotations

from uuid import UUID

from app.core.errors import DomainError, NotFoundError


class TechnicianError(DomainError):
    """Base exception for technician operations."""

    domain = "technician"


class TechnicianNotFoundError(NotFoundError, TechnicianError):
    """Raised when a technician record cannot be located."""

    def __init__(self, entity_id: UUID) -> None:
        super().__init__(
            resource="technician",
            identifier=str(entity_id),
            message=f"Technician {entity_id} was not found",
        )


class TechnicianValidationError(TechnicianError):
    """Raised when technician business rules are violated."""

    def __init__(self, message: str, *, code: str = "validation_error") -> None:
        super().__init__(message=message, code=code)


class TechnicianConflictError(TechnicianError):
    """Raised when an operation conflicts with current technician state."""

    def __init__(self, message: str, *, code: str = "conflict") -> None:
        super().__init__(message=message, code=code)


class TechnicianPermissionError(TechnicianError):
    """Raised when caller lacks permission for technician action."""

    def __init__(self, action: str) -> None:
        super().__init__(
            message=f"Permission denied for {action} on technician",
            code="permission_denied",
        )


class TechnicianStateError(TechnicianError):
    """Raised when an operation is invalid for the current technician state."""

    def __init__(self, current: str, action: str) -> None:
        super().__init__(
            message=f"Cannot {action} while technician is in status '{current}'",
            code="invalid_state",
        )
        self.current = current
        self.action = action


class TechnicianTenantScopeError(TechnicianError):
    """Raised when tenant context is missing or mismatched."""

    def __init__(self, message: str = "Tenant scope violation") -> None:
        super().__init__(message=message, code="tenant_scope_error")


def not_found(entity_id: UUID) -> TechnicianNotFoundError:
    """Factory for consistent not-found exceptions."""
    return TechnicianNotFoundError(entity_id)


def validation(message: str, *, code: str = "validation_error") -> TechnicianValidationError:
    """Factory for validation failures."""
    return TechnicianValidationError(message, code=code)
