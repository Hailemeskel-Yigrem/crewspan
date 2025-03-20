"""Unit tests for SearchService."""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.services.search_service import SearchService


@pytest.fixture
def search_service():
    return SearchService(AsyncMock())


@pytest.mark.asyncio
async def test_search_returns_empty_for_short_query(search_service):
    hits = await search_service.search(uuid4(), "a")
    assert hits == []
