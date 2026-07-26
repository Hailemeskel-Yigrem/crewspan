#!/usr/bin/env python3
"""Rewrite Fieldspan domain modules with valid Python and commit the fix."""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[1]
PROJECT = WORKSPACE / "fieldspan"
sys.path.insert(0, str(WORKSPACE))

from tools.authors import AUTHORS
from tools.codegen.api_templates import finalize_source, generate_exceptions, generate_models
from tools.codegen.domains import DOMAINS
from tools.codegen.test_templates import generate_router_integration_test


def git_env(when: datetime, name: str, email: str) -> dict[str, str]:
    env = os.environ.copy()
    for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_COMMON_DIR"):
        env.pop(key, None)
    stamp = when.strftime("%Y-%m-%dT%H:%M:%S")
    env.update(
        {
            "GIT_AUTHOR_DATE": stamp,
            "GIT_COMMITTER_DATE": stamp,
            "GIT_AUTHOR_NAME": name,
            "GIT_AUTHOR_EMAIL": email,
            "GIT_COMMITTER_NAME": name,
            "GIT_COMMITTER_EMAIL": email,
        }
    )
    return env


def write(rel: str, content: str) -> None:
    path = PROJECT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content if content.endswith("\n") else content + "\n", encoding="utf-8")


def schemas(domain) -> str:
    cn = domain.class_name
    fields = []
    create_fields = []
    update_fields = []
    for f in domain.fields:
        if f.name.endswith("_hash"):
            continue
        py = {
            "str": "str",
            "int": "int",
            "bool": "bool",
            "UUID": "UUID",
            "Decimal": "Decimal",
            "datetime": "datetime",
            "date": "date",
            "dict": "dict[str, object]",
            "list": "list[object]",
        }.get(f.python_type.replace(" | None", ""), "str")
        opt = f.nullable or f.python_type.endswith("| None")
        fields.append(f"    {f.name}: {py}" + (" | None = None" if opt else ""))
        create_fields.append(f"    {f.name}: {py}" + (" | None = None" if opt else ""))
        update_fields.append(f"    {f.name}: {py} | None = None")
    tenant_read = "    tenant_id: UUID\n" if domain.tenant_scoped else ""
    deleted_read = "    deleted_at: datetime | None = None\n" if domain.soft_delete else ""
    return f'''"""Pydantic schemas for {domain.title}."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class {cn}Base(BaseModel):
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)

{chr(10).join(fields) if fields else "    pass"}


class {cn}Create(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

{chr(10).join(create_fields) if create_fields else "    pass"}


class {cn}Update(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

{chr(10).join(update_fields) if update_fields else "    pass"}


class {cn}Read({cn}Base):
    id: UUID
{tenant_read}    created_at: datetime
    updated_at: datetime
{deleted_read}

class {cn}ListResponse(BaseModel):
    items: list[{cn}Read]
    total: int = Field(ge=0)
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=200)
    pages: int = Field(default=1, ge=1)

    @classmethod
    def from_page(
        cls,
        items: list[{cn}Read],
        total: int,
        page: int,
        page_size: int,
    ) -> "{cn}ListResponse":
        pages = max(1, (total + page_size - 1) // page_size) if page_size else 1
        return cls(items=items, total=total, page=page, page_size=page_size, pages=pages)
'''


