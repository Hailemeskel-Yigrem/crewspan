"""Standard API response envelopes and error shapes."""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    data: T
    message: str | None = None
    meta: dict[str, Any] | None = None


class ErrorDetail(BaseModel):
    field: str | None = None
    message: str
    code: str | None = None


class ErrorResponse(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | None = None
    errors: list[ErrorDetail] | None = None

    @classmethod
    def from_domain(cls, *, code: str, message: str, details: dict[str, Any] | None = None) -> "ErrorResponse":
        return cls(code=code, message=message, details=details)


class MessageResponse(BaseModel):
    message: str
    success: bool = True


class IdResponse(BaseModel):
    id: str
    resource: str | None = None


class BatchResult(BaseModel):
    processed: int
    failed: int = 0
    errors: list[str] = Field(default_factory=list)

    @property
    def success(self) -> bool:
        return self.failed == 0
