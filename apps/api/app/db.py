"""Database engine and session management."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.base import Base
from app.config import settings

__all__ = ["Base", "SessionLocal", "close_db", "engine", "get_session", "init_db"]

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
