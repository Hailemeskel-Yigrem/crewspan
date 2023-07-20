"""Domain-specific exceptions for TechnicianSkill."""

from __future__ import annotations

from uuid import UUID

from app.core.errors import DomainError, NotFoundError


class TechnicianSkillError(DomainError):
    """Base exception for technician_skill operations."""

    domain = "technician_skill"


class TechnicianSkillNotFoundError(NotFoundError, TechnicianSkillError):
    """Raised when a technician_skill record cannot be located."""

    def __init__(self, entity_id: UUID) -> None:
        super().__init__(
            resource="technician_skill",
            identifier=str(entity_id),
            message=f"TechnicianSkill {entity_id} was not found",
        )


class TechnicianSkillValidationError(TechnicianSkillError):
    """Raised when technician_skill business rules are violated."""

    def __init__(self, message: str, *, code: str = "validation_error") -> None:
        super().__init__(message=message, code=code)


class TechnicianSkillConflictError(TechnicianSkillError):
    """Raised when an operation conflicts with current technician_skill state."""

    def __init__(self, message: str, *, code: str = "conflict") -> None:
        super().__init__(message=message, code=code)


class TechnicianSkillPermissionError(TechnicianSkillError):
    """Raised when caller lacks permission for technician_skill action."""

    def __init__(self, action: str) -> None:
        super().__init__(
            message=f"Permission denied for {action} on technician_skill",
            code="permission_denied",
        )


class TechnicianSkillStateError(TechnicianSkillError):
    """Raised when an operation is invalid for the current technician_skill state."""

    def __init__(self, current: str, action: str) -> None:
        super().__init__(
            message=f"Cannot {action} while technician_skill is in status '{current}'",
            code="invalid_state",
        )
        self.current = current
        self.action = action


class TechnicianSkillTenantScopeError(TechnicianSkillError):
    """Raised when tenant context is missing or mismatched."""

    def __init__(self, message: str = "Tenant scope violation") -> None:
        super().__init__(message=message, code="tenant_scope_error")


def not_found(entity_id: UUID) -> TechnicianSkillNotFoundError:
    """Factory for consistent not-found exceptions."""
    return TechnicianSkillNotFoundError(entity_id)


def validation(message: str, *, code: str = "validation_error") -> TechnicianSkillValidationError:
    """Factory for validation failures."""
    return TechnicianSkillValidationError(message, code=code)
