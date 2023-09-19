"""Domain-specific exceptions for Notification."""

from __future__ import annotations

from uuid import UUID

from app.core.errors import DomainError, NotFoundError


class NotificationError(DomainError):
    """Base exception for notification operations."""

    domain = "notification"


class NotificationNotFoundError(NotFoundError, NotificationError):
    """Raised when a notification record cannot be located."""

    def __init__(self, entity_id: UUID) -> None:
        super().__init__(
            resource="notification",
            identifier=str(entity_id),
            message=f"Notification {entity_id} was not found",
        )


class NotificationValidationError(NotificationError):
    """Raised when notification business rules are violated."""

    def __init__(self, message: str, *, code: str = "validation_error") -> None:
        super().__init__(message=message, code=code)


class NotificationConflictError(NotificationError):
    """Raised when an operation conflicts with current notification state."""

    def __init__(self, message: str, *, code: str = "conflict") -> None:
        super().__init__(message=message, code=code)


class NotificationPermissionError(NotificationError):
    """Raised when caller lacks permission for notification action."""

    def __init__(self, action: str) -> None:
        super().__init__(
            message=f"Permission denied for {action} on notification",
            code="permission_denied",
        )


class NotificationStateError(NotificationError):
    """Raised when an operation is invalid for the current notification state."""

    def __init__(self, current: str, action: str) -> None:
        super().__init__(
            message=f"Cannot {action} while notification is in status '{current}'",
            code="invalid_state",
        )
        self.current = current
        self.action = action


class NotificationTenantScopeError(NotificationError):
    """Raised when tenant context is missing or mismatched."""

    def __init__(self, message: str = "Tenant scope violation") -> None:
        super().__init__(message=message, code="tenant_scope_error")


def not_found(entity_id: UUID) -> NotificationNotFoundError:
    """Factory for consistent not-found exceptions."""
    return NotificationNotFoundError(entity_id)


def validation(message: str, *, code: str = "validation_error") -> NotificationValidationError:
    """Factory for validation failures."""
    return NotificationValidationError(message, code=code)
