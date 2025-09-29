"""
app.py
------
Application bootstrap: wiring handlers and shared services.
"""

import asyncio
import logging

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    InlineQueryHandler,
)

from .config import SETTINGS
from .prices import PriceService
from .handlers import start, help_cmd, setlang, text_query, inline_query

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("crypto-pulse-bot")


async def main() -> None:
    if not SETTINGS.bot_token:
        raise RuntimeError("BOT_TOKEN is missing")

    app = Application.builder().token(SETTINGS.bot_token).build()

    # shared services
    app.bot_data["prices"] = PriceService(ttl=SETTINGS.cache_ttl)

    # handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("setlang", setlang))
    app.add_handler(InlineQueryHandler(inline_query))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_query))

    logger.info("Bot started")
    try:
        await app.run_polling()
    finally:
        ps: PriceService = app.bot_data["prices"]
        await ps.close()
        logger.info("Bot stopped")


if __name__ == "__main__":
    asyncio.run(main())
