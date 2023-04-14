"""Pagination utilities for list endpoints and repository queries."""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from typing import Generic, Sequence, TypeVar

from pydantic import BaseModel, Field, field_validator

from app.config import settings

T = TypeVar("T")


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=settings.default_page_size, ge=1, le=settings.max_page_size)
    order_by: str = Field(default="created_at")
    order_dir: str = Field(default="desc", pattern="^(asc|desc)$")

    @field_validator("page_size")
    @classmethod
    def clamp_page_size(cls, value: int) -> int:
        return min(value, settings.max_page_size)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    pages: int

    @classmethod
    def from_items(
        cls,
        items: Sequence[T],
        total: int,
        params: PaginationParams,
    ) -> "PaginatedResponse[T]":
        pages = max(1, ceil(total / params.page_size)) if params.page_size else 1
        return cls(
            items=list(items),
            total=total,
            page=params.page,
            page_size=params.page_size,
            pages=pages,
        )


@dataclass(frozen=True, slots=True)
class PageSlice:
    offset: int
    limit: int

    @classmethod
    def from_params(cls, params: PaginationParams) -> "PageSlice":
        return cls(offset=params.offset, limit=params.limit)


def normalize_page(page: int, total: int, page_size: int) -> int:
    if page_size <= 0:
        return 1
    max_page = max(1, ceil(total / page_size))
    return min(max(1, page), max_page)
