const axios = require('axios');

// مپینگ سمبل → آی‌دی کوین‌گکو
const COIN_MAP = {
  btc: 'bitcoin',
  eth: 'ethereum',
  usdt: 'tether',
  bnb: 'binancecoin',
  xrp: 'ripple',
  ada: 'cardano',
  doge: 'dogecoin',
  sol: 'solana',
  matic: 'polygon',
  // ... می‌تونی کامل‌ترش کنی یا داینامیک از API بگیری
};

async function fetchCoinPrice(symbol, vsCurrency) {
  try {
    const id = COIN_MAP[symbol.toLowerCase()] || symbol.toLowerCase();

    const { data } = await axios.get(
      'https://api.coingecko.com/api/v3/simple/price',
      {
        params: {
          ids: id,
          vs_currencies: vsCurrency.toLowerCase()
        },
        timeout: 5000,
      }
    );

    if (!data[id] || !data[id][vsCurrency.toLowerCase()]) {
      return null;
    }

    return data[id][vsCurrency.toLowerCase()];
  } catch (err) {
    console.error('fetchCoinPrice error:', err.message);
    return null;
  }
}

async function convertCrypto(input) {
  const parts = input.match(/^([0-9]+(?:\.[0-9]+)?)\s*(\w+)\s*(?:to|->)\s*(\w+)$/i);

  if (!parts) {
    throw new Error('⚠️ فرمت درست: /convert AMOUNT FROM to TO\nمثال: /convert 2 btc to usd');
  }

  const amount = parseFloat(parts[1]);
  const from = parts[2];
  const to = parts[3];

  const fromPrice = await fetchCoinPrice(from, 'usd');
  const toPrice = await fetchCoinPrice(to, 'usd');

  if (!fromPrice || !toPrice) {
    throw new Error('⚠️ قیمت پیدا نشد، لطفاً نمادها را بررسی کنید.');
  }

  const result = amount * (fromPrice / toPrice);
  return `${amount} ${from.toUpperCase()} ≈ ${result.toFixed(6)} ${to.toUpperCase()}`;
}

module.exports = { fetchCoinPrice, convertCrypto };
