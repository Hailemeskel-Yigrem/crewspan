"""Domain-specific exceptions for InvoiceLineItem."""

from __future__ import annotations

from uuid import UUID

from app.core.errors import DomainError, NotFoundError


class InvoiceLineItemError(DomainError):
    """Base exception for invoice_line_item operations."""

    domain = "invoice_line_item"


class InvoiceLineItemNotFoundError(NotFoundError, InvoiceLineItemError):
    """Raised when a invoice_line_item record cannot be located."""

    def __init__(self, entity_id: UUID) -> None:
        super().__init__(
            resource="invoice_line_item",
            identifier=str(entity_id),
            message=f"InvoiceLineItem {entity_id} was not found",
        )


class InvoiceLineItemValidationError(InvoiceLineItemError):
    """Raised when invoice_line_item business rules are violated."""

    def __init__(self, message: str, *, code: str = "validation_error") -> None:
        super().__init__(message=message, code=code)


class InvoiceLineItemConflictError(InvoiceLineItemError):
    """Raised when an operation conflicts with current invoice_line_item state."""

    def __init__(self, message: str, *, code: str = "conflict") -> None:
        super().__init__(message=message, code=code)


class InvoiceLineItemPermissionError(InvoiceLineItemError):
    """Raised when caller lacks permission for invoice_line_item action."""

    def __init__(self, action: str) -> None:
        super().__init__(
            message=f"Permission denied for {action} on invoice_line_item",
            code="permission_denied",
        )


class InvoiceLineItemStateError(InvoiceLineItemError):
    """Raised when an operation is invalid for the current invoice_line_item state."""

    def __init__(self, current: str, action: str) -> None:
        super().__init__(
            message=f"Cannot {action} while invoice_line_item is in status '{current}'",
            code="invalid_state",
        )
        self.current = current
        self.action = action


class InvoiceLineItemTenantScopeError(InvoiceLineItemError):
    """Raised when tenant context is missing or mismatched."""

    def __init__(self, message: str = "Tenant scope violation") -> None:
        super().__init__(message=message, code="tenant_scope_error")


def not_found(entity_id: UUID) -> InvoiceLineItemNotFoundError:
    """Factory for consistent not-found exceptions."""
    return InvoiceLineItemNotFoundError(entity_id)


def validation(message: str, *, code: str = "validation_error") -> InvoiceLineItemValidationError:
    """Factory for validation failures."""
    return InvoiceLineItemValidationError(message, code=code)
