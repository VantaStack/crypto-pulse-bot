const TelegramBot = require('node-telegram-bot-api');
const { handlePriceCommand } = require('./commands/price');
const { handleConvertCommand } = require('./commands/convert');
const { TELEGRAM_TOKEN } = require('../config/config');
const logger = require('../config/logger'); // پیشنهاد: به جای console

let botInstance = null;

async function startBot() {
  if (!TELEGRAM_TOKEN) throw new Error('❌ TELEGRAM_TOKEN is missing in .env');

  const bot = new TelegramBot(TELEGRAM_TOKEN, { polling: true });
  botInstance = bot;

  // error handling
  bot.on('polling_error', (err) => {
    logger.error({ msg: 'Polling error', err: err.message || err });
  });

  // commands
  bot.onText(/\/price\s+(.+)/i, async (msg, match) => {
    try {
      await handlePriceCommand(bot, msg, match);
    } catch (err) {
      logger.error({ msg: 'Error in /price command', err: err.message || err });
      bot.sendMessage(msg.chat.id, '⚠️ مشکلی در گرفتن قیمت پیش اومد.');
    }
  });

  bot.onText(/\/convert\s+(.+)/i, async (msg, match) => {
    try {
      await handleConvertCommand(bot, msg, match);
    } catch (err) {
      logger.error({ msg: 'Error in /convert command', err: err.message || err });
      bot.sendMessage(msg.chat.id, '⚠️ مشکلی در تبدیل پیش اومد.');
    }
  });

  bot.onText(/\/start/, (msg) => {
    bot.sendMessage(
      msg.chat.id,
      '👋 سلام! من ربات Crypto Pulse هستم.\n' +
      'دستورات:\n' +
      '• /price SYMBOL [vs]\n' +
      '• /convert AMOUNT FROM to TO'
    );
  });

  // graceful shutdown
  process.once('SIGINT', shutdown);
  process.once('SIGTERM', shutdown);

  logger.info('✅ Crypto Pulse Bot started.');
  return bot;
}

function shutdown() {
  if (botInstance) {
    botInstance.stopPolling();
    logger.info('Bot polling stopped.');
  }
}

module.exports = { startBot, shutdown };
