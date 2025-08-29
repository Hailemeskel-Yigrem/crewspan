"""Domain-specific exceptions for ServiceContract."""

from __future__ import annotations

from uuid import UUID

from app.core.errors import DomainError, NotFoundError


class ServiceContractError(DomainError):
    """Base exception for service_contract operations."""

    domain = "service_contract"


class ServiceContractNotFoundError(NotFoundError, ServiceContractError):
    """Raised when a service_contract record cannot be located."""

    def __init__(self, entity_id: UUID) -> None:
        super().__init__(
            resource="service_contract",
            identifier=str(entity_id),
            message=f"ServiceContract {entity_id} was not found",
        )


class ServiceContractValidationError(ServiceContractError):
    """Raised when service_contract business rules are violated."""

    def __init__(self, message: str, *, code: str = "validation_error") -> None:
        super().__init__(message=message, code=code)


class ServiceContractConflictError(ServiceContractError):
    """Raised when an operation conflicts with current service_contract state."""

    def __init__(self, message: str, *, code: str = "conflict") -> None:
        super().__init__(message=message, code=code)


class ServiceContractPermissionError(ServiceContractError):
    """Raised when caller lacks permission for service_contract action."""

    def __init__(self, action: str) -> None:
        super().__init__(
            message=f"Permission denied for {action} on service_contract",
            code="permission_denied",
        )


class ServiceContractStateError(ServiceContractError):
    """Raised when an operation is invalid for the current service_contract state."""

    def __init__(self, current: str, action: str) -> None:
        super().__init__(
            message=f"Cannot {action} while service_contract is in status '{current}'",
            code="invalid_state",
        )
        self.current = current
        self.action = action


class ServiceContractTenantScopeError(ServiceContractError):
    """Raised when tenant context is missing or mismatched."""

    def __init__(self, message: str = "Tenant scope violation") -> None:
        super().__init__(message=message, code="tenant_scope_error")


def not_found(entity_id: UUID) -> ServiceContractNotFoundError:
    """Factory for consistent not-found exceptions."""
    return ServiceContractNotFoundError(entity_id)


def validation(message: str, *, code: str = "validation_error") -> ServiceContractValidationError:
    """Factory for validation failures."""
    return ServiceContractValidationError(message, code=code)
# history-note: evolutionary edit 27
