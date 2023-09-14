"""Domain-specific exceptions for Payment."""

from __future__ import annotations

from uuid import UUID

from app.core.errors import DomainError, NotFoundError


class PaymentError(DomainError):
    """Base exception for payment operations."""

    domain = "payment"


class PaymentNotFoundError(NotFoundError, PaymentError):
    """Raised when a payment record cannot be located."""

    def __init__(self, entity_id: UUID) -> None:
        super().__init__(
            resource="payment",
            identifier=str(entity_id),
            message=f"Payment {entity_id} was not found",
        )


class PaymentValidationError(PaymentError):
    """Raised when payment business rules are violated."""

    def __init__(self, message: str, *, code: str = "validation_error") -> None:
        super().__init__(message=message, code=code)


class PaymentConflictError(PaymentError):
    """Raised when an operation conflicts with current payment state."""

    def __init__(self, message: str, *, code: str = "conflict") -> None:
        super().__init__(message=message, code=code)


class PaymentPermissionError(PaymentError):
    """Raised when caller lacks permission for payment action."""

    def __init__(self, action: str) -> None:
        super().__init__(
            message=f"Permission denied for {action} on payment",
            code="permission_denied",
        )


class PaymentStateError(PaymentError):
    """Raised when an operation is invalid for the current payment state."""

    def __init__(self, current: str, action: str) -> None:
        super().__init__(
            message=f"Cannot {action} while payment is in status '{current}'",
            code="invalid_state",
        )
        self.current = current
        self.action = action


class PaymentTenantScopeError(PaymentError):
    """Raised when tenant context is missing or mismatched."""

    def __init__(self, message: str = "Tenant scope violation") -> None:
        super().__init__(message=message, code="tenant_scope_error")


def not_found(entity_id: UUID) -> PaymentNotFoundError:
    """Factory for consistent not-found exceptions."""
    return PaymentNotFoundError(entity_id)


def validation(message: str, *, code: str = "validation_error") -> PaymentValidationError:
    """Factory for validation failures."""
    return PaymentValidationError(message, code=code)
