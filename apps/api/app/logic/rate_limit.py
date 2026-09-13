"""Token-bucket and sliding-window rate limit helpers for API gateways."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from time import monotonic


@dataclass
class TokenBucket:
    capacity: float
    refill_per_second: float
    tokens: float
    updated_at: float

    @classmethod
    def create(cls, capacity: float, refill_per_second: float) -> TokenBucket:
        now = monotonic()
        return cls(capacity=capacity, refill_per_second=refill_per_second, tokens=capacity, updated_at=now)

    def _refill(self, now: float) -> None:
        elapsed = now - self.updated_at
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_per_second)
        self.updated_at = now

    def allow(self, cost: float = 1.0) -> bool:
        now = monotonic()
        self._refill(now)
        if self.tokens < cost:
            return False
        self.tokens -= cost
        return True

    def retry_after_seconds(self, cost: float = 1.0) -> float:
        now = monotonic()
        self._refill(now)
        if self.tokens >= cost:
            return 0.0
        deficit = cost - self.tokens
        return deficit / self.refill_per_second


@dataclass
class RateLimiterRegistry:
    """Named token buckets (e.g., per tenant or API key)."""

    _buckets: dict[str, TokenBucket] = field(default_factory=dict)
    _factory: Callable[[], TokenBucket] = field(
        default=lambda: TokenBucket.create(capacity=120.0, refill_per_second=2.0)
    )

    def allow(self, key: str, cost: float = 1.0) -> bool:
        bucket = self._buckets.setdefault(key, self._factory())
        return bucket.allow(cost)

    def retry_after(self, key: str, cost: float = 1.0) -> float:
        bucket = self._buckets.setdefault(key, self._factory())
        return bucket.retry_after_seconds(cost)
