"""Domain-specific exceptions for Role."""

from __future__ import annotations

from uuid import UUID

from app.core.errors import DomainError, NotFoundError


class RoleError(DomainError):
    """Base exception for role operations."""

    domain = "role"


class RoleNotFoundError(NotFoundError, RoleError):
    """Raised when a role record cannot be located."""

    def __init__(self, entity_id: UUID) -> None:
        super().__init__(
            resource="role",
            identifier=str(entity_id),
            message=f"Role {entity_id} was not found",
        )


class RoleValidationError(RoleError):
    """Raised when role business rules are violated."""

    def __init__(self, message: str, *, code: str = "validation_error") -> None:
        super().__init__(message=message, code=code)


class RoleConflictError(RoleError):
    """Raised when an operation conflicts with current role state."""

    def __init__(self, message: str, *, code: str = "conflict") -> None:
        super().__init__(message=message, code=code)


class RolePermissionError(RoleError):
    """Raised when caller lacks permission for role action."""

    def __init__(self, action: str) -> None:
        super().__init__(
            message=f"Permission denied for {action} on role",
            code="permission_denied",
        )


class RoleStateError(RoleError):
    """Raised when an operation is invalid for the current role state."""

    def __init__(self, current: str, action: str) -> None:
        super().__init__(
            message=f"Cannot {action} while role is in status '{current}'",
            code="invalid_state",
        )
        self.current = current
        self.action = action


class RoleTenantScopeError(RoleError):
    """Raised when tenant context is missing or mismatched."""

    def __init__(self, message: str = "Tenant scope violation") -> None:
        super().__init__(message=message, code="tenant_scope_error")


def not_found(entity_id: UUID) -> RoleNotFoundError:
    """Factory for consistent not-found exceptions."""
    return RoleNotFoundError(entity_id)


def validation(message: str, *, code: str = "validation_error") -> RoleValidationError:
    """Factory for validation failures."""
    return RoleValidationError(message, code=code)
