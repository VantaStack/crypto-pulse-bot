const { convertCrypto } = require('../services/coingecko');

async function handleConvertCommand(bot, msg, match) {
  const chatId = msg.chat.id;

  // بررسی ورودی اولیه
  if (!match || !match[1]) {
    return bot.sendMessage(
      chatId,
      '⚠️ فرمت درست: /convert AMOUNT SYMBOL to SYMBOL\nمثال: /convert 2 btc to usd'
    );
  }

  const input = match[1].trim();
  const parts = input.split(/\s+/);

  // انتظار: عدد + symbol + 'to' + symbol
  if (parts.length < 3) {
    return bot.sendMessage(
      chatId,
      '⚠️ لطفاً ورودی رو درست بده.\nمثال: /convert 2 btc to usd'
    );
  }

  try {
    const result = await convertCrypto(input);

    if (!result) {
      return bot.sendMessage(chatId, '⚠️ تبدیل انجام نشد. لطفاً ورودی رو بررسی کن.');
    }

    bot.sendMessage(chatId, `🔄 نتیجه تبدیل:\n${result}`);
  } catch (error) {
    console.error('Error in handleConvertCommand:', error.message);
    bot.sendMessage(chatId, '⚠️ خطا در انجام تبدیل، لطفاً دوباره تلاش کن.');
  }
}

module.exports = { handleConvertCommand };
