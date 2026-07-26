"""Generate the Crewspan FastAPI application tree."""

from __future__ import annotations

import textwrap
from pathlib import Path

from tools.codegen.api_templates import _T_CLASS, _snippet, finalize_source, generate_all_domain_files
from tools.codegen.domains import DOMAINS


def _write(path: Path, content: str) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = finalize_source(content) if path.suffix == ".py" else content
    path.write_text(normalized, encoding="utf-8")
    return len(normalized.splitlines())


def _pyproject() -> str:
    return textwrap.dedent(
        """\
        [build-system]
        requires = ["setuptools>=68", "wheel"]
        build-backend = "setuptools.build_meta"

        [project]
        name = "crewspan-api"
        version = "0.1.0"
        description = "Crewspan multi-tenant field service operations API"
        requires-python = ">=3.11"
        dependencies = [
            "fastapi>=0.110.0",
            "uvicorn[standard]>=0.27.0",
            "sqlalchemy[asyncio]>=2.0.25",
            "asyncpg>=0.29.0",
            "pydantic>=2.6.0",
            "pydantic-settings>=2.2.0",
            "alembic>=1.13.0",
            "redis>=5.0.0",
            "structlog>=24.1.0",
            "python-jose[cryptography]>=3.3.0",
            "passlib[bcrypt]>=1.7.4",
            "httpx>=0.27.0",
            "python-multipart>=0.0.9",
        ]

        [project.optional-dependencies]
        dev = [
            "pytest>=8.0.0",
            "pytest-asyncio>=0.23.0",
            "ruff>=0.3.0",
            "mypy>=1.8.0",
        ]

        [tool.setuptools.packages.find]
        where = ["."]
        include = ["app*"]

        [tool.ruff]
        line-length = 100
        target-version = "py311"

        [tool.pytest.ini_options]
        asyncio_mode = "auto"
        testpaths = ["tests"]
        """
    )


def _requirements() -> str:
    return textwrap.dedent(
        """\
        fastapi>=0.110.0
        uvicorn[standard]>=0.27.0
        sqlalchemy[asyncio]>=2.0.25
        asyncpg>=0.29.0
        pydantic>=2.6.0
        pydantic-settings>=2.2.0
        alembic>=1.13.0
        redis>=5.0.0
        structlog>=24.1.0
        python-jose[cryptography]>=3.3.0
        passlib[bcrypt]>=1.7.4
        httpx>=0.27.0
        python-multipart>=0.0.9
        """
    )


def _main_py(router_imports: str, router_includes: str) -> str:
    return f'''\
        """Crewspan API application entrypoint."""

        from __future__ import annotations

        from contextlib import asynccontextmanager

        import structlog
        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware

        from app.config import settings
        from app.db import close_db, init_db
        from app.logging_config import configure_logging
        from app.core.errors import register_exception_handlers
        from app.middleware import RequestContextMiddleware, TenantContextMiddleware
{router_imports}

        logger = structlog.get_logger(__name__)


        @asynccontextmanager
        async def lifespan(app: FastAPI):
            configure_logging()
            await init_db()
            logger.info("crewspan.startup", environment=settings.environment)
            yield
            await close_db()
            logger.info("crewspan.shutdown")


        def create_app() -> FastAPI:
            app = FastAPI(
                title="Crewspan API",
                description="Multi-tenant field service operations platform",
                version="0.1.0",
                lifespan=lifespan,
            )
            app.add_middleware(
                CORSMiddleware,
                allow_origins=settings.cors_origins,
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )
            app.add_middleware(TenantContextMiddleware)
            app.add_middleware(RequestContextMiddleware)
            register_exception_handlers(app)

            @app.get("/health")
            async def health() -> dict[str, str]:
                return {{"status": "ok", "service": "crewspan-api"}}

            @app.get("/ready")
            async def ready() -> dict[str, str]:
                return {{"status": "ready"}}

{router_includes}
            return app


        app = create_app()
        '''


def _config_py() -> str:
    return textwrap.dedent(
        '''\
        """Crewspan API configuration with environment-aware validation."""

        from __future__ import annotations

        from functools import lru_cache
        from typing import Literal

        from pydantic import Field, field_validator
        from pydantic_settings import BaseSettings, SettingsConfigDict


        Environment = Literal["development", "staging", "production", "test"]


        class Settings(BaseSettings):
            """Application settings loaded from environment variables (CREWSPAN_ prefix)."""

            model_config = SettingsConfigDict(
                env_file=".env",
                env_prefix="CREWSPAN_",
                extra="ignore",
                case_sensitive=False,
            )

            environment: Environment = "development"
            debug: bool = False
            database_url: str = "postgresql+asyncpg://crewspan:crewspan@localhost:5432/crewspan"
            redis_url: str = "redis://localhost:6379/0"
            secret_key: str = Field(default="change-me-in-production")
            access_token_expire_minutes: int = Field(default=60, ge=5, le=1440)
            refresh_token_expire_days: int = Field(default=7, ge=1, le=90)
            cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])
            log_level: str = "INFO"
            log_json: bool = True
            default_page_size: int = Field(default=50, ge=1, le=200)
            max_page_size: int = Field(default=200, ge=10, le=500)
            request_timeout_seconds: float = Field(default=30.0, ge=1.0)
            rate_limit_per_minute: int = Field(default=120, ge=10)
            export_max_rows: int = Field(default=10_000, ge=100)
            search_max_results: int = Field(default=500, ge=50)
            webhook_timeout_seconds: int = Field(default=30, ge=5)
            bcrypt_rounds: int = Field(default=12, ge=10, le=14)

            @field_validator("secret_key")
            @classmethod
            def validate_secret_key(cls, value: str, info) -> str:
                env = info.data.get("environment", "development")
                if env == "production" and value == "change-me-in-production":
                    raise ValueError("CREWSPAN_SECRET_KEY must be set in production")
                if len(value) < 16:
                    raise ValueError("secret_key must be at least 16 characters")
                return value

            @field_validator("cors_origins", mode="before")
            @classmethod
            def parse_cors_origins(cls, value):
                if isinstance(value, str):
                    return [part.strip() for part in value.split(",") if part.strip()]
                return value

            @property
            def is_production(self) -> bool:
                return self.environment == "production"

            @property
            def sqlalchemy_echo(self) -> bool:
                return self.debug and not self.is_production


        @lru_cache
        def get_settings() -> Settings:
            return Settings()


        settings = get_settings()
        '''
    )


