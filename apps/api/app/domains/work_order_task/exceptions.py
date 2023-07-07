"""Domain-specific exceptions for WorkOrderTask."""

from __future__ import annotations

from uuid import UUID

from app.core.errors import DomainError, NotFoundError


class WorkOrderTaskError(DomainError):
    """Base exception for work_order_task operations."""

    domain = "work_order_task"


class WorkOrderTaskNotFoundError(NotFoundError, WorkOrderTaskError):
    """Raised when a work_order_task record cannot be located."""

    def __init__(self, entity_id: UUID) -> None:
        super().__init__(
            resource="work_order_task",
            identifier=str(entity_id),
            message=f"WorkOrderTask {entity_id} was not found",
        )


class WorkOrderTaskValidationError(WorkOrderTaskError):
    """Raised when work_order_task business rules are violated."""

    def __init__(self, message: str, *, code: str = "validation_error") -> None:
        super().__init__(message=message, code=code)


class WorkOrderTaskConflictError(WorkOrderTaskError):
    """Raised when an operation conflicts with current work_order_task state."""

    def __init__(self, message: str, *, code: str = "conflict") -> None:
        super().__init__(message=message, code=code)


class WorkOrderTaskPermissionError(WorkOrderTaskError):
    """Raised when caller lacks permission for work_order_task action."""

    def __init__(self, action: str) -> None:
        super().__init__(
            message=f"Permission denied for {action} on work_order_task",
            code="permission_denied",
        )


class WorkOrderTaskStateError(WorkOrderTaskError):
    """Raised when an operation is invalid for the current work_order_task state."""

    def __init__(self, current: str, action: str) -> None:
        super().__init__(
            message=f"Cannot {action} while work_order_task is in status '{current}'",
            code="invalid_state",
        )
        self.current = current
        self.action = action


class WorkOrderTaskTenantScopeError(WorkOrderTaskError):
    """Raised when tenant context is missing or mismatched."""

    def __init__(self, message: str = "Tenant scope violation") -> None:
        super().__init__(message=message, code="tenant_scope_error")


def not_found(entity_id: UUID) -> WorkOrderTaskNotFoundError:
    """Factory for consistent not-found exceptions."""
    return WorkOrderTaskNotFoundError(entity_id)


def validation(message: str, *, code: str = "validation_error") -> WorkOrderTaskValidationError:
    """Factory for validation failures."""
    return WorkOrderTaskValidationError(message, code=code)