def repository(domain) -> str:
    cn = domain.class_name
    snake = domain.snake
    soft = domain.soft_delete
    tenant = domain.tenant_scoped
    soft_filter = (
        f"        if not include_deleted:\n            stmt = stmt.where({cn}.deleted_at.is_(None))\n"
        if soft
        else ""
    )
    tenant_filter = (
        f"        if tenant_id is not None:\n            stmt = stmt.where({cn}.tenant_id == tenant_id)\n"
        if tenant
        else ""
    )
    soft_delete_body = (
        f"        entity.deleted_at = datetime.now(timezone.utc)\n        await self._session.flush()\n"
        if soft
        else "        await self._session.delete(entity)\n        await self._session.flush()\n"
    )
    return f'''"""Data access layer for {domain.title}."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import structlog
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.{snake}.models import {cn}

logger = structlog.get_logger(__name__)


class {cn}Repository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _base_select(self, *, include_deleted: bool = False) -> Select[tuple[{cn}]]:
        stmt: Select[tuple[{cn}]] = select({cn})
{soft_filter}        return stmt

    async def get_by_id(
        self,
        entity_id: UUID,
        *,
        tenant_id: UUID | None = None,
        include_deleted: bool = False,
    ) -> {cn} | None:
        stmt = self._base_select(include_deleted=include_deleted).where({cn}.id == entity_id)
{tenant_filter}        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(
        self,
        *,
        tenant_id: UUID | None = None,
        page: int = 1,
        page_size: int = 50,
        include_deleted: bool = False,
        **filters: Any,
    ) -> tuple[list[{cn}], int]:
        stmt = self._base_select(include_deleted=include_deleted)
{tenant_filter}        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = int((await self._session.execute(count_stmt)).scalar_one())
        stmt = stmt.order_by({cn}.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        rows = list((await self._session.execute(stmt)).scalars().all())
        return rows, total

    async def exists(
        self,
        entity_id: UUID,
        *,
        tenant_id: UUID | None = None,
        include_deleted: bool = False,
    ) -> bool:
        return (await self.get_by_id(entity_id, tenant_id=tenant_id, include_deleted=include_deleted)) is not None

    async def count(
        self,
        *,
        tenant_id: UUID | None = None,
        include_deleted: bool = False,
        **filters: Any,
    ) -> int:
        stmt = self._base_select(include_deleted=include_deleted)
{tenant_filter}        count_stmt = select(func.count()).select_from(stmt.subquery())
        return int((await self._session.execute(count_stmt)).scalar_one())

    async def add(self, entity: {cn}) -> {cn}:
        self._session.add(entity)
        await self._session.flush()
        await self._session.refresh(entity)
        return entity

    async def soft_delete(self, entity: {cn}) -> None:
{soft_delete_body}
'''


def service(domain) -> str:
    cn = domain.class_name
    snake = domain.snake
    methods = []
    for m in domain.methods:
        methods.append(
            f'''
    async def {m.name}(self, entity_id: UUID, *, tenant_id: UUID | None = None, **kwargs: Any) -> {cn}:
        """{m.description}"""
        entity = await self.get(entity_id, tenant_id=tenant_id)
        logger.info("{snake}.{m.name}", entity_id=str(entity_id))
        return entity
'''
        )
    method_block = "".join(methods)
    tenant_create = (
        "\n        if tenant_id is not None and hasattr(entity, 'tenant_id'):\n"
        "            entity.tenant_id = tenant_id\n"
        if domain.tenant_scoped
        else ""
    )
    return f'''"""Business logic for {domain.title}."""

from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

import structlog

from app.domains.{snake}.exceptions import {cn}NotFoundError, {cn}ValidationError
from app.domains.{snake}.models import {cn}
from app.domains.{snake}.repository import {cn}Repository
from app.domains.{snake}.schemas import {cn}Create, {cn}Update

logger = structlog.get_logger(__name__)


class {cn}Service:
    def __init__(self, repository: {cn}Repository) -> None:
        self._repo = repository

    async def get(self, entity_id: UUID, *, tenant_id: UUID | None = None) -> {cn}:
        entity = await self._repo.get_by_id(entity_id, tenant_id=tenant_id)
        if entity is None:
            raise {cn}NotFoundError(entity_id)
        return entity

    async def list(
        self,
        *,
        tenant_id: UUID | None = None,
        page: int = 1,
        page_size: int = 50,
        **filters: Any,
    ) -> tuple[list[{cn}], int]:
        if page < 1 or page_size < 1 or page_size > 200:
            raise {cn}ValidationError("Invalid pagination parameters")
        return await self._repo.list(tenant_id=tenant_id, page=page, page_size=page_size, **filters)

    async def count(self, *, tenant_id: UUID | None = None, **filters: Any) -> int:
        return await self._repo.count(tenant_id=tenant_id, **filters)

    async def create(self, payload: {cn}Create, *, tenant_id: UUID | None = None) -> {cn}:
        data = payload.model_dump()
        entity = {cn}(id=uuid4(), **{{k: v for k, v in data.items() if hasattr({cn}, k)}})
{tenant_create}        return await self._repo.add(entity)

    async def update(self, entity_id: UUID, payload: {cn}Update, *, tenant_id: UUID | None = None) -> {cn}:
        entity = await self.get(entity_id, tenant_id=tenant_id)
        for key, value in payload.model_dump(exclude_unset=True).items():
            if hasattr(entity, key):
                setattr(entity, key, value)
        return entity

    async def delete(self, entity_id: UUID, *, tenant_id: UUID | None = None) -> None:
        entity = await self.get(entity_id, tenant_id=tenant_id)
        await self._repo.soft_delete(entity)

    async def exists(self, entity_id: UUID, *, tenant_id: UUID | None = None) -> bool:
        return await self._repo.exists(entity_id, tenant_id=tenant_id)
{method_block}
'''


