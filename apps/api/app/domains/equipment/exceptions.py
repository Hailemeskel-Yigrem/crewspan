"""Domain-specific exceptions for Equipment."""

from __future__ import annotations

from uuid import UUID

from app.core.errors import DomainError, NotFoundError


class EquipmentError(DomainError):
    """Base exception for equipment operations."""

    domain = "equipment"


class EquipmentNotFoundError(NotFoundError, EquipmentError):
    """Raised when a equipment record cannot be located."""

    def __init__(self, entity_id: UUID) -> None:
        super().__init__(
            resource="equipment",
            identifier=str(entity_id),
            message=f"Equipment {entity_id} was not found",
        )


class EquipmentValidationError(EquipmentError):
    """Raised when equipment business rules are violated."""

    def __init__(self, message: str, *, code: str = "validation_error") -> None:
        super().__init__(message=message, code=code)


class EquipmentConflictError(EquipmentError):
    """Raised when an operation conflicts with current equipment state."""

    def __init__(self, message: str, *, code: str = "conflict") -> None:
        super().__init__(message=message, code=code)


class EquipmentPermissionError(EquipmentError):
    """Raised when caller lacks permission for equipment action."""

    def __init__(self, action: str) -> None:
        super().__init__(
            message=f"Permission denied for {action} on equipment",
            code="permission_denied",
        )


class EquipmentStateError(EquipmentError):
    """Raised when an operation is invalid for the current equipment state."""

    def __init__(self, current: str, action: str) -> None:
        super().__init__(
            message=f"Cannot {action} while equipment is in status '{current}'",
            code="invalid_state",
        )
        self.current = current
        self.action = action


class EquipmentTenantScopeError(EquipmentError):
    """Raised when tenant context is missing or mismatched."""

    def __init__(self, message: str = "Tenant scope violation") -> None:
        super().__init__(message=message, code="tenant_scope_error")


def not_found(entity_id: UUID) -> EquipmentNotFoundError:
    """Factory for consistent not-found exceptions."""
    return EquipmentNotFoundError(entity_id)


def validation(message: str, *, code: str = "validation_error") -> EquipmentValidationError:
    """Factory for validation failures."""
    return EquipmentValidationError(message, code=code)