def _db_py() -> str:
    model_imports = "\n".join(
        f"        from app.domains.{d.snake}.models import {d.class_name}  # noqa: F401"
        for d in DOMAINS
    )
    return f'''\
        """Database engine and session management."""

        from __future__ import annotations

        from collections.abc import AsyncGenerator

        from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
        from sqlalchemy.orm import DeclarativeBase

        from app.config import settings

{model_imports}


        class Base(DeclarativeBase):
            pass


        engine: AsyncEngine | None = None
        SessionLocal: async_sessionmaker[AsyncSession] | None = None


        async def init_db() -> None:
            global engine, SessionLocal
            engine = create_async_engine(
                settings.database_url,
                echo=settings.debug,
                pool_pre_ping=True,
                pool_size=10,
                max_overflow=20,
            )
            SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


        async def close_db() -> None:
            global engine
            if engine is not None:
                await engine.dispose()
                engine = None


        async def get_session() -> AsyncGenerator[AsyncSession, None]:
            if SessionLocal is None:
                raise RuntimeError("Database not initialized")
            async with SessionLocal() as session:
                try:
                    yield session
                    await session.commit()
                except Exception:
                    await session.rollback()
                    raise
        '''


def _deps_py() -> str:
    return textwrap.dedent(
        '''\
        """FastAPI dependency providers for DB sessions, auth, and tenant context."""

        from __future__ import annotations

        from typing import Annotated
        from uuid import UUID

        from fastapi import Depends, Header, HTTPException, status
        from sqlalchemy.ext.asyncio import AsyncSession

        from app.core.security import get_current_user_id, get_optional_user_id
        from app.db import get_session


        async def get_db_session(session: AsyncSession = Depends(get_session)) -> AsyncSession:
            return session


        DbSession = Annotated[AsyncSession, Depends(get_db_session)]


        async def get_tenant_id(
            x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"),
        ) -> UUID:
            if not x_tenant_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="X-Tenant-Id header is required",
                )
            try:
                return UUID(x_tenant_id)
            except ValueError as exc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid tenant id format",
                ) from exc


        async def get_optional_tenant_id(
            x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"),
        ) -> UUID | None:
            if not x_tenant_id:
                return None
            try:
                return UUID(x_tenant_id)
            except ValueError:
                return None


        TenantId = Annotated[UUID, Depends(get_tenant_id)]


        async def get_current_user(
            user_id: UUID = Depends(get_current_user_id),
            tenant_id: UUID = Depends(get_tenant_id),
        ) -> dict[str, UUID]:
            return {"user_id": user_id, "tenant_id": tenant_id}


        async def get_request_context(
            user_id: UUID | None = Depends(get_optional_user_id),
            tenant_id: UUID | None = Depends(get_optional_tenant_id),
            x_request_id: str | None = Header(default=None, alias="X-Request-Id"),
        ) -> dict[str, object]:
            return {
                "user_id": str(user_id) if user_id else None,
                "tenant_id": str(tenant_id) if tenant_id else None,
                "request_id": x_request_id,
            }
        '''
    )


def _logging_config_py() -> str:
    return textwrap.dedent(
        '''\
        """Structured logging configuration."""

        from __future__ import annotations

        import logging
        import sys

        import structlog

        from app.config import settings


        def configure_logging() -> None:
            logging.basicConfig(
                format="%(message)s",
                stream=sys.stdout,
                level=getattr(logging, settings.log_level.upper(), logging.INFO),
            )
            processors: list[structlog.types.Processor] = [
                structlog.contextvars.merge_contextvars,
                structlog.processors.add_log_level,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
            ]
            if settings.log_json:
                processors.append(structlog.processors.JSONRenderer())
            else:
                processors.append(structlog.dev.ConsoleRenderer())
            structlog.configure(
                processors=processors,
                wrapper_class=structlog.make_filtering_bound_logger(
                    getattr(logging, settings.log_level.upper(), logging.INFO)
                ),
                context_class=dict,
                logger_factory=structlog.PrintLoggerFactory(),
                cache_logger_on_first_use=True,
            )
        '''
    )


def _middleware_py() -> str:
    return textwrap.dedent(
        '''\
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
        '''
    )