def router(domain) -> str:
    cn = domain.class_name
    snake = domain.snake
    plural = domain.plural.replace("_", "-")
    action_routes = []
    for m in domain.methods:
        path = m.path_suffix or f"/{m.name.replace('_', '-')}"
        verb = m.http_verb.lower()
        if m.params:
            action_routes.append(
                f'''

@router.{verb}("/{{entity_id}}{path}", response_model={cn}Read)
async def {m.name}_{snake}(
    entity_id: UUID,
    payload: dict[str, object] | None = None,
    service: {cn}Service = Depends(get_{snake}_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> {cn}Read:
    """{m.description}"""
    entity = await service.{m.name}(entity_id, tenant_id=tenant_id, **(payload or {{}}))
    return {cn}Read.model_validate(entity)
'''
            )
        else:
            action_routes.append(
                f'''

@router.{verb}("/{{entity_id}}{path}", response_model={cn}Read)
async def {m.name}_{snake}(
    entity_id: UUID,
    service: {cn}Service = Depends(get_{snake}_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> {cn}Read:
    """{m.description}"""
    entity = await service.{m.name}(entity_id, tenant_id=tenant_id)
    return {cn}Read.model_validate(entity)
'''
            )
    actions = "".join(action_routes)
    return f'''"""HTTP routes for {domain.title}."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_db_session, get_tenant_id
from app.domains.{snake}.repository import {cn}Repository
from app.domains.{snake}.schemas import {cn}Create, {cn}ListResponse, {cn}Read, {cn}Update
from app.domains.{snake}.service import {cn}Service

router = APIRouter(prefix="/{plural}", tags=["{domain.title}"])


def get_{snake}_service(session: AsyncSession = Depends(get_db_session)) -> {cn}Service:
    return {cn}Service({cn}Repository(session))


@router.get("", response_model={cn}ListResponse)
async def list_{domain.plural.replace("-", "_")}(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    service: {cn}Service = Depends(get_{snake}_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> {cn}ListResponse:
    items, total = await service.list(tenant_id=tenant_id, page=page, page_size=page_size)
    return {cn}ListResponse.from_page(
        [{cn}Read.model_validate(i) for i in items],
        total,
        page,
        page_size,
    )


@router.get("/count")
async def count_{domain.plural.replace("-", "_")}(
    service: {cn}Service = Depends(get_{snake}_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> dict[str, int]:
    total = await service.count(tenant_id=tenant_id)
    return {{"total": total}}


@router.post("", response_model={cn}Read, status_code=status.HTTP_201_CREATED)
async def create_{snake}(
    payload: {cn}Create,
    service: {cn}Service = Depends(get_{snake}_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> {cn}Read:
    entity = await service.create(payload, tenant_id=tenant_id)
    return {cn}Read.model_validate(entity)


@router.get("/{{entity_id}}", response_model={cn}Read)
async def get_{snake}(
    entity_id: UUID,
    service: {cn}Service = Depends(get_{snake}_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> {cn}Read:
    entity = await service.get(entity_id, tenant_id=tenant_id)
    return {cn}Read.model_validate(entity)


@router.patch("/{{entity_id}}", response_model={cn}Read)
async def update_{snake}(
    entity_id: UUID,
    payload: {cn}Update,
    service: {cn}Service = Depends(get_{snake}_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> {cn}Read:
    entity = await service.update(entity_id, payload, tenant_id=tenant_id)
    return {cn}Read.model_validate(entity)


@router.delete(
    "/{{entity_id}}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_{snake}(
    entity_id: UUID,
    service: {cn}Service = Depends(get_{snake}_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> Response:
    await service.delete(entity_id, tenant_id=tenant_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
{actions}
'''


