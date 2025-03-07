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