def _core_errors_py() -> str:
    return textwrap.dedent(
        '''\
        """Shared error types, HTTP mapping, and FastAPI exception handlers."""

        from __future__ import annotations

        from typing import Any

        from fastapi import FastAPI, Request, status
        from fastapi.exceptions import RequestValidationError
        from fastapi.responses import JSONResponse
        import structlog

        logger = structlog.get_logger(__name__)


        class DomainError(Exception):
            """Base class for business rule violations."""

            def __init__(self, message: str, *, code: str = "domain_error", details: dict[str, Any] | None = None) -> None:
                self.message = message
                self.code = code
                self.details = details or {}
                super().__init__(message)


        class NotFoundError(DomainError):
            def __init__(self, *, resource: str, identifier: str, message: str) -> None:
                super().__init__(message, code="not_found", details={"resource": resource, "identifier": identifier})
                self.resource = resource
                self.identifier = identifier


        class ValidationAppError(DomainError):
            def __init__(self, message: str, *, field: str | None = None) -> None:
                details = {"field": field} if field else {}
                super().__init__(message, code="validation_error", details=details)


        class AuthorizationError(DomainError):
            def __init__(self, message: str = "Permission denied") -> None:
                super().__init__(message, code="permission_denied")


        class ConflictError(DomainError):
            def __init__(self, message: str) -> None:
                super().__init__(message, code="conflict")


        def _error_body(exc: DomainError) -> dict[str, Any]:
            body: dict[str, Any] = {"code": exc.code, "message": exc.message}
            if exc.details:
                body["details"] = exc.details
            return body


        def register_exception_handlers(app: FastAPI) -> None:
            @app.exception_handler(NotFoundError)
            async def not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
                logger.info("api.not_found", resource=exc.resource, identifier=exc.identifier)
                return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=_error_body(exc))

            @app.exception_handler(AuthorizationError)
            async def authz_handler(request: Request, exc: AuthorizationError) -> JSONResponse:
                return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content=_error_body(exc))

            @app.exception_handler(ConflictError)
            async def conflict_handler(request: Request, exc: ConflictError) -> JSONResponse:
                return JSONResponse(status_code=status.HTTP_409_CONFLICT, content=_error_body(exc))

            @app.exception_handler(DomainError)
            async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
                status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
                if exc.code == "conflict":
                    status_code = status.HTTP_409_CONFLICT
                elif exc.code == "permission_denied":
                    status_code = status.HTTP_403_FORBIDDEN
                logger.warning("api.domain_error", code=exc.code, message=exc.message)
                return JSONResponse(status_code=status_code, content=_error_body(exc))

            @app.exception_handler(RequestValidationError)
            async def validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
                errors = exc.errors()
                logger.info("api.validation_error", count=len(errors))
                return JSONResponse(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    content={
                        "code": "validation_error",
                        "message": "Request validation failed",
                        "details": {"errors": errors},
                    },
                )
        '''
    )


def _core_security_py() -> str:
    return textwrap.dedent(
        '''\
        """Authentication, password hashing, JWT creation, and dependency guards."""

        from __future__ import annotations

        from datetime import datetime, timedelta, timezone
        from typing import Any
        from uuid import UUID

        from fastapi import Depends, HTTPException, status
        from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
        from jose import JWTError, jwt
        from passlib.context import CryptContext

        from app.config import settings

        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=settings.bcrypt_rounds)
        bearer_scheme = HTTPBearer(auto_error=False)

        ALGORITHM = "HS256"


        def hash_password(password: str) -> str:
            if len(password) < 8:
                raise ValueError("Password must be at least 8 characters")
            return pwd_context.hash(password)


        def verify_password(plain: str, hashed: str) -> bool:
            try:
                return pwd_context.verify(plain, hashed)
            except ValueError:
                return False


        def create_access_token(
            subject: str,
            *,
            tenant_id: UUID | None = None,
            extra_claims: dict[str, Any] | None = None,
        ) -> str:
            expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
            payload: dict[str, Any] = {"sub": subject, "exp": expire, "type": "access"}
            if tenant_id:
                payload["tenant_id"] = str(tenant_id)
            if extra_claims:
                payload.update(extra_claims)
            return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


        def create_refresh_token(subject: str, *, tenant_id: UUID | None = None) -> str:
            expire = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
            payload: dict[str, Any] = {"sub": subject, "exp": expire, "type": "refresh"}
            if tenant_id:
                payload["tenant_id"] = str(tenant_id)
            return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


        def decode_token(token: str) -> dict[str, Any]:
            return jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])


        async def get_current_user_id(
            credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
        ) -> UUID:
            if credentials is None or not credentials.credentials:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
            try:
                payload = decode_token(credentials.credentials)
                if payload.get("type") not in (None, "access"):
                    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
                return UUID(payload["sub"])
            except (JWTError, ValueError, KeyError) as exc:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc


        async def get_optional_user_id(
            credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
        ) -> UUID | None:
            if credentials is None:
                return None
            try:
                return await get_current_user_id(credentials)
            except HTTPException:
                return None
        '''
    )


def _core_pagination_py() -> str:
    return textwrap.dedent(
        '''\
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
        '''
    )


def _core_responses_py() -> str:
    return textwrap.dedent(
        '''\
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
        '''
    )


def _alembic_ini() -> str:
    return textwrap.dedent(
        """\
        [alembic]
        script_location = alembic
        prepend_sys_path = .
        sqlalchemy.url = postgresql+asyncpg://crewspan:crewspan@localhost:5432/crewspan

        [loggers]
        keys = root,sqlalchemy,alembic

        [handlers]
        keys = console

        [formatters]
        keys = generic

        [logger_root]
        level = WARN
        handlers = console

        [logger_sqlalchemy]
        level = WARN
        handlers =
        qualname = sqlalchemy.engine

        [logger_alembic]
        level = INFO
        handlers =
        qualname = alembic

        [handler_console]
        class = StreamHandler
        args = (sys.stderr,)
        level = NOTSET
        formatter = generic

        [formatter_generic]
        format = %(levelname)-5.5s [%(name)s] %(message)s
        """
    )


