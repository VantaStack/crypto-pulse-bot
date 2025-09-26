const TelegramBot = require('node-telegram-bot-api');
const { handlePriceCommand } = require('./commands/price');
const { handleConvertCommand } = require('./commands/convert');
const { TELEGRAM_TOKEN } = require('../config/config');

let bot;

async function startBot() {
  if (!TELEGRAM_TOKEN) throw new Error('TELEGRAM_TOKEN is missing in .env');

  bot = new TelegramBot(TELEGRAM_TOKEN, { polling: true });

  bot.onText(/\/price\s+(.+)/i, handlePriceCommand.bind(null, bot));
  bot.onText(/\/convert\s+(.+)/i, handleConvertCommand.bind(null, bot));

  bot.onText(/\/start/, (msg) => {
    bot.sendMessage(msg.chat.id, 'سلام! من ربات Crypto Pulse هستم.\nاستفاده: /price SYMBOL [vs] یا /convert AMOUNT FROM to TO');
  });
}

module.exports = { startBot };
