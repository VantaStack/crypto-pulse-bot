# tests/test_prices.py
"""
Tests for src/prices.py PriceService

- Uses pytest and pytest-asyncio
- Mocks aiohttp responses using simple fake session objects to avoid network calls
- Verifies caching, retry behavior (via simulated failures), and Decimal conversion
"""
import asyncio
from decimal import Decimal
import pytest

from src.prices import PriceService
from src.config import Settings

class DummyResponse:
    def __init__(self, status: int, json_data=None, text_data=""):
        self.status = status
        self._json = json_data or {}
        self._text = text_data
        self.headers = {}

    async def json(self):
        return self._json

    async def text(self):
        return self._text

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

class DummySession:
    def __init__(self, responses):
        # responses: list of DummyResponse or exceptions to raise
        self._responses = list(responses)
        self.calls = []

    def get(self, url, params=None, timeout=None):
        self.calls.append((url, params, timeout))
        item = self._responses.pop(0)
        if isinstance(item, Exception):
            async def _raise():
                raise item
            return _raise()
        return item

@pytest.mark.asyncio
async def test_get_price_success_caching():
    settings = Settings(_env_file=None, BOT_TOKEN="x", CACHE_TTL=60, HTTP_RETRIES=1, HTTP_TIMEOUT=2)
    # prepare a successful JSON payload
    data = {"bitcoin": {"usd": 12345.67}}
    resp = DummyResponse(200, json_data=data)
    session = DummySession([resp])
    svc = PriceService(settings=settings, session=session)

    price = await svc.get_price("bitcoin", "usd")
    assert price == Decimal("12345.67")

    # second call should hit cache and not call session.get again
    price2 = await svc.get_price("bitcoin", "usd")
    assert price2 == price
    assert len(session.calls) == 1

@pytest.mark.asyncio
async def test_get_price_retry_and_fail_then_success():
    settings = Settings(_env_file=None, BOT_TOKEN="x", CACHE_TTL=1, HTTP_RETRIES=3, HTTP_TIMEOUT=1)
    # first two: server error 500, third: success
    resp1 = DummyResponse(500, json_data={})
    resp2 = DummyResponse(500, json_data={})
    resp3 = DummyResponse(200, json_data={"ethereum": {"usd": 2000}})
    session = DummySession([resp1, resp2, resp3])
    svc = PriceService(settings=settings, session=session)

    price = await svc.get_price("ethereum", "usd")
    assert price == Decimal("2000")

@pytest.mark.asyncio
async def test_get_price_not_found_returns_none():
    settings = Settings(_env_file=None, BOT_TOKEN="x", CACHE_TTL=1, HTTP_RETRIES=1, HTTP_TIMEOUT=1)
    resp = DummyResponse(200, json_data={"othercoin": {"usd": 1}})
    session = DummySession([resp])
    svc = PriceService(settings=settings, session=session)

    price = await svc.get_price("nonexistent", "usd")
    assert price is None

@pytest.mark.asyncio
async def test_clear_cache_and_stats():
    settings = Settings(_env_file=None, BOT_TOKEN="x", CACHE_TTL=60, HTTP_RETRIES=1, HTTP_TIMEOUT=1)
    resp = DummyResponse(200, json_data={"tether": {"usd": 1}})
    session = DummySession([resp])
    svc = PriceService(settings=settings, session=session)

    p = await svc.get_price("tether", "usd")
    assert p == Decimal("1")
    stats = svc.cache_stats()
    assert stats["keys"] == 1

    svc.clear_cache()
    stats2 = svc.cache_stats()
    assert stats2["keys"] == 0
