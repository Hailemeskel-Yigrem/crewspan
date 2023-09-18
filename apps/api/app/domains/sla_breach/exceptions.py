"""Domain-specific exceptions for SlaBreach."""

from __future__ import annotations

from uuid import UUID

from app.core.errors import DomainError, NotFoundError


class SlaBreachError(DomainError):
    """Base exception for sla_breach operations."""

    domain = "sla_breach"


class SlaBreachNotFoundError(NotFoundError, SlaBreachError):
    """Raised when a sla_breach record cannot be located."""

    def __init__(self, entity_id: UUID) -> None:
        super().__init__(
            resource="sla_breach",
            identifier=str(entity_id),
            message=f"SlaBreach {entity_id} was not found",
        )


class SlaBreachValidationError(SlaBreachError):
    """Raised when sla_breach business rules are violated."""

    def __init__(self, message: str, *, code: str = "validation_error") -> None:
        super().__init__(message=message, code=code)


class SlaBreachConflictError(SlaBreachError):
    """Raised when an operation conflicts with current sla_breach state."""

    def __init__(self, message: str, *, code: str = "conflict") -> None:
        super().__init__(message=message, code=code)


class SlaBreachPermissionError(SlaBreachError):
    """Raised when caller lacks permission for sla_breach action."""

    def __init__(self, action: str) -> None:
        super().__init__(
            message=f"Permission denied for {action} on sla_breach",
            code="permission_denied",
        )


class SlaBreachStateError(SlaBreachError):
    """Raised when an operation is invalid for the current sla_breach state."""

    def __init__(self, current: str, action: str) -> None:
        super().__init__(
            message=f"Cannot {action} while sla_breach is in status '{current}'",
            code="invalid_state",
        )
        self.current = current
        self.action = action


class SlaBreachTenantScopeError(SlaBreachError):
    """Raised when tenant context is missing or mismatched."""

    def __init__(self, message: str = "Tenant scope violation") -> None:
        super().__init__(message=message, code="tenant_scope_error")


def not_found(entity_id: UUID) -> SlaBreachNotFoundError:
    """Factory for consistent not-found exceptions."""
    return SlaBreachNotFoundError(entity_id)


def validation(message: str, *, code: str = "validation_error") -> SlaBreachValidationError:
    """Factory for validation failures."""
    return SlaBreachValidationError(message, code=code)
