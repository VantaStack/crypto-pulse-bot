require('dotenv').config();
const { TELEGRAM_TOKEN, PREFERRED_PROVIDERS, NODE_ENV } = process.env;

module.exports = {
  TELEGRAM_TOKEN,
  PREFERRED_PROVIDERS: PREFERRED_PROVIDERS ? PREFERRED_PROVIDERS.split(',').map(s => s.trim()) : ['coingecko','binance'],
  NODE_ENV: NODE_ENV || 'development',
};
