"""Domain-specific exceptions for InventoryLocation."""

from __future__ import annotations

from uuid import UUID

from app.core.errors import DomainError, NotFoundError


class InventoryLocationError(DomainError):
    """Base exception for inventory_location operations."""

    domain = "inventory_location"


class InventoryLocationNotFoundError(NotFoundError, InventoryLocationError):
    """Raised when a inventory_location record cannot be located."""

    def __init__(self, entity_id: UUID) -> None:
        super().__init__(
            resource="inventory_location",
            identifier=str(entity_id),
            message=f"InventoryLocation {entity_id} was not found",
        )


class InventoryLocationValidationError(InventoryLocationError):
    """Raised when inventory_location business rules are violated."""

    def __init__(self, message: str, *, code: str = "validation_error") -> None:
        super().__init__(message=message, code=code)


class InventoryLocationConflictError(InventoryLocationError):
    """Raised when an operation conflicts with current inventory_location state."""

    def __init__(self, message: str, *, code: str = "conflict") -> None:
        super().__init__(message=message, code=code)


class InventoryLocationPermissionError(InventoryLocationError):
    """Raised when caller lacks permission for inventory_location action."""

    def __init__(self, action: str) -> None:
        super().__init__(
            message=f"Permission denied for {action} on inventory_location",
            code="permission_denied",
        )


class InventoryLocationStateError(InventoryLocationError):
    """Raised when an operation is invalid for the current inventory_location state."""

    def __init__(self, current: str, action: str) -> None:
        super().__init__(
            message=f"Cannot {action} while inventory_location is in status '{current}'",
            code="invalid_state",
        )
        self.current = current
        self.action = action


class InventoryLocationTenantScopeError(InventoryLocationError):
    """Raised when tenant context is missing or mismatched."""

    def __init__(self, message: str = "Tenant scope violation") -> None:
        super().__init__(message=message, code="tenant_scope_error")


def not_found(entity_id: UUID) -> InventoryLocationNotFoundError:
    """Factory for consistent not-found exceptions."""
    return InventoryLocationNotFoundError(entity_id)


def validation(message: str, *, code: str = "validation_error") -> InventoryLocationValidationError:
    """Factory for validation failures."""
    return InventoryLocationValidationError(message, code=code)