def _alembic_env_py() -> str:
    return textwrap.dedent(
        '''\
        """Alembic migration environment."""

        from __future__ import annotations

        import asyncio
        from logging.config import fileConfig

        from alembic import context
        from sqlalchemy import pool
        from sqlalchemy.engine import Connection
        from sqlalchemy.ext.asyncio import async_engine_from_config

        from app.config import settings
        from app.db import Base

        config = context.config
        if config.config_file_name is not None:
            fileConfig(config.config_file_name)
        config.set_main_option("sqlalchemy.url", settings.database_url)
        target_metadata = Base.metadata


        def run_migrations_offline() -> None:
            url = config.get_main_option("sqlalchemy.url")
            context.configure(
                url=url,
                target_metadata=target_metadata,
                literal_binds=True,
                dialect_opts={"paramstyle": "named"},
            )
            with context.begin_transaction():
                context.run_migrations()


        def do_run_migrations(connection: Connection) -> None:
            context.configure(connection=connection, target_metadata=target_metadata)
            with context.begin_transaction():
                context.run_migrations()


        async def run_async_migrations() -> None:
            connectable = async_engine_from_config(
                config.get_section(config.config_ini_section, {}),
                prefix="sqlalchemy.",
                poolclass=pool.NullPool,
            )
            async with connectable.connect() as connection:
                await connection.run_sync(do_run_migrations)
            await connectable.dispose()


        def run_migrations_online() -> None:
            asyncio.run(run_async_migrations())


        if context.is_offline_mode():
            run_migrations_offline()
        else:
            run_migrations_online()
        '''
    )


def _initial_migration() -> str:
    table_blocks = []
    for d in DOMAINS:
        table = d.table_name or d.plural
        cols = ['sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True)']
        if d.tenant_scoped:
            cols.append('sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False, index=True)')
        for f in d.fields:
            col_args = [f'sa.Column("{f.name}", {f.sqlalchemy_type}']
            if f.nullable:
                col_args.append("nullable=True")
            else:
                col_args.append("nullable=False")
            if f.indexed:
                col_args.append("index=True")
            if f.unique:
                col_args.append("unique=True")
            cols.append(", ".join(col_args) + ")")
        cols.append('sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False)')
        cols.append('sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False)')
        if d.soft_delete:
            cols.append('sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True, index=True)')
        col_text = ",\n".join(f"            {col}" for col in cols)
        table_blocks.append(
            _snippet(
                f"""
                op.create_table(
                    "{table}",
                    {col_text},
                )
                """,
                level=_T_CLASS,
            )
        )
    upgrade = "\n".join(table_blocks)
    downgrade_tables = ", ".join(f'"{d.table_name or d.plural}"' for d in reversed(DOMAINS))
    return f'''\
        """Initial Crewspan schema migration."""

        from __future__ import annotations

        from alembic import op
        import sqlalchemy as sa
        from sqlalchemy.dialects import postgresql

        revision = "001_initial"
        down_revision = None
        branch_labels = None
        depends_on = None


        def upgrade() -> None:
{upgrade}


        def downgrade() -> None:
            for table in [{downgrade_tables}]:
                op.drop_table(table)
        '''


def _dockerfile() -> str:
    return textwrap.dedent(
        """\
        FROM python:3.11-slim

        WORKDIR /app

        RUN apt-get update && apt-get install -y --no-install-recommends \\
            build-essential libpq-dev \\
            && rm -rf /var/lib/apt/lists/*

        COPY requirements.txt .
        RUN pip install --no-cache-dir -r requirements.txt

        COPY . .

        ENV CREWSPAN_ENVIRONMENT=production
        EXPOSE 8000

        CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
        """
    )


def _core_validators_py() -> str:
    return textwrap.dedent(
        '''\
        """Shared validation helpers for API inputs and business rules."""

        from __future__ import annotations

        import re
        from datetime import datetime
        from decimal import Decimal
        from uuid import UUID

        from app.core.errors import ValidationAppError

        EMAIL_RE = re.compile(r"^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$")
        SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
        PHONE_RE = re.compile(r"^\\+?[0-9\\s\\-().]{7,32}$")


        def require_non_empty(value: str | None, *, field: str) -> str:
            if value is None or not str(value).strip():
                raise ValidationAppError(f"{field} is required", field=field)
            return str(value).strip()


        def validate_email(value: str | None, *, field: str = "email") -> str:
            normalized = require_non_empty(value, field=field).lower()
            if not EMAIL_RE.match(normalized):
                raise ValidationAppError("Invalid email address", field=field)
            return normalized


        def validate_slug(value: str, *, field: str = "slug") -> str:
            cleaned = value.strip().lower()
            if not SLUG_RE.match(cleaned):
                raise ValidationAppError("Slug must be lowercase alphanumeric with hyphens", field=field)
            return cleaned


        def validate_phone(value: str | None, *, field: str = "phone", required: bool = False) -> str | None:
            if value is None or not value.strip():
                if required:
                    raise ValidationAppError(f"{field} is required", field=field)
                return None
            cleaned = value.strip()
            if not PHONE_RE.match(cleaned):
                raise ValidationAppError("Invalid phone number format", field=field)
            return cleaned


        def validate_enum(value: str, allowed: set[str], *, field: str) -> str:
            if value not in allowed:
                raise ValidationAppError(
                    f"{field} must be one of: {', '.join(sorted(allowed))}",
                    field=field,
                )
            return value


        def validate_positive_decimal(value: Decimal | None, *, field: str, allow_zero: bool = False) -> Decimal | None:
            if value is None:
                return None
            if value < 0 or (not allow_zero and value == 0):
                raise ValidationAppError(f"{field} must be positive", field=field)
            return value


        def validate_date_order(start: datetime | None, end: datetime | None, *, start_field: str, end_field: str) -> None:
            if start is not None and end is not None and end < start:
                raise ValidationAppError(f"{end_field} must be on or after {start_field}")


        def validate_uuid(value: str | UUID, *, field: str) -> UUID:
            if isinstance(value, UUID):
                return value
            try:
                return UUID(str(value))
            except ValueError as exc:
                raise ValidationAppError(f"Invalid UUID for {field}", field=field) from exc


        def clamp_page_size(page_size: int, *, minimum: int = 1, maximum: int = 200) -> int:
            if page_size < minimum:
                raise ValidationAppError(f"page_size must be >= {minimum}", field="page_size")
            return min(page_size, maximum)
        '''
    )


