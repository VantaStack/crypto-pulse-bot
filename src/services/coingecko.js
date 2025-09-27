const axios = require('axios');
const logger = require('../../config/logger');

const COIN_MAP = {
  btc: 'bitcoin',
  eth: 'ethereum',
  usdt: 'tether',
  bnb: 'binancecoin',
  xrp: 'ripple',
  ada: 'cardano',
  doge: 'dogecoin',
  sol: 'solana',
  matic: 'polygon'
};

async function fetchFromCoinGecko(symbol, vsCurrency) {
  try {
    const id = (COIN_MAP[symbol.toLowerCase()] || symbol.toLowerCase());
    const res = await axios.get('https://api.coingecko.com/api/v3/simple/price', {
      params: { ids: id, vs_currencies: vsCurrency.toLowerCase() },
      timeout: 5000
    });
    const data = res.data;
    if (!data || !data[id] || data[id][vsCurrency.toLowerCase()] === undefined) return null;
    return Number(data[id][vsCurrency.toLowerCase()]);
  } catch (err) {
    logger.warn({msg:'CoinGecko fetch failed', err: err.message || err});
    return null;
  }
}

module.exports = { fetchFromCoinGecko };
