"""
prices.py
---------
Fetch and cache crypto/fiat prices from CoinGecko with retry/backoff.
"""

import asyncio
import logging
from decimal import Decimal
from typing import Optional

import httpx
from cachetools import TTLCache

logger = logging.getLogger(__name__)

COINGECKO_URL = "https://api.coingecko.com/api/v3"
FIAT_CODES = {"usd", "eur", "cad", "irr", "gbp", "try", "jpy", "cny"}


class PriceService:
    """Service to fetch and cache crypto/fiat prices."""

    def __init__(self, ttl: int = 60) -> None:
        self.cache: TTLCache[str, Decimal] = TTLCache(maxsize=2048, ttl=ttl)
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(10.0),
            headers={"User-Agent": "CryptoPulseBot/1.0"},
        )

    async def close(self) -> None:
        """Close the HTTP client session."""
        await self.client.aclose()

    async def _request(self, url: str, params: dict, retries: int = 3) -> dict:
        """Perform GET request with retry and exponential backoff."""
        backoff = 0.5
        for attempt in range(retries):
            try:
                response = await self.client.get(url, params=params)
                if response.status_code == 429:  # rate limited
                    await asyncio.sleep(backoff)
                    backoff *= 2
                    continue
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as exc:
                logger.warning("HTTP error on attempt %d: %s", attempt + 1, exc)
                await asyncio.sleep(backoff)
                backoff *= 2
        return {}

    async def get_price(self, base_id: str, quote_id: str) -> Optional[Decimal]:
        """
        Get the price of base_id in terms of quote_id.
        Returns Decimal or None if not available.
        """
        key = f"{base_id}:{quote_id}"
        if key in self.cache:
            return self.cache[key]

        url = f"{COINGECKO_URL}/simple/price"
        if quote_id in FIAT_CODES:
            params = {"ids": base_id, "vs_currencies": quote_id}
            data = await self._request(url, params)
            value = data.get(base_id, {}).get(quote_id)
            if value is None:
                return None
            price = Decimal(str(value))
        else:
            params = {"ids": f"{base_id},{quote_id}", "vs_currencies": "usd"}
            data = await self._request(url, params)
            base_usd = data.get(base_id, {}).get("usd")
            quote_usd = data.get(quote_id, {}).get("usd")
            if not base_usd or not quote_usd:
                return None
            price = Decimal(str(base_usd)) / Decimal(str(quote_usd))

        self.cache[key] = price
        return price
