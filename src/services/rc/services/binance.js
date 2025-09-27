const axios = require('axios');
const logger = require('../../config/logger');

async function fetchFromBinance(symbol, vsCurrency) {
  try {
    const s = symbol.toUpperCase();
    const v = vsCurrency.toUpperCase();
    const pairsToTry = [`${s}${v}`, `${s}USDT`, `${s}USD`];
    for (const pair of pairsToTry) {
      try {
        const res = await axios.get(`https://api.binance.com/api/v3/ticker/price`, {
          params: { symbol: pair },
          timeout: 4000
        });
        if (res && res.data && res.data.price) {
          return Number(res.data.price);
        }
      } catch (innerErr) {
        // ignore and try next pair
      }
    }
    return null;
  } catch (err) {
    logger.warn({msg:'Binance fetch failed', err: err.message || err});
    return null;
  }
}

module.exports = { fetchFromBinance };
