"""Domain-specific exceptions for User."""

from __future__ import annotations

from uuid import UUID

from app.core.errors import DomainError, NotFoundError


class UserError(DomainError):
    """Base exception for user operations."""

    domain = "user"


class UserNotFoundError(NotFoundError, UserError):
    """Raised when a user record cannot be located."""

    def __init__(self, entity_id: UUID) -> None:
        super().__init__(
            resource="user",
            identifier=str(entity_id),
            message=f"User {entity_id} was not found",
        )


class UserValidationError(UserError):
    """Raised when user business rules are violated."""

    def __init__(self, message: str, *, code: str = "validation_error") -> None:
        super().__init__(message=message, code=code)


class UserConflictError(UserError):
    """Raised when an operation conflicts with current user state."""

    def __init__(self, message: str, *, code: str = "conflict") -> None:
        super().__init__(message=message, code=code)


class UserPermissionError(UserError):
    """Raised when caller lacks permission for user action."""

    def __init__(self, action: str) -> None:
        super().__init__(
            message=f"Permission denied for {action} on user",
            code="permission_denied",
        )


class UserStateError(UserError):
    """Raised when an operation is invalid for the current user state."""

    def __init__(self, current: str, action: str) -> None:
        super().__init__(
            message=f"Cannot {action} while user is in status '{current}'",
            code="invalid_state",
        )
        self.current = current
        self.action = action


class UserTenantScopeError(UserError):
    """Raised when tenant context is missing or mismatched."""

    def __init__(self, message: str = "Tenant scope violation") -> None:
        super().__init__(message=message, code="tenant_scope_error")


def not_found(entity_id: UUID) -> UserNotFoundError:
    """Factory for consistent not-found exceptions."""
    return UserNotFoundError(entity_id)


def validation(message: str, *, code: str = "validation_error") -> UserValidationError:
    """Factory for validation failures."""
    return UserValidationError(message, code=code)