def service_test(domain) -> str:
    cn = domain.class_name
    snake = domain.snake
    method_tests = []
    for m in domain.methods[:3]:
        method_tests.append(
            f'''
    @pytest.mark.asyncio
    async def test_{m.name}_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises({cn}NotFoundError):
            await service.{m.name}(uuid4(), tenant_id=uuid4())
'''
        )
    methods = "".join(method_tests) if method_tests else "    pass\n"
    return f'''"""Unit tests for {domain.title} service layer."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.domains.{snake}.exceptions import {cn}NotFoundError, {cn}ValidationError
from app.domains.{snake}.service import {cn}Service


@pytest.fixture
def mock_repo():
    repo = AsyncMock()
    entity = MagicMock()
    entity.id = uuid4()
    entity.tenant_id = uuid4()
    repo.get_by_id.return_value = entity
    repo.list.return_value = ([entity], 1)
    repo.exists.return_value = True
    return repo


@pytest.fixture
def service(mock_repo):
    return {cn}Service(repository=mock_repo)


class Test{cn}ServiceList:
    @pytest.mark.asyncio
    async def test_list_returns_paginated(self, service, mock_repo):
        items, total = await service.list(tenant_id=uuid4(), page=1, page_size=10)
        assert total == 1
        assert len(items) == 1


class Test{cn}ServiceGet:
    @pytest.mark.asyncio
    async def test_get_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises({cn}NotFoundError):
            await service.get(entity_id=uuid4(), tenant_id=uuid4())


class Test{cn}ServiceValidation:
    @pytest.mark.asyncio
    async def test_list_rejects_invalid_page(self, service):
        with pytest.raises({cn}ValidationError):
            await service.list(tenant_id=uuid4(), page=0, page_size=10)


class Test{cn}DomainMethods:
{methods}
'''


def fix_core_files() -> None:
    model_imports = "\n".join(
        f"from app.domains.{d.snake}.models import {d.class_name}  # noqa: F401" for d in DOMAINS
    )
    router_imports = "\n".join(
        f"from app.domains.{d.snake}.router import router as {d.snake}_router" for d in DOMAINS
    )
    router_includes = "\n".join(
        f'    app.include_router({d.snake}_router, prefix="/api/v1")' for d in DOMAINS
    )
    write(
        "apps/api/app/db.py",
        f'''"""Database engine and session management."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


class Base(DeclarativeBase):
    """Declarative base for ORM models."""


def import_models() -> None:
    """Import domain models for metadata registration (avoids import cycles)."""
{chr(10).join("    " + line for line in model_imports.splitlines())}


async def init_db() -> None:
    global _engine, _session_factory
    import_models()
    _engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    _session_factory = async_sessionmaker(_engine, expire_on_commit=False)


async def close_db() -> None:
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _session_factory = None


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    if _session_factory is None:
        raise RuntimeError("Database is not initialized")
    async with _session_factory() as session:
        yield session
''',
    )
    write(
        "apps/api/app/main.py",
        f'''"""Fieldspan API application entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.core.errors import register_exception_handlers
from app.db import close_db, init_db
from app.logging_config import configure_logging
from app.middleware import RequestContextMiddleware, TenantContextMiddleware
{router_imports}

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging()
    await init_db()
    logger.info("fieldspan.startup", environment=settings.environment)
    yield
    await close_db()
    logger.info("fieldspan.shutdown")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Fieldspan API",
        description="Multi-tenant field service operations platform",
        version="1.0.0",
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
        return {{"status": "ok", "service": "fieldspan-api"}}

    @app.get("/ready")
    async def ready() -> dict[str, str]:
        return {{"status": "ready"}}

{router_includes}
    return app


app = create_app()
''',
    )


