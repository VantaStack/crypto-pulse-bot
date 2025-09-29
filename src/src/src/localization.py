"""
localization.py
---------------
English/Persian messages and helpers.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Messages:
    START: str
    HELP: str
    LANG_SET_EN: str
    LANG_SET_FA: str
    PROMPT: str
    ERROR: str
    INLINE_HINT: str
    RATE_LIMIT: str
    NOT_ALLOWED: str


EN = Messages(
    START=(
        "Welcome to Crypto Pulse Bot! 👋\n"
        "Send queries like: `2 BTC to USD` or `eth to cad`.\n"
        "Use /help for details."
    ),
    HELP=(
        "How to use:\n"
        "- Format: `<amount> <symbol> to <fiat|crypto>` (amount optional)\n"
        "- Examples:\n"
        "  • `btc usd`\n"
        "  • `2.5 eth to eur`\n"
        "  • `(1.2 eth + 0.3 eth) to usd`\n"
        "- Inline: type `@BotName btc usd` in any chat\n"
        "- /setlang en|fa to change language"
    ),
    LANG_SET_EN="Language set to English ✅",
    LANG_SET_FA="Language set to Persian ✅",
    PROMPT="Type a query, e.g., `0.1 BTC to USD`",
    ERROR="Sorry, I couldn't parse that. Try `2 BTC to USD`.",
    INLINE_HINT="Enter e.g. `btc usd` or `2 eth to cad`",
    RATE_LIMIT="Too many requests. Please wait a moment ⏳",
    NOT_ALLOWED="This chat is not allowed to use the bot 🚫",
)

FA = Messages(
    START=(
        "به کریپتو پالس بات خوش آمدی! 👋\n"
        "مثل این بفرست: `2 BTC به USD` یا `eth به cad`.\n"
        "برای جزئیات /help رو بزن."
    ),
    HELP=(
        "نحوه استفاده:\n"
        "- قالب: `<مقدار> <نماد> به <فیات|کریپتو>` (مقدار اختیاری)\n"
        "- مثال‌ها:\n"
        "  • `btc usd`\n"
        "  • `2.5 eth به eur`\n"
        "  • `(1.2 eth + 0.3 eth) به usd`\n"
        "- اینلاین: در هر چت `@BotName btc usd` تایپ کن\n"
        "- تغییر زبان: /setlang en|fa"
    ),
    LANG_SET_EN="زبان روی انگلیسی تنظیم شد ✅",
    LANG_SET_FA="زبان روی فارسی تنظیم شد ✅",
    PROMPT="یک پرسش بفرست، مثل `0.1 BTC به USD`",
    ERROR="متاسفم، نفهمیدم. امتحان کن: `2 BTC به USD`.",
    INLINE_HINT="مثلاً `btc usd` یا `2 eth به cad` وارد کن",
    RATE_LIMIT="درخواست‌های زیاد. چند لحظه صبر کن ⏳",
    NOT_ALLOWED="این چت مجاز به استفاده از ربات نیست 🚫",
)


def get_messages(lang: str) -> Messages:
    return EN if lang.lower() != "fa" else FA
