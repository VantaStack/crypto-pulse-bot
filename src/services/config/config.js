require('dotenv').config();

const TELEGRAM_TOKEN = process.env.TELEGRAM_TOKEN;
const DEFAULT_VS_CURRENCIES = process.env.DEFAULT_VS_CURRENCIES || 'usd,eur';

module.exports = {
  TELEGRAM_TOKEN,
  DEFAULT_VS_CURRENCIES
};
