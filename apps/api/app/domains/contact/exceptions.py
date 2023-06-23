"""Domain-specific exceptions for Contact."""

from __future__ import annotations

from uuid import UUID

from app.core.errors import DomainError, NotFoundError


class ContactError(DomainError):
    """Base exception for contact operations."""

    domain = "contact"


class ContactNotFoundError(NotFoundError, ContactError):
    """Raised when a contact record cannot be located."""

    def __init__(self, entity_id: UUID) -> None:
        super().__init__(
            resource="contact",
            identifier=str(entity_id),
            message=f"Contact {entity_id} was not found",
        )


class ContactValidationError(ContactError):
    """Raised when contact business rules are violated."""

    def __init__(self, message: str, *, code: str = "validation_error") -> None:
        super().__init__(message=message, code=code)


class ContactConflictError(ContactError):
    """Raised when an operation conflicts with current contact state."""

    def __init__(self, message: str, *, code: str = "conflict") -> None:
        super().__init__(message=message, code=code)


class ContactPermissionError(ContactError):
    """Raised when caller lacks permission for contact action."""

    def __init__(self, action: str) -> None:
        super().__init__(
            message=f"Permission denied for {action} on contact",
            code="permission_denied",
        )


class ContactStateError(ContactError):
    """Raised when an operation is invalid for the current contact state."""

    def __init__(self, current: str, action: str) -> None:
        super().__init__(
            message=f"Cannot {action} while contact is in status '{current}'",
            code="invalid_state",
        )
        self.current = current
        self.action = action


class ContactTenantScopeError(ContactError):
    """Raised when tenant context is missing or mismatched."""

    def __init__(self, message: str = "Tenant scope violation") -> None:
        super().__init__(message=message, code="tenant_scope_error")


def not_found(entity_id: UUID) -> ContactNotFoundError:
    """Factory for consistent not-found exceptions."""
    return ContactNotFoundError(entity_id)


def validation(message: str, *, code: str = "validation_error") -> ContactValidationError:
    """Factory for validation failures."""
    return ContactValidationError(message, code=code)
