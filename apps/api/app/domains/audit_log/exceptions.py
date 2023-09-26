"""Domain-specific exceptions for AuditLog."""

from __future__ import annotations

from uuid import UUID

from app.core.errors import DomainError, NotFoundError


class AuditLogError(DomainError):
    """Base exception for audit_log operations."""

    domain = "audit_log"


class AuditLogNotFoundError(NotFoundError, AuditLogError):
    """Raised when a audit_log record cannot be located."""

    def __init__(self, entity_id: UUID) -> None:
        super().__init__(
            resource="audit_log",
            identifier=str(entity_id),
            message=f"AuditLog {entity_id} was not found",
        )


class AuditLogValidationError(AuditLogError):
    """Raised when audit_log business rules are violated."""

    def __init__(self, message: str, *, code: str = "validation_error") -> None:
        super().__init__(message=message, code=code)


class AuditLogConflictError(AuditLogError):
    """Raised when an operation conflicts with current audit_log state."""

    def __init__(self, message: str, *, code: str = "conflict") -> None:
        super().__init__(message=message, code=code)


class AuditLogPermissionError(AuditLogError):
    """Raised when caller lacks permission for audit_log action."""

    def __init__(self, action: str) -> None:
        super().__init__(
            message=f"Permission denied for {action} on audit_log",
            code="permission_denied",
        )


class AuditLogStateError(AuditLogError):
    """Raised when an operation is invalid for the current audit_log state."""

    def __init__(self, current: str, action: str) -> None:
        super().__init__(
            message=f"Cannot {action} while audit_log is in status '{current}'",
            code="invalid_state",
        )
        self.current = current
        self.action = action


class AuditLogTenantScopeError(AuditLogError):
    """Raised when tenant context is missing or mismatched."""

    def __init__(self, message: str = "Tenant scope violation") -> None:
        super().__init__(message=message, code="tenant_scope_error")


def not_found(entity_id: UUID) -> AuditLogNotFoundError:
    """Factory for consistent not-found exceptions."""
    return AuditLogNotFoundError(entity_id)


def validation(message: str, *, code: str = "validation_error") -> AuditLogValidationError:
    """Factory for validation failures."""
    return AuditLogValidationError(message, code=code)