def _services_init_py() -> str:
    return '"""Cross-domain application services."""\n'


def _auth_service_py() -> str:
    return textwrap.dedent(
        '''\
        """Authentication service: login, token refresh, and password lifecycle."""

        from __future__ import annotations

        from dataclasses import dataclass
        from datetime import datetime, timezone
        from uuid import UUID

        import structlog
        from sqlalchemy import select
        from sqlalchemy.ext.asyncio import AsyncSession

        from app.core.errors import AuthorizationError, ValidationAppError
        from app.core.security import (
            create_access_token,
            create_refresh_token,
            decode_token,
            hash_password,
            verify_password,
        )
        from app.domains.user.models import User

        logger = structlog.get_logger(__name__)


        @dataclass(frozen=True, slots=True)
        class AuthTokens:
            access_token: str
            refresh_token: str
            token_type: str = "bearer"
            expires_in_minutes: int = 60


        @dataclass(frozen=True, slots=True)
        class AuthenticatedUser:
            user_id: UUID
            tenant_id: UUID
            email: str
            full_name: str


        class AuthService:
            """Handles credential verification and JWT issuance."""

            def __init__(self, session: AsyncSession) -> None:
                self._session = session

            async def authenticate(
                self,
                *,
                email: str,
                password: str,
                tenant_id: UUID,
            ) -> AuthTokens:
                email_normalized = email.strip().lower()
                if not email_normalized or "@" not in email_normalized:
                    raise ValidationAppError("Valid email is required", field="email")
                if len(password) < 8:
                    raise ValidationAppError("Password must be at least 8 characters", field="password")

                stmt = select(User).where(
                    User.email == email_normalized,
                    User.tenant_id == tenant_id,
                    User.deleted_at.is_(None),
                )
                user = (await self._session.execute(stmt)).scalar_one_or_none()
                if user is None or not user.is_active:
                    logger.info("auth.login.failed", reason="unknown_user", email=email_normalized)
                    raise AuthorizationError("Invalid email or password")
                if not verify_password(password, user.password_hash):
                    logger.info("auth.login.failed", reason="bad_password", user_id=str(user.id))
                    raise AuthorizationError("Invalid email or password")

                user.last_login_at = datetime.now(timezone.utc)
                await self._session.flush()

                access = create_access_token(
                    str(user.id),
                    tenant_id=tenant_id,
                    extra_claims={"email": user.email, "name": user.full_name},
                )
                refresh = create_refresh_token(str(user.id), tenant_id=tenant_id)
                logger.info("auth.login.success", user_id=str(user.id), tenant_id=str(tenant_id))
                return AuthTokens(access_token=access, refresh_token=refresh)

            async def refresh(self, refresh_token: str) -> AuthTokens:
                try:
                    payload = decode_token(refresh_token)
                except Exception as exc:
                    raise AuthorizationError("Invalid refresh token") from exc
                if payload.get("type") != "refresh":
                    raise AuthorizationError("Token is not a refresh token")
                user_id = UUID(payload["sub"])
                tenant_id = UUID(payload["tenant_id"]) if payload.get("tenant_id") else None
                access = create_access_token(str(user_id), tenant_id=tenant_id)
                new_refresh = create_refresh_token(str(user_id), tenant_id=tenant_id)
                return AuthTokens(access_token=access, refresh_token=new_refresh)

            async def change_password(
                self,
                user_id: UUID,
                *,
                tenant_id: UUID,
                current_password: str,
                new_password: str,
            ) -> None:
                stmt = select(User).where(User.id == user_id, User.tenant_id == tenant_id)
                user = (await self._session.execute(stmt)).scalar_one_or_none()
                if user is None:
                    raise AuthorizationError("User not found")
                if not verify_password(current_password, user.password_hash):
                    raise AuthorizationError("Current password is incorrect")
                user.password_hash = hash_password(new_password)
                await self._session.flush()
                logger.info("auth.password_changed", user_id=str(user_id))
        '''
    )


