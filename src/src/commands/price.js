const { fetchCoinPrice } = require('../services/coingecko');

async function handlePriceCommand(bot, msg, match) {
  const chatId = msg.chat.id;
  const input = match[1].trim();
  const [symbol, vs] = input.split(/\s+/);

  try {
    const vsCurrency = vs || 'usd';
    const price = await fetchCoinPrice(symbol, vsCurrency);
    bot.sendMessage(chatId, `${symbol.toUpperCase()} → ${vsCurrency.toUpperCase()}: ${price}`);
  } catch (error) {
    bot.sendMessage(chatId, `خطا در گرفتن قیمت: ${error.message}`);
  }
}

module.exports = { handlePriceCommand };
