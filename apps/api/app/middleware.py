"""HTTP middleware for request tracing, tenant context, and timing."""

from __future__ import annotations

import time
import uuid
from collections.abc import Callable

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.config import settings

logger = structlog.get_logger(__name__)


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Bind request ID, path, and timing to structured logs."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            path=request.url.path,
            method=request.method,
            client_host=request.client.host if request.client else None,
        )
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            duration_ms = (time.perf_counter() - start) * 1000
            logger.exception(
                "http.request.error",
                duration_ms=round(duration_ms, 2),
            )
            raise
        duration_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Request-Id"] = request_id
        response.headers["X-Response-Time-Ms"] = str(round(duration_ms, 2))
        logger.info(
            "http.request",
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2),
        )
        if duration_ms > settings.request_timeout_seconds * 1000 * 0.8:
            logger.warning("http.request.slow", duration_ms=round(duration_ms, 2))
        return response


class TenantContextMiddleware(BaseHTTPMiddleware):
    """Propagate tenant header into logging context for correlation."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        tenant_id = request.headers.get("X-Tenant-Id")
        user_agent = request.headers.get("User-Agent", "")
        if tenant_id:
            structlog.contextvars.bind_contextvars(tenant_id=tenant_id)
        if user_agent:
            structlog.contextvars.bind_contextvars(user_agent=user_agent[:120])
        return await call_next(request)


def middleware_stack() -> list[Callable]:
    return [RequestContextMiddleware, TenantContextMiddleware]
