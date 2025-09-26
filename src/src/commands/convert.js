const { convertCrypto } = require('../services/coingecko');

async function handleConvertCommand(bot, msg, match) {
  const chatId = msg.chat.id;
  const input = match[1].trim();

  try {
    const result = await convertCrypto(input);
    bot.sendMessage(chatId, result);
  } catch (error) {
    bot.sendMessage(chatId, `خطا در تبدیل: ${error.message}`);
  }
}

module.exports = { handleConvertCommand };
