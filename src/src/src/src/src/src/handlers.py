# src/handlers.py
"""
Telegram handlers
- Async, type-hinted handlers compatible with python-telegram-bot v20+
- Centralized parse_mode from app.bot_data
- Allowed-chats check via settings.is_chat_allowed
- Lightweight in-memory per-user rate-limit (cooldown seconds) with ability to upgrade to Redis
- Uses PriceService from app.bot_data
- All user-facing text obtained via localization.get_messages(lang)
- Errors are converted to user-friendly replies and logged
"""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Dict, Optional, Tuple

from telegram import InlineQueryResultArticle, InputTextMessageContent, Update
from telegram.ext import (
    ContextTypes,
    CommandHandler,
    MessageHandler,
    InlineQueryHandler,
    filters,
)

from .config import Settings
from .prices import PriceService
from .localization import get_messages
from .utils import parse_amount_and_pair, format_price

logger = logging.getLogger(__name__)

# simple in-memory rate limiter: user_id -> last_ts
_RATE_LIMIT_STATE: Dict[int, float] = {}
# simple per-chat cooldown map: chat_id -> last_ts (optional)
_CHAT_RATE_LIMIT_STATE: Dict[int, float] = {}


def _is_allowed_chat(app_bot_data: Dict[str, Any], chat_id: int) -> bool:
    settings: Settings = app_bot_data.get("settings")
    if not settings:
        return True
    try:
        return settings.is_chat_allowed(chat_id)
    except Exception:
        logger.exception("Error checking allowed_chats")
        return False


def _get_parse_mode(app_bot_data: Dict[str, Any]) -> Optional[str]:
    return app_bot_data.get("parse_mode")


def _get_rate_limit_cooldown(app_bot_data: Dict[str, Any]) -> float:
    try:
        return float(app_bot_data.get("rate_limit_cooldown", 0.7))
    except Exception:
        return 0.7


def _is_rate_limited(user_id: int, app_bot_data: Dict[str, Any]) -> bool:
    cooldown = _get_rate_limit_cooldown(app_bot_data)
    now = time.time()
    last = _RATE_LIMIT_STATE.get(user_id, 0.0)
    if now - last < cooldown:
        return True
    _RATE_LIMIT_STATE[user_id] = now
    return False


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Simple /start handler"""
    if update.effective_chat is None:
        return
    app_data = context.application.bot_data
    if not _is_allowed_chat(app_data, update.effective_chat.id):
        msgs = get_messages(_lang_from_update(update))
        await update.effective_message.reply_text(msgs.NOT_ALLOWED, parse_mode=_get_parse_mode(app_data))
        return

    msgs = get_messages(_lang_from_update(update))
    await update.effective_message.reply_text(msgs.START, parse_mode=_get_parse_mode(app_data))


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat is None:
        return
    app_data = context.application.bot_data
    msgs = get_messages(_lang_from_update(update))
    await update.effective_message.reply_text(msgs.HELP, parse_mode=_get_parse_mode(app_data))


async def convert_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Main text handler: parse user text, fetch price, reply formatted result.
    Rate-limited and respects allowed_chats.
    """
    if update.effective_message is None or update.effective_chat is None:
        return

    app_data = context.application.bot_data
    chat_id = update.effective_chat.id
    user = update.effective_user
    user_id = user.id if user else 0

    if not _is_allowed_chat(app_data, chat_id):
        msgs = get_messages(_lang_from_update(update))
        await update.effective_message.reply_text(msgs.NOT_ALLOWED, parse_mode=_get_parse_mode(app_data))
        return

    if _is_rate_limited(user_id, app_data):
        msgs = get_messages(_lang_from_update(update))
        await update.effective_message.reply_text(msgs.RATE_LIMITED, parse_mode=_get_parse_mode(app_data))
        return

    text = update.effective_message.text or ""
    msgs = get_messages(_lang_from_update(update))

    try:
        amount, base_sym, quote_sym = parse_amount_and_pair(text)
    except ValueError as e:
        logger.debug("Parse error for text=%r: %s", text, e)
        await update.effective_message.reply_text(msgs.INVALID_QUERY, parse_mode=_get_parse_mode(app_data))
        return
    except Exception:
        logger.exception("Unexpected parse error")
        await update.effective_message.reply_text(msgs.ERROR, parse_mode=_get_parse_mode(app_data))
        return

    price_service: PriceService = app_data.get("price_service")
    if not price_service:
        logger.error("PriceService missing in app.bot_data")
        await update.effective_message.reply_text(msgs.ERROR, parse_mode=_get_parse_mode(app_data))
        return

    try:
        price = await price_service.get_price(base_sym, quote_sym)
    except Exception:
        logger.exception("Price fetch error for %s->%s", base_sym, quote_sym)
        await update.effective_message.reply_text(msgs.ERROR, parse_mode=_get_parse_mode(app_data))
        return

    if price is None:
        await update.effective_message.reply_text(msgs.NOT_FOUND.format(base=base_sym, quote=quote_sym), parse_mode=_get_parse_mode(app_data))
        return

    try:
        text_out = format_price(amount, price, base_sym, quote_sym)
    except Exception:
        logger.exception("Formatting error for amount=%s price=%s", amount, price)
        await update.effective_message.reply_text(msgs.ERROR, parse_mode=_get_parse_mode(app_data))
        return

    await update.effective_message.reply_text(text_out, parse_mode=_get_parse_mode(app_data))


