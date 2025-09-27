const logger = require('../../config/logger');
const { formatPrice } = require('../../config/formatter');
const { getAggregatedPrice } = require('../services/aggregator');

async function handlePriceCommand(bot, msg, match) {
  const chatId = msg.chat.id;

  if (!match || !match[1]) {
    return bot.sendMessage(chatId, '⚠️ فرمت درست: /price SYMBOL [vs]\nمثال: /price btc usd');
  }

  const input = match[1].trim();
  const parts = input.split(/\s+/);
  const symbol = parts[0];
  const vs = parts[1] || 'usd';

  if (!symbol) {
    return bot.sendMessage(chatId, '⚠️ لطفا نماد ارز را وارد کنید. مثال: /price btc');
  }

  try {
    const price = await getAggregatedPrice(symbol, vs);
    if (price === null) {
      return bot.sendMessage(chatId, `⚠️ قیمت برای ${symbol.toUpperCase()} یافت نشد.`);
    }
    bot.sendMessage(chatId, `💰 ${symbol.toUpperCase()} → ${vs.toUpperCase()}: ${formatPrice(price)}`);
  } catch (err) {
    logger.error({msg:'handlePriceCommand error', err: err.message || err});
    bot.sendMessage(chatId, '⚠️ خطا در دریافت قیمت، لطفاً بعداً تلاش کنید.');
  }
}

module.exports = { handlePriceCommand };
