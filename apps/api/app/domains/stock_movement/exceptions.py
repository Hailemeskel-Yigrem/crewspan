"""Domain-specific exceptions for StockMovement."""

from __future__ import annotations

from uuid import UUID

from app.core.errors import DomainError, NotFoundError


class StockMovementError(DomainError):
    """Base exception for stock_movement operations."""

    domain = "stock_movement"


class StockMovementNotFoundError(NotFoundError, StockMovementError):
    """Raised when a stock_movement record cannot be located."""

    def __init__(self, entity_id: UUID) -> None:
        super().__init__(
            resource="stock_movement",
            identifier=str(entity_id),
            message=f"StockMovement {entity_id} was not found",
        )


class StockMovementValidationError(StockMovementError):
    """Raised when stock_movement business rules are violated."""

    def __init__(self, message: str, *, code: str = "validation_error") -> None:
        super().__init__(message=message, code=code)


class StockMovementConflictError(StockMovementError):
    """Raised when an operation conflicts with current stock_movement state."""

    def __init__(self, message: str, *, code: str = "conflict") -> None:
        super().__init__(message=message, code=code)


class StockMovementPermissionError(StockMovementError):
    """Raised when caller lacks permission for stock_movement action."""

    def __init__(self, action: str) -> None:
        super().__init__(
            message=f"Permission denied for {action} on stock_movement",
            code="permission_denied",
        )


class StockMovementStateError(StockMovementError):
    """Raised when an operation is invalid for the current stock_movement state."""

    def __init__(self, current: str, action: str) -> None:
        super().__init__(
            message=f"Cannot {action} while stock_movement is in status '{current}'",
            code="invalid_state",
        )
        self.current = current
        self.action = action


class StockMovementTenantScopeError(StockMovementError):
    """Raised when tenant context is missing or mismatched."""

    def __init__(self, message: str = "Tenant scope violation") -> None:
        super().__init__(message=message, code="tenant_scope_error")


def not_found(entity_id: UUID) -> StockMovementNotFoundError:
    """Factory for consistent not-found exceptions."""
    return StockMovementNotFoundError(entity_id)


def validation(message: str, *, code: str = "validation_error") -> StockMovementValidationError:
    """Factory for validation failures."""
    return StockMovementValidationError(message, code=code)
