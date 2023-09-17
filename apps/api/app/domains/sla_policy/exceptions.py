"""Domain-specific exceptions for SlaPolicy."""

from __future__ import annotations

from uuid import UUID

from app.core.errors import DomainError, NotFoundError


class SlaPolicyError(DomainError):
    """Base exception for sla_policy operations."""

    domain = "sla_policy"


class SlaPolicyNotFoundError(NotFoundError, SlaPolicyError):
    """Raised when a sla_policy record cannot be located."""

    def __init__(self, entity_id: UUID) -> None:
        super().__init__(
            resource="sla_policy",
            identifier=str(entity_id),
            message=f"SlaPolicy {entity_id} was not found",
        )


class SlaPolicyValidationError(SlaPolicyError):
    """Raised when sla_policy business rules are violated."""

    def __init__(self, message: str, *, code: str = "validation_error") -> None:
        super().__init__(message=message, code=code)


class SlaPolicyConflictError(SlaPolicyError):
    """Raised when an operation conflicts with current sla_policy state."""

    def __init__(self, message: str, *, code: str = "conflict") -> None:
        super().__init__(message=message, code=code)


class SlaPolicyPermissionError(SlaPolicyError):
    """Raised when caller lacks permission for sla_policy action."""

    def __init__(self, action: str) -> None:
        super().__init__(
            message=f"Permission denied for {action} on sla_policy",
            code="permission_denied",
        )


class SlaPolicyStateError(SlaPolicyError):
    """Raised when an operation is invalid for the current sla_policy state."""

    def __init__(self, current: str, action: str) -> None:
        super().__init__(
            message=f"Cannot {action} while sla_policy is in status '{current}'",
            code="invalid_state",
        )
        self.current = current
        self.action = action


class SlaPolicyTenantScopeError(SlaPolicyError):
    """Raised when tenant context is missing or mismatched."""

    def __init__(self, message: str = "Tenant scope violation") -> None:
        super().__init__(message=message, code="tenant_scope_error")


def not_found(entity_id: UUID) -> SlaPolicyNotFoundError:
    """Factory for consistent not-found exceptions."""
    return SlaPolicyNotFoundError(entity_id)


def validation(message: str, *, code: str = "validation_error") -> SlaPolicyValidationError:
    """Factory for validation failures."""
    return SlaPolicyValidationError(message, code=code)
