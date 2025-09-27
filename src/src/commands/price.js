const { fetchCoinPrice } = require('../services/coingecko');

async function handlePriceCommand(bot, msg, match) {
  const chatId = msg.chat.id;

  // ورودی اولیه
  if (!match || !match[1]) {
    return bot.sendMessage(chatId, '⚠️ فرمت درست: /price SYMBOL [vs]\nمثال: /price btc usd');
  }

  const input = match[1].trim();
  const [symbol, vs] = input.split(/\s+/);

  if (!symbol) {
    return bot.sendMessage(chatId, '⚠️ لطفاً نماد ارز رو وارد کن. مثال: /price btc');
  }

  try {
    const vsCurrency = vs || 'usd';
    const price = await fetchCoinPrice(symbol.toLowerCase(), vsCurrency.toLowerCase());

    if (!price) {
      return bot.sendMessage(chatId, `⚠️ قیمت برای ${symbol.toUpperCase()} یافت نشد.`);
    }

    bot.sendMessage(
      chatId,
      `💰 ${symbol.toUpperCase()} → ${vsCurrency.toUpperCase()}: ${price}`
    );
  } catch (error) {
    console.error('Error in handlePriceCommand:', error.message);
    bot.sendMessage(chatId, '⚠️ خطا در دریافت قیمت، لطفاً دوباره امتحان کن.');
  }
}

module.exports = { handlePriceCommand };