async def inline_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle inline queries. Return a short list (max 5) of results.
    Lightweight rate-limit and allowed_chats via user chat not available in inline context.
    """
    if update.inline_query is None:
        return
    query = update.inline_query.query or ""
    app_data = context.application.bot_data

    # basic inline rate-limit by user
    user = update.inline_query.from_user
    user_id = user.id if user else 0
    if _is_rate_limited(user_id, app_data):
        # return empty results quickly
        await update.inline_query.answer([], cache_time=1)
        return

    msgs = get_messages(_lang_from_update(update))

    try:
        amount, base_sym, quote_sym = parse_amount_and_pair(query)
    except ValueError:
        # silently ignore parse errors in inline mode
        await update.inline_query.answer([], cache_time=1)
        return
    except Exception:
        logger.exception("Unexpected inline parse error")
        await update.inline_query.answer([], cache_time=1)
        return

    price_service: PriceService = app_data.get("price_service")
    if not price_service:
        await update.inline_query.answer([], cache_time=1)
        return

    price = await price_service.get_price(base_sym, quote_sym)
    if price is None:
        await update.inline_query.answer([], cache_time=1)
        return

    try:
        formatted = format_price(amount, price, base_sym, quote_sym)
    except Exception:
        logger.exception("Formatting in inline")
        await update.inline_query.answer([], cache_time=1)
        return

    result = InlineQueryResultArticle(
        id=f"{base_sym}-{quote_sym}-{int(time.time())}",
        title=f"{amount} {base_sym} → {quote_sym}",
        input_message_content=InputTextMessageContent(formatted, parse_mode=_get_parse_mode(app_data)),
        description=formatted,
    )

    await update.inline_query.answer([result], cache_time=5, is_personal=True)


def _lang_from_update(update: Update) -> Optional[str]:
    """
    Determine language for localization.
    Priority: user.lang_code -> chat locale -> default None (fallback to en)
    """
    if update.effective_user and getattr(update.effective_user, "language_code", None):
        return update.effective_user.language_code
    if update.effective_chat and getattr(update.effective_chat, "locale", None):
        return update.effective_chat.locale
    return None


def register_handlers(application) -> None:
    """
    Register core handlers onto the provided Application instance.
    Call after build_app and before run_polling.
    """
    # commands
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))

    # inline queries
    application.add_handler(InlineQueryHandler(inline_query_handler))

    # main message handler: basic texts (ignore commands which are handled above)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, convert_message))

    logger.info("Handlers registered")
