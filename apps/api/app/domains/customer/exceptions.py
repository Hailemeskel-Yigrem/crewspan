"""Domain-specific exceptions for Customer."""

from __future__ import annotations

from uuid import UUID

from app.core.errors import DomainError, NotFoundError


class CustomerError(DomainError):
    """Base exception for customer operations."""

    domain = "customer"


class CustomerNotFoundError(NotFoundError, CustomerError):
    """Raised when a customer record cannot be located."""

    def __init__(self, entity_id: UUID) -> None:
        super().__init__(
            resource="customer",
            identifier=str(entity_id),
            message=f"Customer {entity_id} was not found",
        )


class CustomerValidationError(CustomerError):
    """Raised when customer business rules are violated."""

    def __init__(self, message: str, *, code: str = "validation_error") -> None:
        super().__init__(message=message, code=code)


class CustomerConflictError(CustomerError):
    """Raised when an operation conflicts with current customer state."""

    def __init__(self, message: str, *, code: str = "conflict") -> None:
        super().__init__(message=message, code=code)


class CustomerPermissionError(CustomerError):
    """Raised when caller lacks permission for customer action."""

    def __init__(self, action: str) -> None:
        super().__init__(
            message=f"Permission denied for {action} on customer",
            code="permission_denied",
        )


class CustomerStateError(CustomerError):
    """Raised when an operation is invalid for the current customer state."""

    def __init__(self, current: str, action: str) -> None:
        super().__init__(
            message=f"Cannot {action} while customer is in status '{current}'",
            code="invalid_state",
        )
        self.current = current
        self.action = action


class CustomerTenantScopeError(CustomerError):
    """Raised when tenant context is missing or mismatched."""

    def __init__(self, message: str = "Tenant scope violation") -> None:
        super().__init__(message=message, code="tenant_scope_error")


def not_found(entity_id: UUID) -> CustomerNotFoundError:
    """Factory for consistent not-found exceptions."""
    return CustomerNotFoundError(entity_id)


def validation(message: str, *, code: str = "validation_error") -> CustomerValidationError:
    """Factory for validation failures."""
    return CustomerValidationError(message, code=code)
