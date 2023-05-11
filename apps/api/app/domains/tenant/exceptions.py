"""Domain-specific exceptions for Tenant."""

from __future__ import annotations

from uuid import UUID

from app.core.errors import DomainError, NotFoundError


class TenantError(DomainError):
    """Base exception for tenant operations."""

    domain = "tenant"


class TenantNotFoundError(NotFoundError, TenantError):
    """Raised when a tenant record cannot be located."""

    def __init__(self, entity_id: UUID) -> None:
        super().__init__(
            resource="tenant",
            identifier=str(entity_id),
            message=f"Tenant {entity_id} was not found",
        )


class TenantValidationError(TenantError):
    """Raised when tenant business rules are violated."""

    def __init__(self, message: str, *, code: str = "validation_error") -> None:
        super().__init__(message=message, code=code)


class TenantConflictError(TenantError):
    """Raised when an operation conflicts with current tenant state."""

    def __init__(self, message: str, *, code: str = "conflict") -> None:
        super().__init__(message=message, code=code)


class TenantPermissionError(TenantError):
    """Raised when caller lacks permission for tenant action."""

    def __init__(self, action: str) -> None:
        super().__init__(
            message=f"Permission denied for {action} on tenant",
            code="permission_denied",
        )


class TenantStateError(TenantError):
    """Raised when an operation is invalid for the current tenant state."""

    def __init__(self, current: str, action: str) -> None:
        super().__init__(
            message=f"Cannot {action} while tenant is in status '{current}'",
            code="invalid_state",
        )
        self.current = current
        self.action = action


class TenantTenantScopeError(TenantError):
    """Raised when tenant context is missing or mismatched."""

    def __init__(self, message: str = "Tenant scope violation") -> None:
        super().__init__(message=message, code="tenant_scope_error")


def not_found(entity_id: UUID) -> TenantNotFoundError:
    """Factory for consistent not-found exceptions."""
    return TenantNotFoundError(entity_id)


def validation(message: str, *, code: str = "validation_error") -> TenantValidationError:
    """Factory for validation failures."""
    return TenantValidationError(message, code=code)
