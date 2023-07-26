"""Domain-specific exceptions for Schedule."""

from __future__ import annotations

from uuid import UUID

from app.core.errors import DomainError, NotFoundError


class ScheduleError(DomainError):
    """Base exception for schedule operations."""

    domain = "schedule"


class ScheduleNotFoundError(NotFoundError, ScheduleError):
    """Raised when a schedule record cannot be located."""

    def __init__(self, entity_id: UUID) -> None:
        super().__init__(
            resource="schedule",
            identifier=str(entity_id),
            message=f"Schedule {entity_id} was not found",
        )


class ScheduleValidationError(ScheduleError):
    """Raised when schedule business rules are violated."""

    def __init__(self, message: str, *, code: str = "validation_error") -> None:
        super().__init__(message=message, code=code)


class ScheduleConflictError(ScheduleError):
    """Raised when an operation conflicts with current schedule state."""

    def __init__(self, message: str, *, code: str = "conflict") -> None:
        super().__init__(message=message, code=code)


class SchedulePermissionError(ScheduleError):
    """Raised when caller lacks permission for schedule action."""

    def __init__(self, action: str) -> None:
        super().__init__(
            message=f"Permission denied for {action} on schedule",
            code="permission_denied",
        )


class ScheduleStateError(ScheduleError):
    """Raised when an operation is invalid for the current schedule state."""

    def __init__(self, current: str, action: str) -> None:
        super().__init__(
            message=f"Cannot {action} while schedule is in status '{current}'",
            code="invalid_state",
        )
        self.current = current
        self.action = action


class ScheduleTenantScopeError(ScheduleError):
    """Raised when tenant context is missing or mismatched."""

    def __init__(self, message: str = "Tenant scope violation") -> None:
        super().__init__(message=message, code="tenant_scope_error")


def not_found(entity_id: UUID) -> ScheduleNotFoundError:
    """Factory for consistent not-found exceptions."""
    return ScheduleNotFoundError(entity_id)


def validation(message: str, *, code: str = "validation_error") -> ScheduleValidationError:
    """Factory for validation failures."""
    return ScheduleValidationError(message, code=code)
