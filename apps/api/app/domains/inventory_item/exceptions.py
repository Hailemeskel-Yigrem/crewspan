"""Domain-specific exceptions for InventoryItem."""

from __future__ import annotations

from uuid import UUID

from app.core.errors import DomainError, NotFoundError


class InventoryItemError(DomainError):
    """Base exception for inventory_item operations."""

    domain = "inventory_item"


class InventoryItemNotFoundError(NotFoundError, InventoryItemError):
    """Raised when a inventory_item record cannot be located."""

    def __init__(self, entity_id: UUID) -> None:
        super().__init__(
            resource="inventory_item",
            identifier=str(entity_id),
            message=f"InventoryItem {entity_id} was not found",
        )


class InventoryItemValidationError(InventoryItemError):
    """Raised when inventory_item business rules are violated."""

    def __init__(self, message: str, *, code: str = "validation_error") -> None:
        super().__init__(message=message, code=code)


class InventoryItemConflictError(InventoryItemError):
    """Raised when an operation conflicts with current inventory_item state."""

    def __init__(self, message: str, *, code: str = "conflict") -> None:
        super().__init__(message=message, code=code)


class InventoryItemPermissionError(InventoryItemError):
    """Raised when caller lacks permission for inventory_item action."""

    def __init__(self, action: str) -> None:
        super().__init__(
            message=f"Permission denied for {action} on inventory_item",
            code="permission_denied",
        )


class InventoryItemStateError(InventoryItemError):
    """Raised when an operation is invalid for the current inventory_item state."""

    def __init__(self, current: str, action: str) -> None:
        super().__init__(
            message=f"Cannot {action} while inventory_item is in status '{current}'",
            code="invalid_state",
        )
        self.current = current
        self.action = action


class InventoryItemTenantScopeError(InventoryItemError):
    """Raised when tenant context is missing or mismatched."""

    def __init__(self, message: str = "Tenant scope violation") -> None:
        super().__init__(message=message, code="tenant_scope_error")


def not_found(entity_id: UUID) -> InventoryItemNotFoundError:
    """Factory for consistent not-found exceptions."""
    return InventoryItemNotFoundError(entity_id)


def validation(message: str, *, code: str = "validation_error") -> InventoryItemValidationError:
    """Factory for validation failures."""
    return InventoryItemValidationError(message, code=code)