def _reporting_service_py() -> str:
    domain_count = len(DOMAINS)
    return textwrap.dedent(
        f'''\
        """Operational reporting aggregates for dashboard and analytics endpoints."""

        from __future__ import annotations

        from dataclasses import dataclass, field
        from datetime import date, datetime, timedelta, timezone
        from decimal import Decimal
        from typing import Any
        from uuid import UUID

        import structlog
        from sqlalchemy import func, select
        from sqlalchemy.ext.asyncio import AsyncSession

        from app.domains.invoice.models import Invoice
        from app.domains.sla_breach.models import SlaBreach
        from app.domains.technician.models import Technician
        from app.domains.work_order.models import WorkOrder

        logger = structlog.get_logger(__name__)


        @dataclass(slots=True)
        class DashboardMetrics:
            open_work_orders: int = 0
            in_progress_work_orders: int = 0
            active_technicians: int = 0
            revenue_mtd: Decimal = Decimal("0")
            sla_breaches_open: int = 0
            completed_this_week: int = 0
            generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


        @dataclass(slots=True)
        class UtilizationRow:
            technician_id: UUID
            employee_id: str
            utilization_pct: float
            open_jobs: int


        class ReportingService:
            """Computes tenant-scoped KPIs across {domain_count} domain modules."""

            OPEN_STATUSES = ("draft", "submitted", "assigned", "in_progress", "pending")
            IN_PROGRESS_STATUSES = ("in_progress", "assigned")

            def __init__(self, session: AsyncSession) -> None:
                self._session = session

            async def dashboard(self, tenant_id: UUID) -> DashboardMetrics:
                now = datetime.now(timezone.utc)
                month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                week_start = now - timedelta(days=now.weekday())

                open_count = await self._count_work_orders(tenant_id, self.OPEN_STATUSES)
                in_progress = await self._count_work_orders(tenant_id, self.IN_PROGRESS_STATUSES)
                active_techs = await self._count_active_technicians(tenant_id)
                revenue = await self._sum_invoice_revenue(tenant_id, month_start)
                breaches = await self._count_open_sla_breaches(tenant_id)
                completed_week = await self._count_completed_since(tenant_id, week_start)

                metrics = DashboardMetrics(
                    open_work_orders=open_count,
                    in_progress_work_orders=in_progress,
                    active_technicians=active_techs,
                    revenue_mtd=revenue,
                    sla_breaches_open=breaches,
                    completed_this_week=completed_week,
                )
                logger.info("reporting.dashboard", tenant_id=str(tenant_id), **metrics.__dict__)
                return metrics

            async def technician_utilization(
                self,
                tenant_id: UUID,
                *,
                on_date: date | None = None,
            ) -> list[UtilizationRow]:
                on_date = on_date or date.today()
                stmt = select(Technician).where(
                    Technician.tenant_id == tenant_id,
                    Technician.deleted_at.is_(None),
                    Technician.status.in_(("available", "busy", "on_job")),
                )
                techs = (await self._session.execute(stmt)).scalars().all()
                rows: list[UtilizationRow] = []
                for tech in techs:
                    open_jobs = await self._open_jobs_for_technician(tenant_id, tech.id)
                    max_hours = max(1, int(getattr(tech, "max_daily_hours", 8) or 8))
                    utilization = min(100.0, (open_jobs / max_hours) * 100.0)
                    rows.append(
                        UtilizationRow(
                            technician_id=tech.id,
                            employee_id=str(tech.employee_id),
                            utilization_pct=round(utilization, 1),
                            open_jobs=open_jobs,
                        )
                    )
                return sorted(rows, key=lambda r: -r.utilization_pct)

            async def _count_work_orders(self, tenant_id: UUID, statuses: tuple[str, ...]) -> int:
                stmt = (
                    select(func.count())
                    .select_from(WorkOrder)
                    .where(
                        WorkOrder.tenant_id == tenant_id,
                        WorkOrder.deleted_at.is_(None),
                        WorkOrder.status.in_(statuses),
                    )
                )
                return int((await self._session.execute(stmt)).scalar_one())

            async def _count_active_technicians(self, tenant_id: UUID) -> int:
                stmt = (
                    select(func.count())
                    .select_from(Technician)
                    .where(
                        Technician.tenant_id == tenant_id,
                        Technician.deleted_at.is_(None),
                        Technician.status != "offline",
                    )
                )
                return int((await self._session.execute(stmt)).scalar_one())

            async def _sum_invoice_revenue(self, tenant_id: UUID, since: datetime) -> Decimal:
                stmt = select(func.coalesce(func.sum(Invoice.total_amount), 0)).where(
                    Invoice.tenant_id == tenant_id,
                    Invoice.deleted_at.is_(None),
                    Invoice.created_at >= since,
                    Invoice.status.in_(("finalized", "paid", "sent")),
                )
                value = (await self._session.execute(stmt)).scalar_one()
                return Decimal(str(value or 0))

            async def _count_open_sla_breaches(self, tenant_id: UUID) -> int:
                stmt = (
                    select(func.count())
                    .select_from(SlaBreach)
                    .where(
                        SlaBreach.tenant_id == tenant_id,
                        SlaBreach.deleted_at.is_(None),
                        SlaBreach.resolved_at.is_(None),
                    )
                )
                return int((await self._session.execute(stmt)).scalar_one())

            async def _count_completed_since(self, tenant_id: UUID, since: datetime) -> int:
                stmt = (
                    select(func.count())
                    .select_from(WorkOrder)
                    .where(
                        WorkOrder.tenant_id == tenant_id,
                        WorkOrder.deleted_at.is_(None),
                        WorkOrder.status == "completed",
                        WorkOrder.updated_at >= since,
                    )
                )
                return int((await self._session.execute(stmt)).scalar_one())

            async def _open_jobs_for_technician(self, tenant_id: UUID, technician_id: UUID) -> int:
                stmt = (
                    select(func.count())
                    .select_from(WorkOrder)
                    .where(
                        WorkOrder.tenant_id == tenant_id,
                        WorkOrder.deleted_at.is_(None),
                        WorkOrder.assigned_technician_id == technician_id,
                        WorkOrder.status.in_(self.IN_PROGRESS_STATUSES),
                    )
                )
                return int((await self._session.execute(stmt)).scalar_one())
        '''
    )


