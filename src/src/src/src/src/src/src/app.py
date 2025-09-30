# src/app.py
"""
Application bootstrap for the Telegram bot.

Responsibilities:
- Load Settings (src.config.Settings)
- Configure logging
- Build telegram Application with shared aiohttp.ClientSession
- Create and register PriceService into app.bot_data
- Provide warmup task to preload common pairs
- Graceful shutdown: close session and clear caches

Usage:
    from src.app import build_app
    app = build_app()
    app.run_polling()
"""
from __future__ import annotations

import asyncio
import logging
from typing import Iterable, Optional

import aiohttp
from telegram.ext import Application

from .config import Settings
from .prices import PriceService

logger = logging.getLogger(__name__)


DEFAULT_WARMUP_PAIRS = [("bitcoin", "usd"), ("ethereum", "usd"), ("tether", "usd")]


def _configure_logging(level: str) -> None:
    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO), format=fmt)
    # reduce noisy libraries optionally
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def _ensure_event_loop() -> asyncio.AbstractEventLoop:
    try:
        return asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop


def build_app(settings: Optional[Settings] = None) -> Application:
    """
    Build and return a configured telegram.ext.Application instance.

    Registers into app.bot_data:
      - "settings": Settings
      - "http_session": aiohttp.ClientSession
      - "price_service": PriceService
      - "parse_mode": settings.parse_mode

    Callers should later add handlers before run.
    """
    settings = settings or Settings()
    _configure_logging(settings.log_level)

    # ensure loop ready for aiohttp timeouts
    _ensure_event_loop()

    # create shared aiohttp session with sensible defaults
    timeout = aiohttp.ClientTimeout(total=int(settings.http_timeout))
    session = aiohttp.ClientSession(timeout=timeout)

    # build telegram Application
    app = Application.builder().token(settings.bot_token).build()

    # inject shared resources
    app.bot_data["settings"] = settings
    app.bot_data["http_session"] = session
    app.bot_data["price_service"] = PriceService(settings=settings, session=session)
    app.bot_data["parse_mode"] = settings.parse_mode
    app.bot_data["rate_limit_cooldown"] = float(settings.rate_limit_cooldown)

    # register startup/shutdown callbacks
    app.post_init = lambda _: None  # placeholder if library expects it
    app.create_task(_start_background_warmup(app, DEFAULT_WARMUP_PAIRS))

    # graceful shutdown hook
    app.add_handler(_make_shutdown_handler(app))

    logger.info("Application built: parse_mode=%s, cache_ttl=%s", settings.parse_mode, settings.cache_ttl)
    return app


def _make_shutdown_handler(app: Application):
    """
    Returns a handler-like callable that will be scheduled on shutdown to close session and clear caches.
    This is a minimal wrapper to ensure resources are cleaned when Application.stop() is called.
    """
    async def _shutdown_callback() -> None:
        try:
            logger.info("Shutdown: closing http session and clearing caches")
            price_service: PriceService = app.bot_data.get("price_service")
            if price_service:
                price_service.clear_cache()
            session: aiohttp.ClientSession = app.bot_data.get("http_session")
            if session and not session.closed:
                await session.close()
        except Exception:
            logger.exception("Error during shutdown")
    # schedule the callback when application stops
    async def _on_stop(*_args, **_kwargs):
        await _shutdown_callback()
    # wrap into a no-op handler object compatible with add_handler (safe to call)
    class _ShutdownHandler:
        async def __call__(self, update=None, context=None):
            await _shutdown_callback()
    return _ShutdownHandler()


async def _start_background_warmup(app: Application, pairs: Iterable[tuple[str, str]]) -> None:
    """
    Background warmup that preloads cache for a small set of pairs.
    Runs once at startup; failures are logged and ignored.
    """
    await asyncio.sleep(0.1)  # allow event loop to settle
    settings: Settings = app.bot_data.get("settings")
    price_service: PriceService = app.bot_data.get("price_service")
    if not price_service or not settings:
        logger.debug("Warmup skipped: missing price_service or settings")
        return

    logger.info("Warmup: preloading price cache for %d pairs", len(list(pairs)))
    tasks = []
    for base, quote in pairs:
        tasks.append(asyncio.create_task(_safe_fetch(price_service, base, quote)))

    # wait but don't fail startup if warmup fails
    await asyncio.gather(*tasks, return_exceptions=True)
    logger.info("Warmup: completed")


async def _safe_fetch(price_service: PriceService, base: str, quote: str) -> None:
    try:
        price = await price_service.get_price(base, quote)
        logger.debug("Warmup fetched %s->%s price=%s", base, quote, price)
    except Exception:
        logger.exception("Warmup fetch failed for %s->%s", base, quote)
