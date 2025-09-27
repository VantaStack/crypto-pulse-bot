const TelegramBot = require('node-telegram-bot-api');
const { handlePriceCommand } = require('./commands/price');
const { handleConvertCommand } = require('./commands/convert');
const { TELEGRAM_TOKEN } = require('../config/config');

async function startBot() {
  if (!TELEGRAM_TOKEN) throw new Error('❌ TELEGRAM_TOKEN is missing in .env');

  const bot = new TelegramBot(TELEGRAM_TOKEN, { polling: true });

  // error handling
  bot.on('polling_error', (err) => {
    console.error('Polling error:', err.message);
  });

  // commands
  bot.onText(/\/price\s+(.+)/i, async (msg, match) => {
    try {
      await handlePriceCommand(bot, msg, match);
    } catch (err) {
      console.error('Error in /price command:', err);
      bot.sendMessage(msg.chat.id, '⚠️ مشکلی پیش اومد، دوباره امتحان کن.');
    }
  });

  bot.onText(/\/convert\s+(.+)/i, async (msg, match) => {
    try {
      await handleConvertCommand(bot, msg, match);
    } catch (err) {
      console.error('Error in /convert command:', err);
      bot.sendMessage(msg.chat.id, '⚠️ مشکلی در تبدیل پیش اومد.');
    }
  });

  // start
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
  process.once('SIGINT', () => bot.stopPolling());
  process.once('SIGTERM', () => bot.stopPolling());

  console.log('✅ Crypto Pulse Bot started.');
  return bot;
}

module.exports = { startBot };
