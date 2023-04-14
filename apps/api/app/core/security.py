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
