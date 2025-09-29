"""
handlers.py
-----------
Telegram command, text, and inline handlers with rate limiting and access control.
"""

import time
import uuid
from decimal import Decimal

from telegram import Update, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import ContextTypes

from .config import SETTINGS
from .localization import get_messages
from .utils import (
    parse_query,
    eval_amount,
    normalize_symbol,
    is_fiat,
    format_price,
)
from .prices import PriceService

RATE_LIMIT_SECONDS = 0.5


def _lang(context: ContextTypes.DEFAULT_TYPE) -> str:
    return context.chat_data.get("lang", SETTINGS.default_lang)


def _allowed(update: Update) -> bool:
    chat_id = update.effective_chat.id if update.effective_chat else 0
    return SETTINGS.is_chat_allowed(chat_id)


def _rate_limited(context: ContextTypes.DEFAULT_TYPE) -> bool:
    now = time.time()
    last = context.chat_data.get("last_ts", 0.0)
    if now - last < RATE_LIMIT_SECONDS:
        return True
    context.chat_data["last_ts"] = now
    return False


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msgs = get_messages(_lang(context))
    if not _allowed(update):
        await update.message.reply_text(msgs.NOT_ALLOWED)
        return
    await update.message.reply_text(msgs.START)


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msgs = get_messages(_lang(context))
    if not _allowed(update):
        await update.message.reply_text(msgs.NOT_ALLOWED)
        return
    await update.message.reply_text(msgs.HELP)


async def setlang(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msgs = get_messages(_lang(context))
    if not _allowed(update):
        await update.message.reply_text(msgs.NOT_ALLOWED)
        return
    if not context.args:
        await update.message.reply_text("Usage: /setlang en|fa")
        return
    lang = context.args[0].lower()
    if lang not in {"en", "fa"}:
        await update.message.reply_text("Usage: /setlang en|fa")
        return
    context.chat_data["lang"] = lang
    msgs2 = get_messages(lang)
    await update.message.reply_text(
        msgs2.LANG_SET_EN if lang == "en" else msgs2.LANG_SET_FA
    )


async def text_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msgs = get_messages(_lang(context))
    if not _allowed(update):
        await update.message.reply_text(msgs.NOT_ALLOWED)
        return

    if _rate_limited(context):
        await update.message.reply_text(msgs.RATE_LIMIT)
        return

    text = (update.message.text or "").strip()
    q = parse_query(text)
    if not q:
        await update.message.reply_text(msgs.ERROR)
        return

    try:
        amount: Decimal = eval_amount(q["amount_expr"])
    except Exception:
        await update.message.reply_text(msgs.ERROR)
        return

    base_sym = q["base"]
    quote_sym = q["quote"] or ("usd" if not is_fiat(base_sym) else "btc")
    base_id = normalize_symbol(base_sym)
    quote_id = normalize_symbol(quote_sym)

    ps: PriceService = context.bot_data["prices"]
    price = await ps.get_price(base_id, quote_id)
    if price is None:
        await update.message.reply_text(msgs.ERROR)
        return

    await update.message.reply_text(
        format_price(amount, price, base_sym, quote_sym)
    )


async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msgs = get_messages(_lang(context))
    query = (update.inline_query.query or "").strip()

    if not query:
        await update.inline_query.answer(
            [
                InlineQueryResultArticle(
                    id=str(uuid.uuid4()),
                    title="Hint",
                    input_message_content=InputTextMessageContent(msgs.INLINE_HINT),
                )
            ],
            cache_time=1,
        )
        return

    q = parse_query(query)
    if not q:
        await update.inline_query.answer([], cache_time=1)
        return

    try:
        amount: Decimal = eval_amount(q["amount_expr"])
    except Exception:
        await update.inline_query.answer([], cache_time=1)
        return

    base_sym = q["base"]
    quote_sym = q["quote"] or ("usd" if not is_fiat(base_sym) else "btc")
    base_id = normalize_symbol(base_sym)
    quote_id = normalize_symbol(quote_sym)

    ps: PriceService = context.bot_data["prices"]
    price = await ps.get_price(base_id, quote_id)
    if price is None:
        await update.inline_query.answer([], cache_time=1)
        return

    text = format_price(amount, price, base_sym, quote_sym)
    await update.inline_query.answer(
        [
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title=text,
                input_message_content=InputTextMessageContent(text),
            )
        ],
        cache_time=5,
  )
