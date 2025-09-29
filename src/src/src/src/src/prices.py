# src/prices.py
from __future__ import annotations
import asyncio
import aiohttp
from typing import Optional
from decimal import Decimal
import time
import logging

logger = logging.getLogger(__name__)

class PriceService:
    def __init__(self, session: aiohttp.ClientSession, cache_ttl: int = 30, retries: int = 3, timeout: int = 10):
        self._session = session
        self._cache: dict[str, tuple[Decimal, float]] = {}
        self._ttl = cache_ttl
        self._retries = retries
        self._timeout = timeout

    async def get_price(self, base: str, quote: str) -> Optional[Decimal]:
        key = f"{base.lower()}:{quote.lower()}"
        now = time.time()
        cached = self._cache.get(key)
        if cached and now - cached[1] < self._ttl:
            return cached[0]
        # try CoinGecko simple price
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {"ids": base.lower(), "vs_currencies": quote.lower()}
        for attempt in range(1, self._retries + 1):
            try:
                async with self._session.get(url, params=params, timeout=self._timeout) as resp:
                    if resp.status != 200:
                        text = await resp.text()
                        logger.warning("CoinGecko non-200 %s: %s", resp.status, text)
                        raise RuntimeError("Bad response")
                    data = await resp.json()
                    price = data.get(base.lower(), {}).get(quote.lower())
                    if price is None:
                        return None
                    dec = Decimal(str(price))
                    self._cache[key] = (dec, now)
                    return dec
            except asyncio.TimeoutError:
                logger.warning("Timeout fetching price %s/%s attempt=%d", base, quote, attempt)
            except Exception as exc:
                logger.exception("Error fetching price %s/%s attempt=%d: %s", base, quote, attempt, exc)
            await asyncio.sleep(0.5 * attempt)
        return None

    def clear_cache(self) -> None:
        self._cache.clear()
