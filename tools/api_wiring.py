"""Helpers that assemble main.py / db.py as domains are introduced historically."""

from __future__ import annotations

from tools.codegen.domains import DomainSpec


def partial_main_py(domains: list[DomainSpec]) -> str:
    router_imports = "\n".join(
        f"from app.domains.{d.snake}.router import router as {d.snake}_router" for d in domains
    )
    router_includes = "\n".join(
        f'    app.include_router({d.snake}_router, prefix="/api/v1")' for d in domains
    )
    return (
        '"""Fieldspan API application entrypoint."""\n\n'
        "from __future__ import annotations\n\n"
        "from contextlib import asynccontextmanager\n\n"
        "import structlog\n"
        "from fastapi import FastAPI\n"
        "from fastapi.middleware.cors import CORSMiddleware\n\n"
        "from app.config import settings\n"
        "from app.core.errors import register_exception_handlers\n"
        "from app.db import close_db, init_db\n"
        "from app.logging_config import configure_logging\n"
        "from app.middleware import RequestContextMiddleware, TenantContextMiddleware\n"
        f"{router_imports}\n\n"
        "logger = structlog.get_logger(__name__)\n\n\n"
        "@asynccontextmanager\n"
        "async def lifespan(app: FastAPI):\n"
        "    configure_logging()\n"
        "    await init_db()\n"
        '    logger.info("fieldspan.startup", environment=settings.environment)\n'
        "    yield\n"
        "    await close_db()\n"
        '    logger.info("fieldspan.shutdown")\n\n\n'
        "def create_app() -> FastAPI:\n"
        "    app = FastAPI(\n"
        '        title="Fieldspan API",\n'
        '        description="Multi-tenant field service operations platform",\n'
        '        version="0.1.0",\n'
        "        lifespan=lifespan,\n"
        "    )\n"
        "    app.add_middleware(\n"
        "        CORSMiddleware,\n"
        "        allow_origins=settings.cors_origins,\n"
        "        allow_credentials=True,\n"
        '        allow_methods=["*"],\n'
        '        allow_headers=["*"],\n'
        "    )\n"
        "    app.add_middleware(TenantContextMiddleware)\n"
        "    app.add_middleware(RequestContextMiddleware)\n"
        "    register_exception_handlers(app)\n\n"
        '    @app.get("/health")\n'
        "    async def health() -> dict[str, str]:\n"
        '        return {"status": "ok", "service": "fieldspan-api"}\n\n'
        '    @app.get("/ready")\n'
        "    async def ready() -> dict[str, str]:\n"
        '        return {"status": "ready"}\n\n'
        f"{router_includes}\n"
        "    return app\n\n\n"
        "app = create_app()\n"
    )


def partial_db_py(domains: list[DomainSpec]) -> str:
    model_imports = "\n".join(
        f"from app.domains.{d.snake}.models import {d.class_name}  # noqa: F401" for d in domains
    )
    return (
        '"""Database engine and session management."""\n\n'
        "from __future__ import annotations\n\n"
        "from collections.abc import AsyncGenerator\n\n"
        "from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine\n"
        "from sqlalchemy.orm import DeclarativeBase\n\n"
        "from app.config import settings\n\n"
        f"{model_imports}\n\n\n"
        "class Base(DeclarativeBase):\n"
        "    pass\n\n\n"
        "engine: AsyncEngine | None = None\n"
        "SessionLocal: async_sessionmaker[AsyncSession] | None = None\n\n\n"
        "async def init_db() -> None:\n"
        "    global engine, SessionLocal\n"
        "    engine = create_async_engine(\n"
        "        settings.database_url,\n"
        "        echo=settings.debug,\n"
        "        pool_pre_ping=True,\n"
        "        pool_size=10,\n"
        "        max_overflow=20,\n"
        "    )\n"
        "    SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)\n\n\n"
        "async def close_db() -> None:\n"
        "    global engine\n"
        "    if engine is not None:\n"
        "        await engine.dispose()\n"
        "        engine = None\n\n\n"
        "async def get_session() -> AsyncGenerator[AsyncSession, None]:\n"
        "    if SessionLocal is None:\n"
        '        raise RuntimeError("Database not initialized")\n'
        "    async with SessionLocal() as session:\n"
        "        try:\n"
        "            yield session\n"
        "            await session.commit()\n"
        "        except Exception:\n"
        "            await session.rollback()\n"
        "            raise\n"
    )
