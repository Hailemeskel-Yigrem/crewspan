"""Domain-specific exceptions for CustomerSite."""

from __future__ import annotations

from uuid import UUID

from app.core.errors import DomainError, NotFoundError


class CustomerSiteError(DomainError):
    """Base exception for customer_site operations."""

    domain = "customer_site"


class CustomerSiteNotFoundError(NotFoundError, CustomerSiteError):
    """Raised when a customer_site record cannot be located."""

    def __init__(self, entity_id: UUID) -> None:
        super().__init__(
            resource="customer_site",
            identifier=str(entity_id),
            message=f"CustomerSite {entity_id} was not found",
        )


class CustomerSiteValidationError(CustomerSiteError):
    """Raised when customer_site business rules are violated."""

    def __init__(self, message: str, *, code: str = "validation_error") -> None:
        super().__init__(message=message, code=code)


class CustomerSiteConflictError(CustomerSiteError):
    """Raised when an operation conflicts with current customer_site state."""

    def __init__(self, message: str, *, code: str = "conflict") -> None:
        super().__init__(message=message, code=code)


class CustomerSitePermissionError(CustomerSiteError):
    """Raised when caller lacks permission for customer_site action."""

    def __init__(self, action: str) -> None:
        super().__init__(
            message=f"Permission denied for {action} on customer_site",
            code="permission_denied",
        )


class CustomerSiteStateError(CustomerSiteError):
    """Raised when an operation is invalid for the current customer_site state."""

    def __init__(self, current: str, action: str) -> None:
        super().__init__(
            message=f"Cannot {action} while customer_site is in status '{current}'",
            code="invalid_state",
        )
        self.current = current
        self.action = action


class CustomerSiteTenantScopeError(CustomerSiteError):
    """Raised when tenant context is missing or mismatched."""

    def __init__(self, message: str = "Tenant scope violation") -> None:
        super().__init__(message=message, code="tenant_scope_error")


def not_found(entity_id: UUID) -> CustomerSiteNotFoundError:
    """Factory for consistent not-found exceptions."""
    return CustomerSiteNotFoundError(entity_id)


def validation(message: str, *, code: str = "validation_error") -> CustomerSiteValidationError:
    """Factory for validation failures."""
    return CustomerSiteValidationError(message, code=code)
