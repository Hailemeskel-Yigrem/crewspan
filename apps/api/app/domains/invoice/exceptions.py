"""Domain-specific exceptions for Invoice."""

from __future__ import annotations

from uuid import UUID

from app.core.errors import DomainError, NotFoundError


class InvoiceError(DomainError):
    """Base exception for invoice operations."""

    domain = "invoice"


class InvoiceNotFoundError(NotFoundError, InvoiceError):
    """Raised when a invoice record cannot be located."""

    def __init__(self, entity_id: UUID) -> None:
        super().__init__(
            resource="invoice",
            identifier=str(entity_id),
            message=f"Invoice {entity_id} was not found",
        )


class InvoiceValidationError(InvoiceError):
    """Raised when invoice business rules are violated."""

    def __init__(self, message: str, *, code: str = "validation_error") -> None:
        super().__init__(message=message, code=code)


class InvoiceConflictError(InvoiceError):
    """Raised when an operation conflicts with current invoice state."""

    def __init__(self, message: str, *, code: str = "conflict") -> None:
        super().__init__(message=message, code=code)


class InvoicePermissionError(InvoiceError):
    """Raised when caller lacks permission for invoice action."""

    def __init__(self, action: str) -> None:
        super().__init__(
            message=f"Permission denied for {action} on invoice",
            code="permission_denied",
        )


class InvoiceStateError(InvoiceError):
    """Raised when an operation is invalid for the current invoice state."""

    def __init__(self, current: str, action: str) -> None:
        super().__init__(
            message=f"Cannot {action} while invoice is in status '{current}'",
            code="invalid_state",
        )
        self.current = current
        self.action = action


class InvoiceTenantScopeError(InvoiceError):
    """Raised when tenant context is missing or mismatched."""

    def __init__(self, message: str = "Tenant scope violation") -> None:
        super().__init__(message=message, code="tenant_scope_error")


def not_found(entity_id: UUID) -> InvoiceNotFoundError:
    """Factory for consistent not-found exceptions."""
    return InvoiceNotFoundError(entity_id)


def validation(message: str, *, code: str = "validation_error") -> InvoiceValidationError:
    """Factory for validation failures."""
    return InvoiceValidationError(message, code=code)
