"""Unit tests for password hashing and JWT handling."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest

from app.config import settings
from app.core.security import (
    ALGORITHM,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


class TestPasswordHashing:
    def test_hash_then_verify_round_trips(self):
        hashed = hash_password("correct horse battery")
        assert hashed != "correct horse battery"
        assert verify_password("correct horse battery", hashed)

    def test_verify_rejects_wrong_password(self):
        assert not verify_password("nope", hash_password("correct horse battery"))

    def test_verify_rejects_malformed_hash(self):
        assert not verify_password("anything", "not-a-bcrypt-hash")

    def test_hash_rejects_short_password(self):
        with pytest.raises(ValueError):
            hash_password("short")


class TestAccessToken:
    def test_round_trips_subject_and_tenant(self):
        subject, tenant_id = str(uuid4()), uuid4()
        payload = decode_token(create_access_token(subject, tenant_id=tenant_id))
        assert payload["sub"] == subject
        assert payload["tenant_id"] == str(tenant_id)
        assert payload["type"] == "access"

    def test_carries_extra_claims(self):
        token = create_access_token(str(uuid4()), extra_claims={"role": "dispatcher"})
        assert decode_token(token)["role"] == "dispatcher"

    def test_refresh_token_is_marked_as_such(self):
        assert decode_token(create_refresh_token(str(uuid4())))["type"] == "refresh"


class TestTokenRejection:
    def test_rejects_a_token_signed_with_another_key(self):
        forged = jwt.encode({"sub": "someone"}, "not-the-secret", algorithm=ALGORITHM)
        with pytest.raises(jwt.PyJWTError):
            decode_token(forged)

    def test_rejects_an_expired_token(self):
        expired = jwt.encode(
            {"sub": "someone", "exp": datetime.now(UTC) - timedelta(minutes=1)},
            settings.secret_key,
            algorithm=ALGORITHM,
        )
        with pytest.raises(jwt.ExpiredSignatureError):
            decode_token(expired)

    def test_rejects_a_garbage_token(self):
        with pytest.raises(jwt.PyJWTError):
            decode_token("not.a.token")


class TestPasswordLimits:
    def test_rejects_password_over_the_bcrypt_byte_limit(self):
        with pytest.raises(ValueError, match="at most"):
            hash_password("a" * 73)

    def test_accepts_a_password_at_the_limit(self):
        secret = "a" * 72
        assert verify_password(secret, hash_password(secret))

    def test_multibyte_password_is_measured_in_bytes(self):
        # 3 bytes per character in UTF-8, so 24 characters is exactly 72 bytes.
        secret = "é" * 30  # 60 bytes
        assert verify_password(secret, hash_password(secret))
