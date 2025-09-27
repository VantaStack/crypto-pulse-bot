const logger = require('../../config/logger');
const { formatPrice } = require('../../config/formatter');
const { getAggregatedPrice } = require('../services/aggregator');

async function handleConvertCommand(bot, msg, match) {
  const chatId = msg.chat.id;

  if (!match || !match[1]) {
    return bot.sendMessage(chatId, '⚠️ فرمت درست: /convert AMOUNT FROM to TO\nمثال: /convert 2 btc to usd');
  }

  const input = match[1].trim();
  // accept: 2 btc to usd  OR  2 btc usd
  const parts = input.match(/^([0-9]+(?:\.[0-9]+)?)\s+(\w+)\s+(?:to\s+)?(\w+)$/i);
  if (!parts) {
    return bot.sendMessage(chatId, '⚠️ فرمت درست: /convert AMOUNT FROM to TO\nمثال: /convert 2 btc to usd');
  }

  const amount = parseFloat(parts[1]);
  const from = parts[2];
  const to = parts[3];

  if (Number.isNaN(amount) || amount <= 0) {
    return bot.sendMessage(chatId, '⚠️ مقدار نامعتبر است. لطفاً عدد مثبت وارد کنید.');
  }

  try {
    const fromPrice = await getAggregatedPrice(from, 'usd');
    const toPrice = await getAggregatedPrice(to, 'usd');

    if (!fromPrice || !toPrice) {
      return bot.sendMessage(chatId, '⚠️ قیمت نمادها پیدا نشد، لطفاً نمادها را بررسی کنید.');
    }

    const result = amount * (fromPrice / toPrice);
    bot.sendMessage(chatId, `🔄 ${amount} ${from.toUpperCase()} ≈ ${formatPrice(result)} ${to.toUpperCase()}`);
  } catch (err) {
    logger.error({msg:'handleConvertCommand error', err: err.message || err});
    bot.sendMessage(chatId, '⚠️ خطا در انجام تبدیل، لطفاً بعداً تلاش کنید.');
  }
}

module.exports = { handleConvertCommand };