def _search_service_py() -> str:
    return textwrap.dedent(
        '''\
        """Cross-entity search across customers, work orders, and technicians."""

        from __future__ import annotations

        from dataclasses import dataclass
        from enum import Enum
        from typing import Any
        from uuid import UUID

        import structlog
        from sqlalchemy import or_, select
        from sqlalchemy.ext.asyncio import AsyncSession

        from app.config import settings
        from app.domains.customer.models import Customer
        from app.domains.technician.models import Technician
        from app.domains.work_order.models import WorkOrder

        logger = structlog.get_logger(__name__)


        class SearchEntity(str, Enum):
            WORK_ORDER = "work_order"
            CUSTOMER = "customer"
            TECHNICIAN = "technician"


        @dataclass(frozen=True, slots=True)
        class SearchHit:
            entity_type: SearchEntity
            entity_id: UUID
            title: str
            subtitle: str | None
            score: float


        class SearchService:
            """Simple ILIKE search with tenant isolation and result caps."""

            def __init__(self, session: AsyncSession) -> None:
                self._session = session

            async def search(
                self,
                tenant_id: UUID,
                query: str,
                *,
                entity_types: list[SearchEntity] | None = None,
                limit: int | None = None,
            ) -> list[SearchHit]:
                q = query.strip()
                if len(q) < 2:
                    return []
                limit = min(limit or 25, settings.search_max_results)
                types = entity_types or list(SearchEntity)
                hits: list[SearchHit] = []

                if SearchEntity.WORK_ORDER in types:
                    hits.extend(await self._search_work_orders(tenant_id, q, limit))
                if SearchEntity.CUSTOMER in types:
                    hits.extend(await self._search_customers(tenant_id, q, limit))
                if SearchEntity.TECHNICIAN in types:
                    hits.extend(await self._search_technicians(tenant_id, q, limit))

                hits.sort(key=lambda h: -h.score)
                result = hits[:limit]
                logger.info("search.executed", tenant_id=str(tenant_id), query=q, hits=len(result))
                return result

            async def _search_work_orders(self, tenant_id: UUID, q: str, limit: int) -> list[SearchHit]:
                pattern = f"%{q}%"
                stmt = (
                    select(WorkOrder)
                    .where(
                        WorkOrder.tenant_id == tenant_id,
                        WorkOrder.deleted_at.is_(None),
                        or_(WorkOrder.title.ilike(pattern), WorkOrder.order_number.ilike(pattern)),
                    )
                    .limit(limit)
                )
                rows = (await self._session.execute(stmt)).scalars().all()
                return [
                    SearchHit(
                        entity_type=SearchEntity.WORK_ORDER,
                        entity_id=row.id,
                        title=row.title,
                        subtitle=row.order_number,
                        score=1.0 if q.lower() in row.order_number.lower() else 0.8,
                    )
                    for row in rows
                ]

            async def _search_customers(self, tenant_id: UUID, q: str, limit: int) -> list[SearchHit]:
                pattern = f"%{q}%"
                stmt = (
                    select(Customer)
                    .where(
                        Customer.tenant_id == tenant_id,
                        Customer.deleted_at.is_(None),
                        or_(Customer.name.ilike(pattern), Customer.account_number.ilike(pattern)),
                    )
                    .limit(limit)
                )
                rows = (await self._session.execute(stmt)).scalars().all()
                return [
                    SearchHit(
                        entity_type=SearchEntity.CUSTOMER,
                        entity_id=row.id,
                        title=row.name,
                        subtitle=row.account_number,
                        score=0.9,
                    )
                    for row in rows
                ]

            async def _search_technicians(self, tenant_id: UUID, q: str, limit: int) -> list[SearchHit]:
                pattern = f"%{q}%"
                stmt = (
                    select(Technician)
                    .where(
                        Technician.tenant_id == tenant_id,
                        Technician.deleted_at.is_(None),
                        Technician.employee_id.ilike(pattern),
                    )
                    .limit(limit)
                )
                rows = (await self._session.execute(stmt)).scalars().all()
                return [
                    SearchHit(
                        entity_type=SearchEntity.TECHNICIAN,
                        entity_id=row.id,
                        title=row.employee_id,
                        subtitle=row.status,
                        score=0.85,
                    )
                    for row in rows
                ]
        '''
    )


