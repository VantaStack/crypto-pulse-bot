const { fetchFromCoinGecko } = require('./coingecko');
const { fetchFromBinance } = require('./binance');
const logger = require('../../config/logger');
const { PREFERRED_PROVIDERS } = require('../../config/config');

const cache = new Map();
const TTL = 10 * 1000; // 10 seconds

function getCacheKey(symbol, vs) {
  return `${symbol.toLowerCase()}_${vs.toLowerCase()}`;
}

async function getAggregatedPrice(symbol, vs = 'usd') {
  const key = getCacheKey(symbol, vs);
  const now = Date.now();
  const cached = cache.get(key);
  if (cached && (now - cached.ts) < TTL) return cached.value;

  const preferred = PREFERRED_PROVIDERS || ['coingecko','binance'];
  const results = [];

  for (const p of preferred) {
    if (p === 'coingecko') {
      const v = await fetchFromCoinGecko(symbol, vs);
      if (v !== null) results.push({provider:'coingecko', price: v});
    } else if (p === 'binance') {
      const v = await fetchFromBinance(symbol, vs);
      if (v !== null) results.push({provider:'binance', price: v});
    }
  }

  if (results.length === 0) {
    cache.set(key, { ts: now, value: null });
    return null;
  }

  const prices = results.map(r => r.price).sort((a,b)=>a-b);
  const median = prices[Math.floor(prices.length/2)];
  cache.set(key, { ts: now, value: median });
  return median;
}

module.exports = { getAggregatedPrice };
