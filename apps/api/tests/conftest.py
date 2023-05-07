"""Shared pytest fixtures for RelayOps API tests."""

from __future__ import annotations

from uuid import uuid4

import pytest


@pytest.fixture
def tenant_id():
    return uuid4()


@pytest.fixture
def user_id():
    return uuid4()
