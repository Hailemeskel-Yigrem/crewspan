"""Domain-specific exceptions for WorkOrder."""

from __future__ import annotations

from uuid import UUID

from app.core.errors import DomainError, NotFoundError


class WorkOrderError(DomainError):
    """Base exception for work_order operations."""

    domain = "work_order"


class WorkOrderNotFoundError(NotFoundError, WorkOrderError):
    """Raised when a work_order record cannot be located."""

    def __init__(self, entity_id: UUID) -> None:
        super().__init__(
            resource="work_order",
            identifier=str(entity_id),
            message=f"WorkOrder {entity_id} was not found",
        )


class WorkOrderValidationError(WorkOrderError):
    """Raised when work_order business rules are violated."""

    def __init__(self, message: str, *, code: str = "validation_error") -> None:
        super().__init__(message=message, code=code)


class WorkOrderConflictError(WorkOrderError):
    """Raised when an operation conflicts with current work_order state."""

    def __init__(self, message: str, *, code: str = "conflict") -> None:
        super().__init__(message=message, code=code)


class WorkOrderPermissionError(WorkOrderError):
    """Raised when caller lacks permission for work_order action."""

    def __init__(self, action: str) -> None:
        super().__init__(
            message=f"Permission denied for {action} on work_order",
            code="permission_denied",
        )


class WorkOrderStateError(WorkOrderError):
    """Raised when an operation is invalid for the current work_order state."""

    def __init__(self, current: str, action: str) -> None:
        super().__init__(
            message=f"Cannot {action} while work_order is in status '{current}'",
            code="invalid_state",
        )
        self.current = current
        self.action = action


class WorkOrderTenantScopeError(WorkOrderError):
    """Raised when tenant context is missing or mismatched."""

    def __init__(self, message: str = "Tenant scope violation") -> None:
        super().__init__(message=message, code="tenant_scope_error")


def not_found(entity_id: UUID) -> WorkOrderNotFoundError:
    """Factory for consistent not-found exceptions."""
    return WorkOrderNotFoundError(entity_id)


def validation(message: str, *, code: str = "validation_error") -> WorkOrderValidationError:
    """Factory for validation failures."""
    return WorkOrderValidationError(message, code=code)