def _export_service_py() -> str:
    return textwrap.dedent(
        '''\
        """CSV/JSON export helpers for operational data extracts."""

        from __future__ import annotations

        import csv
        import io
        import json
        from dataclasses import dataclass
        from datetime import datetime
        from enum import Enum
        from typing import Any, Sequence
        from uuid import UUID, uuid4

        import structlog
        from sqlalchemy.ext.asyncio import AsyncSession

        from app.config import settings
        from app.core.errors import ValidationAppError
        from app.domains.work_order.models import WorkOrder
        from app.domains.work_order.repository import WorkOrderRepository

        logger = structlog.get_logger(__name__)


        class ExportFormat(str, Enum):
            CSV = "csv"
            JSON = "json"


        @dataclass(frozen=True, slots=True)
        class ExportResult:
            export_id: UUID
            format: ExportFormat
            row_count: int
            content: str
            filename: str
            generated_at: datetime


        class ExportService:
            """Builds bounded exports for work orders and related entities."""

            WORK_ORDER_COLUMNS = (
                "id",
                "order_number",
                "title",
                "status",
                "priority",
                "customer_id",
                "scheduled_start",
                "created_at",
            )

            def __init__(self, session: AsyncSession) -> None:
                self._session = session
                self._work_orders = WorkOrderRepository(session)

            async def export_work_orders(
                self,
                tenant_id: UUID,
                *,
                fmt: ExportFormat = ExportFormat.CSV,
                status: str | None = None,
                max_rows: int | None = None,
            ) -> ExportResult:
                max_rows = min(max_rows or settings.export_max_rows, settings.export_max_rows)
                filters: dict[str, Any] = {}
                if status:
                    filters["status"] = status
                rows, total = await self._work_orders.list(
                    tenant_id=tenant_id,
                    page=1,
                    page_size=max_rows,
                    **filters,
                )
                if total > max_rows:
                    logger.warning(
                        "export.truncated",
                        tenant_id=str(tenant_id),
                        total=total,
                        exported=len(rows),
                    )
                content = self._serialize(rows, fmt)
                export_id = uuid4()
                filename = f"work_orders_{export_id.hex[:8]}.{fmt.value}"
                result = ExportResult(
                    export_id=export_id,
                    format=fmt,
                    row_count=len(rows),
                    content=content,
                    filename=filename,
                    generated_at=datetime.utcnow(),
                )
                logger.info("export.work_orders", export_id=str(export_id), rows=len(rows), format=fmt.value)
                return result

            def _serialize(self, rows: Sequence[WorkOrder], fmt: ExportFormat) -> str:
                dict_rows = [
                    {col: getattr(row, col, None) for col in self.WORK_ORDER_COLUMNS}
                    for row in rows
                ]
                if fmt == ExportFormat.JSON:
                    return json.dumps(dict_rows, default=str, indent=2)
                if fmt == ExportFormat.CSV:
                    buffer = io.StringIO()
                    writer = csv.DictWriter(buffer, fieldnames=list(self.WORK_ORDER_COLUMNS))
                    writer.writeheader()
                    for row in dict_rows:
                        writer.writerow({k: row[k] for k in self.WORK_ORDER_COLUMNS})
                    return buffer.getvalue()
                raise ValidationAppError(f"Unsupported export format: {fmt}")
        '''
    )


def generate_api_tree(root: Path) -> dict[str, int]:
    """Write the complete Crewspan API tree under *root*.

    Returns a mapping of relative path -> line count for generated files.
    """
    api_root = root / "apps" / "api"
    stats: dict[str, int] = {}

    def record(rel: str, content: str) -> None:
        stats[rel] = _write(api_root / rel, content)

    record("pyproject.toml", _pyproject())
    record("requirements.txt", _requirements())
    record("Dockerfile", _dockerfile())
    record("app/__init__.py", '"""Crewspan API package."""\n')
    record("app/config.py", _config_py())
    record("app/logging_config.py", _logging_config_py())
    record("app/middleware.py", _middleware_py())
    record("app/deps.py", _deps_py())
    record("app/db.py", _db_py())

    record("app/core/__init__.py", '"""Core utilities."""\n')
    record("app/core/errors.py", _core_errors_py())
    record("app/core/security.py", _core_security_py())
    record("app/core/pagination.py", _core_pagination_py())
    record("app/core/responses.py", _core_responses_py())
    record("app/core/validators.py", _core_validators_py())

    record("app/services/__init__.py", _services_init_py())
    record("app/services/auth_service.py", _auth_service_py())
    record("app/services/reporting_service.py", _reporting_service_py())
    record("app/services/search_service.py", _search_service_py())
    record("app/services/export_service.py", _export_service_py())

    for domain in DOMAINS:
        files = generate_all_domain_files(domain)
        for filename, source in files.items():
            rel = f"app/domains/{domain.snake}/{filename}"
            record(rel, source)

    router_imports = "\n".join(
        f"        from app.domains.{d.snake}.router import router as {d.snake}_router"
        for d in DOMAINS
    )
    router_includes = "\n".join(
        f'            app.include_router({d.snake}_router, prefix="/api/v1")'
        for d in DOMAINS
    )
    record("app/main.py", _main_py(router_imports, router_includes))

    record("alembic.ini", _alembic_ini())
    record("alembic/env.py", _alembic_env_py())
    record("alembic/script.py.mako", textwrap.dedent(
        """\
        \"\"\"${message}\"\"\"
        revision = ${repr(up_revision)}
        down_revision = ${repr(down_revision)}
        branch_labels = ${repr(branch_labels)}
        depends_on = ${repr(depends_on)}

        from alembic import op
        import sqlalchemy as sa
        ${imports if imports else ""}

        def upgrade() -> None:
            ${upgrades if upgrades else "pass"}


        def downgrade() -> None:
            ${downgrades if downgrades else "pass"}
        """
    ))
    record("alembic/versions/001_initial.py", _initial_migration())

    return stats


def print_generation_summary(stats: dict[str, int]) -> None:
    total_lines = sum(stats.values())
    total_files = len(stats)
    print(f"Generated {total_files} files, ~{total_lines:,} lines of API source")
    for rel, lines in sorted(stats.items()):
        print(f"  {rel}: {lines} lines")


if __name__ == "__main__":
    from pathlib import Path

    repo_root = Path(__file__).resolve().parents[2]
    summary = generate_api_tree(repo_root)
    print_generation_summary(summary)