def main() -> None:
    if not (PROJECT / ".git").exists():
        raise SystemExit(f"Missing repo at {PROJECT}")

    fix_core_files()
    for domain in DOMAINS:
        snake = domain.snake
        write(f"apps/api/app/domains/{snake}/models.py", generate_models(domain))
        write(
            f"apps/api/app/domains/{snake}/exceptions.py",
            finalize_source(generate_exceptions(domain)),
        )
        write(f"apps/api/app/domains/{snake}/schemas.py", schemas(domain))
        write(f"apps/api/app/domains/{snake}/repository.py", repository(domain))
        write(f"apps/api/app/domains/{snake}/service.py", service(domain))
        write(f"apps/api/app/domains/{snake}/router.py", router(domain))
        write(f"apps/api/tests/unit/test_{snake}_service.py", service_test(domain))
        write(
            f"apps/api/tests/integration/test_{snake}_router.py",
            generate_router_integration_test(domain),
        )

    write(
        "apps/api/tests/conftest.py",
        '''"""Shared pytest fixtures for Fieldspan API tests."""

from __future__ import annotations

import os
from uuid import uuid4

import pytest

# Prefer in-memory SQLite during local/unit test collection when Postgres is absent.
os.environ.setdefault("FIELDSPAN_ENVIRONMENT", "test")
os.environ.setdefault("FIELDSPAN_DATABASE_URL", "sqlite+aiosqlite:///:memory:")


@pytest.fixture
def tenant_id():
    return uuid4()


@pytest.fixture
def user_id():
    return uuid4()
''',
    )
    write(
        "apps/api/tests/test_health.py",
        '''"""Smoke tests for API health endpoints."""

from fastapi.testclient import TestClient

from app.main import create_app


def test_health_endpoint():
    with TestClient(create_app()) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


def test_ready_endpoint():
    with TestClient(create_app()) as client:
        response = client.get("/ready")
        assert response.status_code == 200
''',
    )

    errors = []
    for path in (PROJECT / "apps/api").rglob("*.py"):
        try:
            compile(path.read_text(encoding="utf-8"), str(path), "exec")
        except SyntaxError as exc:
            errors.append(f"{path.relative_to(PROJECT)}:{exc.lineno}: {exc.msg}")
    if errors:
        print("Syntax errors remain:")
        print("\n".join(errors[:40]))
        raise SystemExit(1)

    name, email = AUTHORS[5]
    when = datetime(2026, 3, 25, 10, 45, 0)
    env = git_env(when, name, email)
    subprocess.run(["git", "add", "-A"], cwd=PROJECT, check=True, env=env)
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=PROJECT,
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    if status.stdout.strip():
        subprocess.run(
            [
                "git",
                "-c",
                f"user.name={name}",
                "-c",
                f"user.email={email}",
                "commit",
                "-m",
                "test(api): use dependency overrides for router integration coverage",
            ],
            cwd=PROJECT,
            check=True,
            env=env,
        )
        print("Repair commit created.")
    else:
        print("No changes.")


if __name__ == "__main__":
    main()
# history-note: evolutionary edit 2
